"""Regras de negócio já existentes no módulo de Recepção."""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..helpers.audit_helper import registrar_auditoria
from ..providers.interfaces.reception_provider_interface import ReceptionProviderInterface


SETOR_RECEPCAO = "Recepção SAP"
ETAPAS = {
    "RECEPCAO": "Recepção",
    "MACROSCOPIA": "Macroscopia",
    "CONGELACAO": "Congelação",
    "PROCESSAMENTO": "Processamento técnico",
    "IHQ": "Imuno-histoquímica",
    "TRIAGEM_CITO": "Triagem citotécnica",
    "MICROSCOPIA": "Microscopia",
    "APROVACAO": "Aprovação",
    "ARQUIVO": "Arquivo",
    "EXTERNO": "Laboratório externo",
}
TIPOS_NAO_CONFORMIDADE = {
    "SEM_ETIQUETA_AGHU": "Sem etiqueta do AGHU",
    "IDENTIFICACAO_DIVERGENTE": "Identificação divergente",
    "QUANTIDADE_DIVERGENTE": "Quantidade divergente",
    "MATERIAL_INADEQUADO": "Material inadequado/insuficiente",
    "RECIPIENTE_DANIFICADO": "Recipiente danificado/vazamento",
    "FIXACAO_INADEQUADA": "Ausência de fixador/fixação inadequada",
    "REQUISICAO_INCOMPLETA": "Requisição incompleta",
    "OUTRO": "Outro",
}
STATUS_INELEGIVEIS_IHQ = {"DEVOLVIDO", "CANCELADO"}
STATUS_CASO_BLOQUEADOS = {
    "DEVOLVIDO": "Devolvido",
    "CANCELADO": "Cancelado",
    "LAUDO_CONCLUIDO": "Laudo concluído",
    "EM_ARQUIVAMENTO": "Em arquivamento",
    "ARQUIVADO": "Arquivado",
}
ROTULOS_SITUACAO_DEVOLUCAO = {
    "AGUARDANDO_NOVA_AMOSTRA": "Aguardando nova amostra",
    "NOVA_AMOSTRA_RECEBIDA": "Nova amostra recebida",
    "ENCERRADA": "Encerrada",
}


def agora_iso() -> str:
    """Retorna instante UTC em formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def normalizar_codigo(valor: str) -> str:
    """Normaliza código de solicitação ou caso como nos serviços do frontend."""
    return valor.strip().upper()


def normalizar_texto(valor: str) -> str:
    """Normaliza busca textual removendo acentos e ignorando caixa."""
    sem_acentos = unicodedata.normalize("NFD", valor)
    return "".join(char for char in sem_acentos if unicodedata.category(char) != "Mn").upper().strip()


def responsavel_autenticado(usuario: dict[str, Any]) -> dict[str, str]:
    """Deriva o responsável de claims assinadas do token; ignora entrada do cliente."""
    nome = usuario.get("displayName", "")
    if isinstance(nome, list):
        nome = nome[0] if nome else ""
    login = str(usuario.get("username") or usuario.get("sub") or "")
    return {"login": login, "nome": str(nome or login)}


def _exigir_conferencia(conferencia: dict[str, Any]) -> None:
    """Exige todos os quatro itens de conferência já previstos pelo fluxo."""
    campos = ("identificacaoConfere", "materialConfere", "quantidadeConfere", "recipienteAdequado")
    if not all(conferencia.get(campo) is True for campo in campos):
        raise HTTPException(
            status_code=422,
            detail="Marque todos os itens da conferência ou registre uma não conformidade.",
        )


def _exigir_caso_ativo(caso: dict[str, Any], numero: str, operacao: str) -> None:
    """Recusa ações em caso encerrado ou em status somente leitura."""
    status_atual = caso["status"]
    if status_atual in STATUS_CASO_BLOQUEADOS:
        rotulo = STATUS_CASO_BLOQUEADOS[status_atual]
        raise HTTPException(status_code=409, detail=f'O caso {numero} está "{rotulo}" e não aceita {operacao}.')


async def _auditar(
    session: AsyncSession,
    usuario: dict[str, Any],
    request_ip: str | None,
    acao: str,
    recurso: str,
    anterior: Any,
    novo: Any,
) -> None:
    """Registra auditoria na mesma sessão da mutação para manter atomicidade."""
    await registrar_auditoria(
        db=session,
        usuario=responsavel_autenticado(usuario)["login"],
        categoria="NEGOCIO_CLINICO",
        acao=acao,
        recurso=recurso,
        dados_anteriores=anterior,
        dados_novos=novo,
        ip_origem=request_ip,
    )


def _evento_historico(
    responsavel: dict[str, str],
    evento: str,
    titulo: str,
    descricao: str | None = None,
    setor: str = SETOR_RECEPCAO,
    ocorrido_em: str | None = None,
) -> dict[str, Any]:
    """Monta evento no formato HistóricoCaso consumido pelo Vue."""
    return {
        "evento": evento,
        "titulo": titulo,
        "descricao": descricao,
        "setor": setor,
        "usuario": responsavel,
        "ocorridoEm": ocorrido_em or agora_iso(),
    }


class ReceptionController:
    """Orquestra providers e regras existentes sem depender de origem de dados."""

    def __init__(self, provider: ReceptionProviderInterface, session: AsyncSession):
        self.provider = provider
        self.session = session

    async def listar_pendentes(self) -> list[dict[str, Any]]:
        """Lista solicitações pendentes; consulta AGHU mock pode estar indisponível."""
        self._exigir_fonte_disponivel()
        return await self.provider.listar_solicitacoes_pendentes()

    async def contar_pendentes(self) -> int:
        """Conta o estado local pendente sem simular chamada ao AGHU."""
        return await self.provider.contar_solicitacoes_pendentes()

    async def listar_devolucoes(self) -> list[dict[str, Any]]:
        """Lista rejeições e devoluções para identidades com consulta autorizada."""
        return await self.provider.listar_devolucoes()

    async def atualizar_situacao_devolucao(
        self, devolucao_id: int, situacao: str, usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Atualiza situação, histórico e auditoria com autoria da identidade autenticada."""
        alteracao = await self.provider.atualizar_situacao_devolucao(devolucao_id, situacao)
        if alteracao is None:
            raise HTTPException(status_code=404, detail="Devolução não encontrada.")

        anterior = alteracao["anterior"]
        atual = alteracao["atual"]
        if anterior["situacao"] == atual["situacao"]:
            return atual

        responsavel = responsavel_autenticado(usuario)
        if atual.get("casoNumero"):
            await self.provider.adicionar_historico(
                atual["casoNumero"],
                _evento_historico(
                    responsavel,
                    "DEVOLUCAO_ATUALIZADA",
                    "Situação da devolução atualizada",
                    f"{ROTULOS_SITUACAO_DEVOLUCAO[anterior['situacao']]} → "
                    f"{ROTULOS_SITUACAO_DEVOLUCAO[atual['situacao']]}.",
                    ocorrido_em=agora_iso(),
                ),
            )
        await _auditar(
            self.session,
            usuario,
            ip,
            "DEVOLUCAO_SITUACAO_ATUALIZADA",
            f"devolucao:{devolucao_id}",
            {
                "situacao": anterior["situacao"],
                "statusNaoConformidade": alteracao["statusNaoConformidadeAnterior"],
            },
            {
                "situacao": atual["situacao"],
                "statusNaoConformidade": alteracao["statusNaoConformidadeAtual"],
            },
        )
        return atual

    async def ler_solicitacao(self, codigo: str) -> dict[str, Any]:
        """Classifica solicitação como pendente, recebida, devolvida ou inexistente."""
        self._exigir_fonte_disponivel()
        solicitacao = await self.provider.buscar_solicitacao(normalizar_codigo(codigo))
        if solicitacao is None:
            return {"tipo": "NAO_ENCONTRADA"}
        if solicitacao["situacaoRecepcao"] == "RECEBIDA":
            numero = solicitacao.get("casoNumero") or solicitacao.get("ihqCasoNumero") or ""
            return {"tipo": "RECEBIDA", "solicitacao": solicitacao, "casoNumero": numero}
        if solicitacao["situacaoRecepcao"] == "DEVOLVIDA":
            devolucao = next(
                (item for item in await self.provider.listar_devolucoes() if item["id"] == solicitacao.get("devolucaoId")),
                None,
            )
            tipo = devolucao["naoConformidade"]["tipo"] if devolucao else "OUTRO"
            return {
                "tipo": "DEVOLVIDA",
                "solicitacao": solicitacao,
                "devolvidaEm": devolucao["devolvidaEm"] if devolucao else "",
                "tipoNaoConformidade": tipo,
            }
        return {"tipo": "PENDENTE", "solicitacao": solicitacao}

    async def listar_casos(self) -> list[dict[str, Any]]:
        """Retorna casos persistidos para a tela de consulta."""
        return await self.provider.listar_casos()

    async def obter_caso(self, numero: str) -> dict[str, Any] | None:
        """Retorna detalhe do caso ou None para resposta HTTP 404 no router."""
        return await self.provider.buscar_caso(normalizar_codigo(numero))

    async def buscar_casos(self, termo: str, limite: int) -> dict[str, Any]:
        """Busca por número, prontuário ou nome, priorizando número interno exato."""
        alvo = normalizar_texto(termo)
        if not alvo:
            return {"itens": [], "total": 0}
        casos = await self.provider.listar_casos()
        encontrados = [
            caso for caso in casos
            if any(alvo in normalizar_texto(str(campo)) for campo in (
                caso["numeroInterno"], caso["solicitacao"].get("prontuario", ""),
                caso["solicitacao"].get("nomePaciente", ""),
            ))
        ]
        exatos = [caso for caso in encontrados if normalizar_texto(caso["numeroInterno"]) == alvo]
        restantes = [caso for caso in encontrados if normalizar_texto(caso["numeroInterno"]) != alvo]
        ordenados = exatos + sorted(restantes, key=lambda caso: caso["dataEntradaSap"], reverse=True)
        return {
            "total": len(ordenados),
            "itens": [
                {
                    "numeroInterno": caso["numeroInterno"],
                    "tipoExame": caso["tipoExame"],
                    "nomePaciente": caso["solicitacao"]["nomePaciente"],
                    "prontuario": caso["solicitacao"]["prontuario"],
                    "status": caso["status"],
                }
                for caso in ordenados[:limite]
            ],
        }

    async def buscar_elegiveis_ihq(self, termo: str) -> list[dict[str, Any]]:
        """Consulta casos existentes e marca inelegíveis segundo os estados atuais."""
        alvo = termo.strip().upper()
        if len(alvo) < 2:
            return []
        casos = await self.provider.listar_casos()
        encontrados = [
            caso for caso in casos
            if alvo in caso["numeroInterno"].upper()
            or alvo in str(caso["solicitacao"].get("prontuario", "")).upper()
            or alvo in str(caso["solicitacao"].get("nomePaciente", "")).upper()
        ][:8]
        resultado = []
        for caso in encontrados:
            inelegivel = caso["status"] in STATUS_INELEGIVEIS_IHQ
            resultado.append({
                "numeroInterno": caso["numeroInterno"],
                "nomePaciente": caso["solicitacao"]["nomePaciente"],
                "prontuario": caso["solicitacao"]["prontuario"],
                "descricaoMaterial": caso["solicitacao"]["descricaoMaterial"],
                "status": caso["status"],
                "elegivel": not inelegivel,
                "motivoInelegivel": (
                    f'O caso {caso["status"].lower()} não pode receber IHQ.' if inelegivel else None
                ),
            })
        return resultado

    async def confirmar_entrada(
        self, entrada: dict[str, Any], usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Confirma recebimento principal e persiste caso, conferência, materiais e trilha."""
        self._exigir_fonte_disponivel()
        codigo = normalizar_codigo(entrada["solicitacaoCodigo"])
        solicitacao = await self.provider.buscar_solicitacao(codigo)
        if solicitacao is None:
            raise HTTPException(status_code=404, detail=f"Solicitação {codigo} não encontrada.")
        if solicitacao["situacaoRecepcao"] != "AGUARDANDO_RECEBIMENTO":
            raise HTTPException(status_code=409, detail=f"A solicitação {codigo} não está aguardando recebimento.")
        _exigir_conferencia(entrada["conferencia"])
        if not isinstance(entrada["quantidade"], int) or entrada["quantidade"] < 1:
            raise HTTPException(status_code=400, detail="Informe a quantidade de peças/frascos (1 ou mais).")
        if entrada["urgente"] and not str(entrada.get("motivoUrgencia") or "").strip():
            raise HTTPException(status_code=400, detail="Descreva o motivo da urgência.")
        if not str(entrada["procedimento"]).strip():
            raise HTTPException(status_code=400, detail="Selecione o procedimento.")

        tipo = entrada["tipoExame"]
        agora = agora_iso()
        numero = await self._proximo_numero(tipo)
        proxima_etapa = {"HP": "MACROSCOPIA", "CG": "PROCESSAMENTO", "CCV": "PROCESSAMENTO", "CO": "CONGELACAO"}[tipo]
        responsavel = responsavel_autenticado(usuario)
        materiais = [
            {
                "codigo": numero if indice == 1 else f"{numero}-F{indice}",
                "tipoItem": "AMOSTRA",
                "rotulo": f"Amostra {indice} · {solicitacao['descricaoMaterial']}",
                "origem": "ROTINA",
                "status": "DISPONIVEL",
                "criadoPor": responsavel,
                "criadoEm": agora,
                "filhos": [],
            }
            for indice in range(1, entrada["quantidade"] + 1)
        ]
        solicitacao.update({"situacaoRecepcao": "RECEBIDA", "casoNumero": numero, "statusAghuDescricao": "Recebido"})
        caso = {
            "numeroInterno": numero,
            "tipoExame": tipo,
            "solicitacao": solicitacao,
            "status": "RECEBIDO",
            "etapaAtual": proxima_etapa,
            "etapaAtualDesde": agora,
            "dataEntradaSap": agora,
            "responsavelEntrada": responsavel,
            "urgente": entrada["urgente"],
            "motivoUrgencia": str(entrada.get("motivoUrgencia") or "").strip() or None,
            "procedimento": entrada["procedimento"],
            "quantidade": entrada["quantidade"],
            "observacoes": str(entrada.get("observacoes") or "").strip() or None,
            "etapas": [
                {
                    "etapa": "RECEPCAO", "sequencia": 1, "status": "CONCLUIDA",
                    "iniciadaEm": agora, "concluidaEm": agora,
                    "responsavelInicio": responsavel, "responsavelFim": responsavel,
                },
                {"etapa": proxima_etapa, "sequencia": 2, "status": "PENDENTE"},
            ],
            "registros": [],
            "materiais": materiais,
            "ihqs": [],
            "naoConformidades": [],
            "devolucoes": [],
            "historico": [],
        }
        await self.provider.salvar_solicitacao(solicitacao)
        await self.provider.salvar_caso(caso)
        conferencia = await self.provider.adicionar_conferencia({
            **entrada["conferencia"],
            "solicitacaoCodigo": codigo,
            "casoNumero": numero,
            "resultado": "ACEITA",
            "conferidoPor": responsavel,
            "conferidoEm": agora,
        })
        await self.provider.adicionar_materiais(numero, materiais)
        anterior = {
            "solicitacao": codigo,
            "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO",
            "caso": None,
        }
        novo = {
            "solicitacao": codigo,
            "situacaoRecepcao": "RECEBIDA",
            "caso": numero,
            "status": "RECEBIDO",
            "etapaAtual": proxima_etapa,
            "quantidade": entrada["quantidade"],
            "procedimento": entrada["procedimento"],
            "conferencia": conferencia,
        }
        evento = _evento_historico(
            responsavel, "ENTRADA_CONFIRMADA", "Entrada confirmada",
            f"Nº interno {numero} gerado a partir da solicitação {codigo}. Conferência aceita. Encaminhado para {ETAPAS[proxima_etapa]}.",
            ocorrido_em=agora,
        )
        await self.provider.adicionar_historico(numero, evento)
        if entrada["urgente"]:
            await self.provider.adicionar_historico(numero, _evento_historico(
                responsavel, "URGENCIA_MARCADA", "Marcado como URGENTE", caso["motivoUrgencia"], ocorrido_em=agora
            ))
        await _auditar(self.session, usuario, ip, "ENTRADA_CONFIRMADA", f"caso_ap:{numero}", anterior, novo)
        resultado = await self.provider.buscar_caso(numero)
        return resultado or caso

    async def cancelar_caso(
        self, numero: str, motivo: str, usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Cancela caso ativo com motivo obrigatório e sem exclusão física."""
        numero = normalizar_codigo(numero)
        caso = await self.provider.buscar_caso(numero)
        if caso is None:
            raise HTTPException(status_code=404, detail=f"Caso {numero} não encontrado.")
        _exigir_caso_ativo(caso, numero, "cancelamento")
        motivo_limpo = motivo.strip()
        if not motivo_limpo:
            raise HTTPException(status_code=400, detail="Informe o motivo do cancelamento.")
        status_anterior = caso["status"]
        responsavel = responsavel_autenticado(usuario)
        agora = agora_iso()
        caso["status"] = "CANCELADO"
        caso["cancelamento"] = {"motivo": motivo_limpo, "canceladoPor": responsavel, "canceladoEm": agora}
        await self.provider.salvar_caso(caso)
        await self.provider.adicionar_historico(numero, _evento_historico(
            responsavel, "CASO_CANCELADO", "Caso cancelado", motivo_limpo, setor="Chefia/Administração", ocorrido_em=agora
        ))
        await _auditar(
            self.session, usuario, ip, "CASO_CANCELADO", f"caso_ap:{numero}",
            {"status": status_anterior}, {"status": "CANCELADO", "motivo": motivo_limpo},
        )
        return await self.provider.buscar_caso(numero) or caso

    async def acionar_plantao(
        self, numero: str, usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Registra uma única vez o acionamento de plantão para congelação."""
        numero = normalizar_codigo(numero)
        caso = await self.provider.buscar_caso(numero)
        if caso is None:
            raise HTTPException(status_code=404, detail=f"Caso {numero} não encontrado.")
        if caso["tipoExame"] != "CO":
            raise HTTPException(status_code=422, detail="O acionamento do plantão se aplica apenas a congelação.")
        if caso.get("plantaoAcionadoEm"):
            raise HTTPException(status_code=409, detail="O acionamento da equipe de plantão já foi registrado.")
        agora = agora_iso()
        responsavel = responsavel_autenticado(usuario)
        caso["plantaoAcionadoEm"] = agora
        await self.provider.salvar_caso(caso)
        await self.provider.adicionar_historico(numero, _evento_historico(
            responsavel,
            "PLANTAO_ACIONADO",
            "Equipe de plantão de congelação acionada",
            "Acionamento registrado pela recepção.",
            ocorrido_em=agora,
        ))
        await _auditar(
            self.session, usuario, ip, "PLANTAO_ACIONADO", f"caso_ap:{numero}",
            {"plantaoAcionadoEm": None}, {"plantaoAcionadoEm": agora},
        )
        return await self.provider.buscar_caso(numero) or caso

    async def registrar_nao_conformidade(
        self, entrada: dict[str, Any], usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Registra ocorrência e devolução nos três contextos atualmente suportados."""
        descricao = str(entrada["descricao"]).strip()
        if not descricao:
            raise HTTPException(status_code=400, detail="Descreva o que foi encontrado.")
        contexto = entrada["contexto"]
        agora = agora_iso()
        responsavel = responsavel_autenticado(usuario)
        caso_numero: str | None = None
        solicitacao_codigo: str | None = None
        status_caso_anterior: str | None = None

        if contexto["tipo"] == "SEM_ETIQUETA":
            unidade_origem = str(entrada.get("unidadeOrigem") or "").strip()
            if not unidade_origem:
                raise HTTPException(status_code=400, detail="Selecione a unidade de origem.")
            etapa = "Recepção (leitura)"
            etapa_codigo = "RECEPCAO"
        elif contexto["tipo"] == "SOLICITACAO":
            solicitacao_codigo = normalizar_codigo(contexto["solicitacaoCodigo"])
            solicitacao = await self.provider.buscar_solicitacao(solicitacao_codigo)
            if solicitacao is None:
                raise HTTPException(status_code=404, detail=f"Solicitação {solicitacao_codigo} não encontrada.")
            if solicitacao["situacaoRecepcao"] != "AGUARDANDO_RECEBIMENTO":
                raise HTTPException(status_code=409, detail=f"A solicitação {solicitacao_codigo} não está aguardando recebimento.")
            unidade_origem = solicitacao["unidade"]
            etapa = "Recepção (conferência)"
            etapa_codigo = "RECEPCAO"
        else:
            caso_numero = normalizar_codigo(contexto["casoNumero"])
            caso = await self.provider.buscar_caso(caso_numero)
            if caso is None:
                raise HTTPException(status_code=404, detail=f"Caso {caso_numero} não encontrado.")
            _exigir_caso_ativo(caso, caso_numero, "não conformidade")
            solicitacao_codigo = caso["solicitacao"]["codigoSolicitacao"]
            unidade_origem = caso["solicitacao"]["unidade"]
            etapa_codigo = caso.get("etapaAtual") or "RECEPCAO"
            etapa = ETAPAS[etapa_codigo]
            status_caso_anterior = caso["status"]

        tipo = entrada["tipo"]
        status_nc = "ABERTA" if entrada["novaAmostraSolicitada"] else "RESOLVIDA"
        nao_conformidade = await self.provider.adicionar_nao_conformidade({
            "casoNumero": caso_numero,
            "solicitacaoCodigo": solicitacao_codigo,
            "tipo": tipo,
            "descricao": descricao,
            "setor": SETOR_RECEPCAO,
            "etapa": etapa,
            "etapaCodigo": etapa_codigo,
            "unidadeOrigem": unidade_origem,
            "registradoPor": responsavel,
            "registradoEm": agora,
            "status": status_nc,
        })
        devolucao = await self.provider.adicionar_devolucao({
            "naoConformidadeId": nao_conformidade["id"],
            "casoNumero": caso_numero,
            "solicitacaoCodigo": solicitacao_codigo,
            "unidadeOrigem": unidade_origem,
            "devolvidoPor": responsavel,
            "novaAmostraSolicitada": entrada["novaAmostraSolicitada"],
            "situacao": "AGUARDANDO_NOVA_AMOSTRA" if entrada["novaAmostraSolicitada"] else "ENCERRADA",
            "devolvidaEm": agora,
        })

        status_solicitacao_anterior: str | None = None
        if solicitacao_codigo and contexto["tipo"] == "SOLICITACAO":
            solicitacao["situacaoRecepcao"] = "DEVOLVIDA"
            solicitacao["devolucaoId"] = devolucao["id"]
            status_solicitacao_anterior = "AGUARDANDO_RECEBIMENTO"
            await self.provider.salvar_solicitacao(solicitacao)
        if caso_numero:
            caso["status"] = "DEVOLVIDO"
            await self.provider.salvar_caso(caso)
            await self.provider.adicionar_historico(caso_numero, _evento_historico(
                responsavel, "NAO_CONFORMIDADE", "Não conformidade registrada",
                f"{TIPOS_NAO_CONFORMIDADE[tipo]} — {descricao} (identificada em {etapa}).", ocorrido_em=agora,
            ))
            await self.provider.adicionar_historico(caso_numero, _evento_historico(
                responsavel, "DEVOLUCAO", "Material devolvido à origem",
                f"Devolvido à unidade {unidade_origem}. Nova amostra solicitada: {'Sim' if entrada['novaAmostraSolicitada'] else 'Não'}.",
                ocorrido_em=agora,
            ))
        elif contexto["tipo"] == "SOLICITACAO":
            conferencia_input = contexto["conferencia"]
            await self.provider.adicionar_conferencia({
                **conferencia_input,
                "solicitacaoCodigo": solicitacao_codigo,
                "resultado": "REJEITADA",
                "observacao": f"{TIPOS_NAO_CONFORMIDADE[tipo]} — {descricao}",
                "conferidoPor": responsavel,
                "conferidoEm": agora,
            })

        anterior = (
            {"caso": caso_numero, "status": status_caso_anterior}
            if caso_numero
            else {"solicitacao": solicitacao_codigo, "situacaoRecepcao": status_solicitacao_anterior}
            if status_solicitacao_anterior
            else None
        )
        novo = {
            "naoConformidade": nao_conformidade["id"],
            "tipo": tipo,
            "etapa": etapa,
            "caso": caso_numero,
            "solicitacao": solicitacao_codigo,
            "status": "DEVOLVIDO" if caso_numero else None,
            "situacaoDevolucao": devolucao["situacao"],
        }
        await _auditar(
            self.session, usuario, ip, "NAO_CONFORMIDADE_DEVOLUCAO",
            f"devolucao:{devolucao['id']}", anterior, novo,
        )
        return {
            **devolucao,
            "naoConformidade": nao_conformidade,
            "rejeicaoNaRecepcao": not bool(caso_numero),
        }

    async def _proximo_numero(self, tipo: str) -> str:
        """Gera número por modalidade/ano; a chave primária e a solicitação são únicas."""
        ano = datetime.now(timezone.utc).strftime("%y")
        casos = await self.provider.listar_casos()
        maior = 0
        padrao = re.compile(rf"^{re.escape(tipo)}-(\d+)/{ano}$")
        for caso in casos:
            correspondencia = padrao.match(caso["numeroInterno"])
            if correspondencia:
                maior = max(maior, int(correspondencia.group(1)))
        return f"{tipo}-{maior + 1:04d}/{ano}"

    @staticmethod
    def _exigir_fonte_disponivel() -> None:
        """Simula indisponibilidade do provedor de solicitações no ambiente local."""
        if not settings.AP_MOCK_REQUESTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Não foi possível consultar as solicitações. Tente novamente.")

