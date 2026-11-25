"""
Controller de Ingestão Microsoft Forms → AGHUX
==============================================
Responsável por idempotência, normalização das respostas, cruzamento com o
AGHUX, geração de divergências/alertas, cálculo de prioridade e auditoria.
Nenhuma decisão de negócio fica no router.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..helpers.audit_helper import registrar_auditoria
from ..helpers.crypto_helper import decrypt_phi, encrypt_phi, hash_phi, to_dict_seguro
from ..helpers.paciente_helper import paciente_chave as gerar_paciente_chave
from ..helpers.string_helper import extrair_codigo_exame, normalizar_texto, parse_datetime
from ..models.agendamento import PacienteEndereco
from ..models.forms_integration import (
    Alerta,
    Divergencia,
    FormsResponse,
    Solicitacao,
    SolicitacaoItemExame,
    WebhookNonce,
)
from ..providers.interfaces.aghux_provider_interface import AghuxProviderInterface
from ..providers.interfaces.distance_provider_interface import (
    DistanceProviderInterface,
    DistanceResult,
)
from ..providers.interfaces.forms_provider_interface import FormsProviderInterface

logger = logging.getLogger("forms_integration")

STATUS_PENDENTE = "PENDENTE"
STATUS_PROCESSADA = "PROCESSADA"
STATUS_DUPLICADA = "DUPLICADA"
STATUS_ERRO = "ERRO"
PESOS_PADRAO = {"urgenciaClinica": 40, "idade": 25, "tempoEspera": 20, "complexidadeExame": 15}
# Campos que, quando preenchidos, caracterizam endereço informado no formulário.
CAMPOS_ENDERECO = ("cep", "logradouro", "numero", "complemento", "bairro")


def _agora() -> datetime:
    """Retorna datetime UTC atual."""
    return datetime.now(timezone.utc)


def _iso(valor: Optional[datetime]) -> Optional[str]:
    """Serializa datetime para ISO-8601 sem fuso ambíguo."""
    return valor.isoformat() if valor else None


def _json_texto(valor: Any) -> str:
    """Serializa listas/dicionários para a coluna Text."""
    return json.dumps(valor, ensure_ascii=False, default=str)


def _json_objeto(valor: Optional[str], padrao: Any) -> Any:
    """Desserializa uma coluna Text com segurança."""
    if not valor:
        return padrao
    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return padrao


def _complexidade(codigo: str) -> int:
    """Estima a complexidade do exame pela sigla (mesma regra dos mocks)."""
    sigla = (codigo or "").upper()
    if sigla.startswith(("CM", "PET", "RM", "TC", "CT")):
        return 9
    if sigla.startswith(("MBIOP", "CITOP", "ANA", "PAT")):
        return 8
    if sigla.startswith("US"):
        return 6
    if sigla.startswith(("MAMO", "DMO", "DEN")):
        return 5
    if sigla.startswith("RX"):
        return 3
    if sigla.startswith(("LOG", "ATL", "IMT", "PA", "AUDI")):
        return 4
    return 5


def _pontuacao(recebida_em: datetime, codigo_exame: str) -> Tuple[int, str]:
    """Calcula pontuação/prioridade com os pesos vigentes documentados."""
    recebida = recebida_em if recebida_em.tzinfo else recebida_em.replace(tzinfo=timezone.utc)
    horas = max(0.0, (_agora() - recebida).total_seconds() / 3600)
    tempo_espera = min(10, round(horas / 144))
    atributos = {
        "urgenciaClinica": 5,  # neutro até a triagem clínica ser integrada
        "idade": 5,            # neutro até o prontuário eletrônico ser integrado
        "tempoEspera": tempo_espera,
        "complexidadeExame": _complexidade(codigo_exame),
    }
    total = sum(atributos[chave] * peso for chave, peso in PESOS_PADRAO.items())
    pontuacao = min(100, max(0, round(total / 10)))
    prioridade = "ALTA" if pontuacao >= 70 else "MEDIA" if pontuacao >= 40 else "BAIXA"
    return pontuacao, prioridade


async def receber_evento(
    db: AsyncSession,
    *,
    form_id: str,
    response_id: str,
    nonce: str,
    resposta: Optional[Dict[str, Any]],
    submitted_at: Any,
    ip_origem: Optional[str],
) -> Tuple[FormsResponse, bool]:
    """Grava o evento e o nonce. Retorna `(evento, duplicado)`."""
    nonce_existente = await db.scalar(select(WebhookNonce).where(WebhookNonce.nonce == nonce))
    if nonce_existente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nonce do webhook já utilizado.",
        )
    db.add(
        WebhookNonce(
            nonce=nonce,
            criado_em=_agora(),
            expira_em=_agora() + timedelta(seconds=settings.WEBHOOK_MAX_SKEW_SECONDS),
        )
    )

    existente = await db.scalar(
        select(FormsResponse).where(FormsResponse.response_id == response_id)
    )
    if existente:
        await db.commit()
        return existente, True

    payload_cripto = None
    if resposta:
        payload_cripto = encrypt_phi(_json_texto(resposta))
    evento = FormsResponse(
        response_id=response_id,
        form_id=form_id,
        payload_cripto=payload_cripto,
        status=STATUS_PENDENTE,
        tentativas=0,
        recebido_em=parse_datetime(submitted_at, _agora()),
        ip_origem=ip_origem,
    )
    db.add(evento)
    await db.commit()
    await db.refresh(evento)
    return evento, False


def evento_para_dict(evento: FormsResponse, divergencias: int = 0, alertas: int = 0) -> Dict[str, Any]:
    """Converte um evento para o contrato da tela administrativa (sem PHI)."""
    return {
        "responseId": evento.response_id,
        "formId": evento.form_id,
        "status": evento.status,
        "tentativas": evento.tentativas or 0,
        "ultimoErro": evento.ultimo_erro,
        "recebidoEm": _iso(evento.recebido_em),
        "processadoEm": _iso(evento.processado_em),
        "solicitacaoId": evento.solicitacao_id,
        "divergencias": divergencias,
        "alertas": alertas,
    }


async def _contadores(db: AsyncSession, solicitacao_id: Optional[str]) -> Tuple[int, int]:
    """Conta divergências e alertas ativos de uma solicitação."""
    if not solicitacao_id:
        return 0, 0
    divergencias = await db.scalar(
        select(func.count(Divergencia.id)).where(
            Divergencia.solicitacao_id == solicitacao_id,
            Divergencia.deleted_at.is_(None),
        )
    )
    alertas = await db.scalar(
        select(func.count(Alerta.id)).where(
            Alerta.solicitacao_id == solicitacao_id,
            Alerta.deleted_at.is_(None),
        )
    )
    return int(divergencias or 0), int(alertas or 0)


async def listar_eventos(db: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
    """Lista os eventos recentes do webhook para a tela administrativa."""
    eventos = (
        await db.scalars(
            select(FormsResponse)
            .where(FormsResponse.deleted_at.is_(None))
            .order_by(FormsResponse.recebido_em.desc())
            .limit(max(1, min(limit, 200)))
        )
    ).all()
    resultado: List[Dict[str, Any]] = []
    for item in eventos:
        divergencias, alertas = await _contadores(db, item.solicitacao_id)
        resultado.append(evento_para_dict(item, divergencias, alertas))
    return resultado


async def _audit_falha(db: AsyncSession, evento: FormsResponse, erro: str, ip: Optional[str]) -> None:
    """Registra a falha de processamento na trilha de auditoria."""
    try:
        await registrar_auditoria(
            db=db,
            usuario="webhook:microsoft-forms",
            categoria="NEGOCIO_CLINICO",
            acao="FALHA_PROCESSAMENTO_FORMS",
            recurso=f"forms-response:{evento.response_id}",
            dados_anteriores=None,
            dados_novos={"erro": erro[:500]},
            ip_origem=ip,
        )
    except Exception as exc:  # pragma: no cover - auditoria não pode impedir o retry
        logger.error("Falha ao auditar erro do webhook: %s", exc)


async def _atualizar_endereco(
    db: AsyncSession,
    solicitacao: Solicitacao,
    resposta: Dict[str, Any],
    agora: datetime,
    distance_provider: Optional[DistanceProviderInterface],
) -> None:
    """Grava endereço cifrado e distância calculada, sem inventar coordenadas."""
    if distance_provider is None:
        # Import tardio evita ciclo entre dependencies e este controller.
        from ..dependencies import get_distance_provider

        distance_provider = get_distance_provider()

    endereco = await db.scalar(
        select(PacienteEndereco).where(
            PacienteEndereco.paciente_chave == solicitacao.paciente_chave,
            PacienteEndereco.deleted_at.is_(None),
        )
    )
    if not endereco:
        endereco = PacienteEndereco(
            id=str(uuid.uuid4()),
            paciente_chave=solicitacao.paciente_chave,
        )
        db.add(endereco)

    endereco.cep_cripto = encrypt_phi(resposta.get("cep"))
    endereco.logradouro_cripto = encrypt_phi(resposta.get("logradouro"))
    endereco.numero_cripto = encrypt_phi(resposta.get("numero"))
    endereco.complemento_cripto = encrypt_phi(resposta.get("complemento"))
    endereco.bairro_cripto = encrypt_phi(resposta.get("bairro"))
    endereco.cidade = str(resposta.get("cidade") or "")
    endereco.estado = str(resposta.get("estado") or "")
    endereco.deleted_at = None

    try:
        resultado = await distance_provider.calcular(
            {
                "cep": resposta.get("cep"),
                "logradouro": resposta.get("logradouro"),
                "numero": resposta.get("numero"),
                "complemento": resposta.get("complemento"),
                "bairro": resposta.get("bairro"),
                "cidade": resposta.get("cidade"),
                "estado": resposta.get("estado"),
            }
        )
    except Exception as exc:  # falha de rede/provedor nunca interrompe a ingestão
        logger.warning("Distância indisponível: %s", type(exc).__name__)
        resultado = DistanceResult(fonte="INDISPONIVEL")

    fonte = (resultado.fonte or "").upper()
    if fonte not in {"OSM", "MOCK"} or resultado.distancia_km is None:
        endereco.latitude = None
        endereco.longitude = None
        endereco.distancia_km = None
        endereco.distancia_fonte = "INDISPONIVEL"
    else:
        endereco.latitude = resultado.latitude
        endereco.longitude = resultado.longitude
        endereco.distancia_km = float(resultado.distancia_km)
        endereco.distancia_fonte = fonte
    endereco.calculado_em = agora


async def processar_resposta(
    db: AsyncSession,
    response_id: str,
    forms_provider: FormsProviderInterface,
    aghux_provider: AghuxProviderInterface,
    ip_origem: Optional[str] = None,
    distance_provider: Optional[DistanceProviderInterface] = None,
) -> Optional[FormsResponse]:
    """Processa um evento pendente e persiste a solicitação resultante."""
    evento = await db.scalar(
        select(FormsResponse).where(FormsResponse.response_id == response_id)
    )
    if not evento:
        return None

    evento.tentativas = (evento.tentativas or 0) + 1
    try:
        payload = (
            _json_objeto(decrypt_phi(evento.payload_cripto), {})
            if evento.payload_cripto else {}
        )
        resposta = await forms_provider.buscar_resposta(
            evento.form_id, evento.response_id, payload
        )
        registro = await aghux_provider.buscar_por_prontuario(
            str(resposta.get("prontuario") or "")
        )
        if not registro and resposta.get("codigoSolicitacaoAghux"):
            registro = await aghux_provider.buscar_por_codigo_solicitacao(
                str(resposta["codigoSolicitacaoAghux"])
            )

        divergencias: List[Dict[str, str]] = []
        alertas: List[Dict[str, str]] = []

        def comparar(campo: str, valor_form: Any, valor_aghux: Any) -> None:
            if valor_form and valor_aghux and normalizar_texto(str(valor_form)) != normalizar_texto(str(valor_aghux)):
                divergencias.append({
                    "campo": campo,
                    "valor_formulario": str(valor_form),
                    "valor_aghux": str(valor_aghux),
                })

        if registro:
            comparar("Nome completo", resposta.get("nome"), registro.get("nome"))
            comparar("Telefone", resposta.get("telefone"), registro.get("telefone"))
            uf_form = " / ".join(filter(None, [resposta.get("cidade"), resposta.get("estado")]))
            uf_aghux = " / ".join(filter(None, [registro.get("cidade"), registro.get("estado")]))
            comparar("Cidade / UF", uf_form, uf_aghux)
            comparar("Unidade solicitante", resposta.get("unidadeSolicitante"), registro.get("unidadeSolicitante"))
        else:
            alertas.append({
                "campo": "Prontuário",
                "mensagem": "Prontuário do formulário não localizado no AGHUX; conferência manual necessária.",
                "severidade": "ALTA",
            })

        codigo_forms = resposta.get("codigoExame") or extrair_codigo_exame(str(resposta.get("nomeExame") or ""))
        nome_forms = resposta.get("nomeExame") or ""
        if registro and registro.get("itens"):
            itens = [
                {
                    "codigoExame": str(item.get("codigoExame") or ""),
                    "nomeExame": str(item.get("nomeExame") or ""),
                }
                for item in registro["itens"]
            ]
            if nome_forms:
                nomes_aghux = " / ".join(item["nomeExame"] for item in itens)
                comparar("Exame(s)", nome_forms, nomes_aghux)
            elif codigo_forms:
                codigos_aghux = " / ".join(item["codigoExame"] for item in itens)
                comparar("Código do exame", codigo_forms, codigos_aghux)
        elif codigo_forms or nome_forms:
            itens = [{"codigoExame": str(codigo_forms or ""), "nomeExame": str(nome_forms or "")}]
        else:
            itens = []
            alertas.append({
                "campo": "Exame",
                "mensagem": "Nenhum exame foi informado no formulário.",
                "severidade": "ALTA",
            })
        if divergencias:
            alertas.append({
                "campo": "Conferência",
                "mensagem": f"{len(divergencias)} divergência(s) detectada(s) entre formulário e AGHUX.",
                "severidade": "MEDIA",
            })

        recebida_em = parse_datetime(resposta.get("submittedAt"), evento.recebido_em)
        pontuacao, prioridade = _pontuacao(recebida_em, itens[0]["codigoExame"] if itens else "")
        agora = _agora()

        existente = await db.scalar(
            select(Solicitacao).where(
                Solicitacao.forms_response_id == evento.response_id,
                Solicitacao.deleted_at.is_(None),
            )
        )
        antes = _solicitacao_resumo(existente) if existente else None
        if existente:
            solicitacao = existente
            for classe in (SolicitacaoItemExame, Divergencia, Alerta):
                filhos = (
                    await db.scalars(
                        select(classe).where(
                            classe.solicitacao_id == solicitacao.id,
                            classe.deleted_at.is_(None),
                        )
                    )
                ).all()
                for filho in filhos:
                    filho.deleted_at = agora
        else:
            solicitacao = Solicitacao(
                id=str(uuid.uuid4()),
                protocolo=f"FORMS-{evento.response_id}",
                forms_response_id=evento.response_id,
                criado_em=agora,
            )
            db.add(solicitacao)

        solicitacao.codigo_solicitacao_aghux = (
            str(registro.get("codigoSolicitacao") or "")
            if registro else str(resposta.get("codigoSolicitacaoAghux") or "")
        )
        solicitacao.prontuario = str(resposta.get("prontuario") or "")
        solicitacao.paciente_chave = gerar_paciente_chave(
            resposta.get("prontuario"), resposta.get("cpf"), resposta.get("cns")
        )
        solicitacao.paciente_nome = str(resposta.get("nome") or "Paciente não informado")
        solicitacao.telefone = str(resposta.get("telefone") or "")
        solicitacao.cidade = str(resposta.get("cidade") or "")
        solicitacao.estado = str(resposta.get("estado") or "")
        solicitacao.cpf_cripto = encrypt_phi(resposta.get("cpf"))
        solicitacao.cns_cripto = encrypt_phi(resposta.get("cns"))
        solicitacao.cpf_hash = hash_phi(resposta.get("cpf"))
        solicitacao.cns_hash = hash_phi(resposta.get("cns"))
        solicitacao.exame = itens[0]["nomeExame"] if itens else "Exame não informado"
        solicitacao.itens_exame = _json_texto(itens)
        solicitacao.tipo_exame = str((registro or {}).get("tipoExame") or "")
        solicitacao.setor_solicitante = str(
            resposta.get("unidadeSolicitante") or (registro or {}).get("unidadeSolicitante") or ""
        )
        solicitacao.solicitante_codigo = str((registro or {}).get("solicitante", {}).get("codigo") or "")
        solicitacao.solicitante_nome = str((registro or {}).get("solicitante", {}).get("nome") or "")
        solicitacao.status = "RECEBIDA"
        solicitacao.pontuacao = pontuacao
        solicitacao.prioridade = prioridade
        solicitacao.recebida_em = recebida_em
        solicitacao.atualizado_em = agora

        endereco_informado = any(
            str(resposta.get(campo) or "").strip() for campo in CAMPOS_ENDERECO
        )
        if endereco_informado:
            await _atualizar_endereco(
                db, solicitacao, resposta, agora, distance_provider
            )

        for item in itens:
            db.add(
                SolicitacaoItemExame(
                    solicitacao_id=solicitacao.id,
                    codigo_exame=item["codigoExame"],
                    nome_exame=item["nomeExame"],
                )
            )
        for item in divergencias:
            db.add(
                Divergencia(
                    solicitacao_id=solicitacao.id,
                    campo=item["campo"],
                    valor_formulario=item["valor_formulario"],
                    valor_aghux=item["valor_aghux"],
                    criado_em=agora,
                )
            )
        for item in alertas:
            db.add(
                Alerta(
                    solicitacao_id=solicitacao.id,
                    campo=item["campo"],
                    mensagem=item["mensagem"],
                    severidade=item["severidade"],
                    criado_em=agora,
                )
            )

        evento.status = STATUS_PROCESSADA
        evento.processado_em = agora
        evento.ultimo_erro = None
        evento.solicitacao_id = solicitacao.id
        await db.commit()

        await registrar_auditoria(
            db=db,
            usuario="webhook:microsoft-forms",
            categoria="NEGOCIO_CLINICO",
            acao="IMPORTAR_RESPOSTA_FORMS",
            recurso=f"solicitacao:{solicitacao.id}",
            dados_anteriores=antes,
            dados_novos=to_dict_seguro({
                "responseId": evento.response_id,
                "protocolo": solicitacao.protocolo,
                "prontuario": solicitacao.prontuario,
                "codigoAghux": solicitacao.codigo_solicitacao_aghux,
                "pontuacao": pontuacao,
                "prioridade": prioridade,
                "divergencias": len(divergencias),
                "alertas": len(alertas),
                "cpfInformado": bool(resposta.get("cpf")),
                "cnsInformado": bool(resposta.get("cns")),
                "enderecoInformado": endereco_informado,
            }),
            ip_origem=ip_origem or evento.ip_origem,
        )
        return evento
    except Exception as exc:
        await db.rollback()
        logger.exception("Falha ao processar resposta %s", response_id)
        evento = await db.scalar(
            select(FormsResponse).where(FormsResponse.response_id == response_id)
        )
        if evento:
            evento.status = STATUS_ERRO
            evento.ultimo_erro = str(exc)[:1000]
            evento.processado_em = _agora()
            await db.commit()
            await _audit_falha(db, evento, str(exc), ip_origem)
        return evento


def _solicitacao_resumido(solicitacao: Optional[Solicitacao]) -> Optional[Dict[str, Any]]:
    """Resume uma solicitação para o campo `dados_anteriores` da auditoria."""
    if not solicitacao:
        return None
    return to_dict_seguro({
        "protocolo": solicitacao.protocolo,
        "prontuario": solicitacao.prontuario,
        "status": solicitacao.status,
        "pontuacao": solicitacao.pontuacao,
        "prioridade": solicitacao.prioridade,
    })


# Alias mantido para legibilidade no controller.
_solicitacao_resumo = _solicitacao_resumido


async def reprocessar_evento(
    db: AsyncSession,
    response_id: str,
    forms_provider: FormsProviderInterface,
    aghux_provider: AghuxProviderInterface,
    ip_origem: Optional[str] = None,
    distance_provider: Optional[DistanceProviderInterface] = None,
) -> Optional[FormsResponse]:
    """Permite nova tentativa de processamento sem criar outro evento."""
    evento = await db.scalar(
        select(FormsResponse).where(FormsResponse.response_id == response_id)
    )
    if not evento:
        return None
    evento.status = STATUS_PENDENTE
    evento.ultimo_erro = None
    evento.processado_em = None
    await db.commit()
    return await processar_resposta(
        db, response_id, forms_provider, aghux_provider, ip_origem, distance_provider
    )
