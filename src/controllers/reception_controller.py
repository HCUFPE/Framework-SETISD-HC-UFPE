"""Regras de negócio já existentes no módulo de Recepção."""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
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
    "SEM_SOLICITACAO_OU_ETIQUETA": "Sem solicitação ou etiqueta do AGHU",
    "EXAME_NAO_CORRESPONDE_MATERIAL": "Exame não corresponde ao material",
    "FALTA_DESCRICAO_FRASCO": "Falta descrição no frasco",
    "IDENTIFICACAO_ILEGIVEL": "Identificação ilegível",
    "NUMERACAO_FRASCOS_DIVERGENTE": "Numeração dos frascos divergente",
    "QUANTIDADE_FRASCOS_DIVERGENTE": "Quantidade de frascos divergente",
    "LATERALIDADE_DIVERGENTE": "Lateralidade divergente",
    "FALTA_CARIMBO_ASSINATURA": "Falta carimbo ou assinatura",
    "ACONDICIONAMENTO_INADEQUADO": "Acondicionamento inadequado",
    "SOLICITACOES_DUPLICADAS": "Solicitações duplicadas",
    "PECAS_NAO_DESCRITAS": "Peças não descritas",
    "SISCAN_INCORRETO": "SISCAN incorreto",
    "SEM_AGENDAMENTO_CMCE": "Sem agendamento CMCE",
    "OUTROS": "Outros",
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


def _extrair_codigo_e_amostra(codigo: str) -> tuple[str, str | None]:
    """Decompõe leitura de etiqueta em (codigo_solicitacao, numero_amostra | None).

    Formatos aceitos, nesta ordem de precedência:
    1. ``<solicitação>:<tipo>``  → amostra = None
    2. ``<solicitação>-<amostra>``  (sufixo numérico)
    3. Código contínuo de exatamente 10 dígitos → primeiros 7 = solicitação, últimos 3 = amostra
    4. Qualquer outro valor → amostra = None
    """
    leitura = normalizar_codigo(codigo)
    if ":" in leitura:
        return leitura.split(":", 1)[0], None
    partes = leitura.rsplit("-", 1)
    if len(partes) == 2 and partes[1].isdigit():
        return partes[0], partes[1]
    if leitura.isdigit() and len(leitura) == 10:
        return leitura[:7], leitura[7:]
    return leitura, None


def _normalizar_numero_amostra(valor: str) -> str:
    """Remove zeros à esquerda de números puros para comparação tolerante."""
    return str(int(valor)) if valor.isdigit() else valor.strip().upper()


def _resolver_amostra_bipada(
    numero_amostra: str,
    exames: list[dict[str, Any]],
) -> dict[str, Any]:
    """Localiza o grupo de exame dono da amostra bipada.

    Retorna dicionário com:
    - ``amostraBipada``: número original da amostra
    - ``grupoSelecionadoId``: ID do grupo pendente correspondente (ou None)
    - ``examesFiltrados``: lista com o grupo pendente (ou vazia)
    - ``amostraBipadaSituacao``: metadados quando a amostra foi encontrada em grupo
      já recebido/devolvido (ou None)
    """
    normalizado = _normalizar_numero_amostra(numero_amostra)
    resultado: dict[str, Any] = {
        "amostraBipada": numero_amostra,
        "grupoSelecionadoId": None,
        "examesFiltrados": [],
        "amostraBipadaSituacao": None,
    }
    for exame in exames:
        for amostra in exame.get("amostras", []):
            if _normalizar_numero_amostra(amostra["numeroAmostra"]) == normalizado:
                if exame["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO":
                    resultado["grupoSelecionadoId"] = exame["id"]
                    resultado["examesFiltrados"] = [exame]
                else:
                    resultado["amostraBipadaSituacao"] = {
                        "grupoId": exame["id"],
                        "tipoExame": exame.get("tipoExameSugerido"),
                        "situacaoRecepcao": exame["situacaoRecepcao"],
                        "casoNumero": exame.get("casoNumero"),
                        "ihqCodigo": exame.get("ihqCodigo"),
                        "devolucaoId": exame.get("devolucaoId"),
                        "cancelamento": exame.get("cancelamento"),
                    }
                return resultado
    return resultado


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

    async def cancelar_exame_solicitacao(
        self, grupo_id: str, motivo: str, usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Cancela um grupo pendente e audita a mutação na mesma sessão."""
        identificador = normalizar_codigo(grupo_id)
        solicitacao = await self.provider.buscar_solicitacao(identificador)
        if solicitacao is None:
            raise HTTPException(status_code=404, detail=f"Exame {identificador} não encontrado.")
        if solicitacao["situacaoRecepcao"] != "AGUARDANDO_RECEBIMENTO":
            raise HTTPException(status_code=409, detail=f"O exame {identificador} não está aguardando recebimento.")
        motivo_limpo = motivo.strip()
        if not motivo_limpo:
            raise HTTPException(status_code=400, detail="Informe o motivo do cancelamento.")

        cancelamento = {
            "motivo": motivo_limpo,
            "canceladoPor": responsavel_autenticado(usuario),
            "canceladoEm": agora_iso(),
        }
        novo = await self.provider.cancelar_solicitacao(identificador, cancelamento)
        if novo is None:
            raise HTTPException(status_code=409, detail=f"O exame {identificador} não está aguardando recebimento.")
        await _auditar(
            self.session,
            usuario,
            ip,
            "SOLICITACAO_EXAME_CANCELADA",
            f"solicitacao_exame:{identificador}",
            {"situacaoRecepcao": solicitacao["situacaoRecepcao"]},
            {"situacaoRecepcao": "CANCELADA", "cancelamento": cancelamento},
        )
        return novo

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
        """Classifica a solicitação inteira a partir do código, amostra ou chave de grupo."""
        self._exigir_fonte_disponivel()
        codigo_solicitacao, numero_amostra = _extrair_codigo_e_amostra(codigo)
        exames = await self.provider.listar_exames_da_solicitacao(codigo_solicitacao)
        if not exames:
            return {"tipo": "NAO_ENCONTRADA"}

        # Resolver metadados da amostra bipada (se houver).
        meta_amostra: dict[str, Any] = {}
        if numero_amostra is not None:
            meta_amostra = _resolver_amostra_bipada(numero_amostra, exames)

        pendentes = [exame for exame in exames if exame["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"]
        if pendentes:
            resultado: dict[str, Any] = {"tipo": "PENDENTE", "codigoSolicitacao": codigo_solicitacao, "exames": pendentes}
            if meta_amostra:
                resultado.update(meta_amostra)
            return resultado

        recebidos = [exame for exame in exames if exame["situacaoRecepcao"] == "RECEBIDA"]
        if recebidos:
            recebimentos = [
                {
                    "siglaExame": exame["siglaExame"],
                    "nomeExame": exame["nomeExame"],
                    "casoNumero": exame.get("casoNumero") or exame.get("ihqCasoNumero") or "",
                    "ihqCodigo": exame.get("ihqCodigo"),
                }
                for exame in recebidos
            ]
            resultado = {"tipo": "RECEBIDA", "solicitacao": recebidos[0], "recebimentos": recebimentos}
            if meta_amostra:
                resultado["amostraBipada"] = meta_amostra.get("amostraBipada")
            return resultado

        solicitacao = exames[0]
        if solicitacao["situacaoRecepcao"] == "DEVOLVIDA":
            devolucao = next(
                (item for item in await self.provider.listar_devolucoes() if item["id"] == solicitacao.get("devolucaoId")),
                None,
            )
            tipo = devolucao["naoConformidade"]["tipo"] if devolucao else "OUTROS"
            resultado = {
                "tipo": "DEVOLVIDA",
                "solicitacao": solicitacao,
                "devolvidaEm": devolucao["devolvidaEm"] if devolucao else "",
                "tipoNaoConformidade": tipo,
            }
            if meta_amostra:
                resultado["amostraBipada"] = meta_amostra.get("amostraBipada")
            return resultado
        cancelados = [exame for exame in exames if exame["situacaoRecepcao"] == "CANCELADA"]
        if cancelados and len(cancelados) == len(exames):
            resultado = {
                "tipo": "CANCELADA",
                "solicitacao": solicitacao,
                "cancelamentos": [exame.get("cancelamento") for exame in cancelados],
            }
            if meta_amostra:
                resultado["amostraBipada"] = meta_amostra.get("amostraBipada")
            return resultado
        return {"tipo": "NAO_ENCONTRADA"}

    async def listar_exames_da_solicitacao(self, codigo: str) -> list[dict[str, Any]]:
        """Retorna os grupos recebidos, devolvidos e pendentes de um código AGHU."""
        return await self.provider.listar_exames_da_solicitacao(normalizar_codigo(codigo))

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
                    "codigoSolicitacao": caso["solicitacao"]["codigoSolicitacao"],
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
                "descricaoMaterial": ", ".join(dict.fromkeys(
                    amostra.get("descricaoMaterial", "")
                    for amostra in caso["solicitacao"].get("amostras", [])
                    if amostra.get("descricaoMaterial")
                )),
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
        """Confirma recebimento, recalculando o sequencial após conflito concorrente."""
        for tentativa in range(5):
            try:
                return await self._confirmar_entrada_tentativa(entrada, usuario, ip)
            except IntegrityError as erro:
                # O rollback limpa a transação inválida e a próxima tentativa relê o grupo
                # e recalcula _proximo_numero antes de fazer novos flushes.
                await self.session.rollback()
                if tentativa == 4:
                    raise HTTPException(
                        status_code=409,
                        detail="Conflito concorrente ao gerar o número interno. Tente novamente.",
                    ) from erro
        raise AssertionError("O retry de recebimento terminou sem resposta")

    async def _confirmar_entrada_tentativa(
        self, entrada: dict[str, Any], usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Confirma um grupo de exame e persiste somente as amostras desse grupo."""
        self._exigir_fonte_disponivel()
        grupo_id = normalizar_codigo(entrada["solicitacaoId"])
        solicitacao = await self.provider.buscar_solicitacao(grupo_id)
        if solicitacao is None:
            raise HTTPException(status_code=404, detail=f"Exame {grupo_id} não encontrado.")
        if solicitacao["situacaoRecepcao"] != "AGUARDANDO_RECEBIMENTO":
            raise HTTPException(status_code=409, detail=f"O exame {grupo_id} não está aguardando recebimento.")
        tipo = entrada["tipoExame"]
        if solicitacao["tipoExameSugerido"] != tipo:
            raise HTTPException(status_code=422, detail="O tipo de exame não corresponde ao grupo selecionado.")
        amostras = solicitacao.get("amostras") or []
        if not amostras:
            raise HTTPException(status_code=422, detail="O exame não tem amostras no AGHU.")
        if not str(entrada["procedimento"]).strip():
            raise HTTPException(status_code=400, detail="Selecione o procedimento.")

        agora = agora_iso()
        numero = await self._proximo_numero(tipo)
        proxima_etapa = {"HP": "MACROSCOPIA", "CG": "PROCESSAMENTO", "CCV": "PROCESSAMENTO", "CO": "CONGELACAO"}[tipo]
        responsavel = responsavel_autenticado(usuario)
        quantidade = len(amostras)
        materiais = [
            {
                "codigo": numero if indice == 0 else f"{numero}-F{indice + 1}",
                "tipoItem": "AMOSTRA",
                "rotulo": f"Amostra {amostra['numeroAmostra']}",
                "descricao": amostra.get("descricaoMaterial") or None,
                "numeroAmostraAghu": amostra["numeroAmostra"],
                "origem": "ROTINA",
                "status": "DISPONIVEL",
                "criadoPor": responsavel,
                "criadoEm": agora,
                "filhos": [],
            }
            for indice, amostra in enumerate(amostras)
        ]
        solicitacao.update({"situacaoRecepcao": "RECEBIDA", "casoNumero": numero})
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
            "procedimento": entrada["procedimento"],
            "quantidade": quantidade,
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
            "solicitacaoId": grupo_id,
            "solicitacaoCodigo": solicitacao["codigoSolicitacao"],
            "casoNumero": numero,
            "amostras": [amostra["numeroAmostra"] for amostra in amostras],
            "resultado": "ACEITA",
            "conferidoPor": responsavel,
            "conferidoEm": agora,
        })
        await self.provider.adicionar_materiais(numero, materiais)
        anterior = {
            "solicitacaoId": grupo_id,
            "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO",
            "caso": None,
        }
        novo = {
            "solicitacaoId": grupo_id,
            "situacaoRecepcao": "RECEBIDA",
            "caso": numero,
            "status": "RECEBIDO",
            "etapaAtual": proxima_etapa,
            "quantidade": quantidade,
            "procedimento": entrada["procedimento"],
            "conferencia": conferencia,
        }
        evento = _evento_historico(
            responsavel, "ENTRADA_CONFIRMADA", "Entrada confirmada",
            f"Nº interno {numero} gerado a partir da solicitação {solicitacao['codigoSolicitacao']} (exame {tipo}, amostras {', '.join(amostra['numeroAmostra'] for amostra in amostras)}). Conferência aceita. Encaminhado para {ETAPAS[proxima_etapa]}.",
            ocorrido_em=agora,
        )
        await self.provider.adicionar_historico(numero, evento)
        if entrada["urgente"]:
            await self.provider.adicionar_historico(numero, _evento_historico(
                responsavel, "URGENCIA_MARCADA", "Marcado como URGENTE", "Urgência informada na conferência.", ocorrido_em=agora
            ))
        await _auditar(self.session, usuario, ip, "ENTRADA_CONFIRMADA", f"caso_ap:{numero}", anterior, novo)
        resultado = await self.provider.buscar_caso(numero)
        return resultado or caso

    async def vincular_ihq(
        self, entrada: dict[str, Any], usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Vincula IHQ com retry de unicidade para códigos concorrentes."""
        for tentativa in range(5):
            try:
                return await self._vincular_ihq_tentativa(entrada, usuario, ip)
            except IntegrityError as erro:
                await self.session.rollback()
                if tentativa == 4:
                    raise HTTPException(
                        status_code=409,
                        detail="Conflito concorrente ao gerar o código interno da IHQ. Tente novamente.",
                    ) from erro
        raise AssertionError("O retry de vínculo IHQ terminou sem resposta")

    async def _vincular_ihq_tentativa(
        self, entrada: dict[str, Any], usuario: dict[str, Any], ip: str | None
    ) -> dict[str, Any]:
        """Recebe um grupo IHQ e o associa ao caso de origem selecionado."""
        self._exigir_fonte_disponivel()
        grupo_id = normalizar_codigo(entrada["solicitacaoId"])
        solicitacao = await self.provider.buscar_solicitacao(grupo_id)
        if solicitacao is None:
            raise HTTPException(status_code=404, detail=f"Exame {grupo_id} não encontrado.")
        if solicitacao["tipoExameSugerido"] != "IHQ":
            raise HTTPException(status_code=422, detail="A solicitação selecionada não é de imuno-histoquímica.")
        if solicitacao["situacaoRecepcao"] != "AGUARDANDO_RECEBIMENTO":
            raise HTTPException(status_code=409, detail=f"O exame {grupo_id} não está aguardando recebimento.")

        numero_caso = normalizar_codigo(entrada["casoOrigemNumero"])
        caso = await self.provider.buscar_caso(numero_caso)
        if caso is None:
            raise HTTPException(status_code=404, detail=f"Caso {numero_caso} não encontrado.")
        if caso["status"] in STATUS_INELEGIVEIS_IHQ:
            raise HTTPException(status_code=422, detail=f"O caso {numero_caso} não pode receber IHQ.")
        divergente = caso["solicitacao"].get("prontuario") != solicitacao.get("prontuario")
        if divergente and not entrada.get("divergenciaConfirmada"):
            raise HTTPException(status_code=422, detail="Confirme o vínculo apesar do prontuário divergente.")

        codigo_ihq = await self._proximo_numero("IH")
        agora = agora_iso()
        responsavel = responsavel_autenticado(usuario)
        ihq = {
            "codigoInternoIhq": codigo_ihq,
            "status": "SOLICITADA",
            "solicitacaoAghuCodigo": solicitacao["codigoSolicitacao"],
            "recebidaEm": agora,
            "registradaPor": responsavel,
            "anticorpos": [],
            "observacao": str(entrada.get("observacoes") or "").strip() or None,
        }
        caso.setdefault("ihqs", []).append(ihq)
        await self.provider.adicionar_ihq(numero_caso, grupo_id, ihq)

        solicitacao.update({
            "situacaoRecepcao": "RECEBIDA",
            "ihqCodigo": codigo_ihq,
            "ihqCasoNumero": numero_caso,
        })
        await self.provider.salvar_solicitacao(solicitacao)
        conferencia = await self.provider.adicionar_conferencia({
            "solicitacaoId": grupo_id,
            "solicitacaoCodigo": solicitacao["codigoSolicitacao"],
            "casoNumero": numero_caso,
            "amostras": [amostra["numeroAmostra"] for amostra in solicitacao.get("amostras", [])],
            "resultado": "ACEITA",
            "conferidoPor": responsavel,
            "conferidoEm": agora,
        })
        historico = _evento_historico(
            responsavel,
            "IHQ_VINCULADA",
            f"IHQ {codigo_ihq} vinculada ao caso",
            f"Solicitação AGHU {solicitacao['codigoSolicitacao']} recebida pela recepção.",
            ocorrido_em=agora,
        )
        await self.provider.adicionar_historico(numero_caso, historico)
        await _auditar(
            self.session,
            usuario,
            ip,
            "IHQ_VINCULADA",
            f"exame_ihq:{codigo_ihq}",
            {"solicitacaoId": grupo_id, "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO"},
            {
                "codigoInternoIhq": codigo_ihq,
                "casoOrigem": numero_caso,
                "divergenciaProntuario": divergente,
                "conferencia": conferencia,
            },
        )
        caso_atualizado = await self.provider.buscar_caso(numero_caso)
        return {"caso": caso_atualizado or caso, "ihq": ihq}

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
        """Registra uma ocorrência e devolve os grupos selecionados em uma única operação."""
        contexto = entrada["contexto"]
        agora = agora_iso()
        responsavel = responsavel_autenticado(usuario)
        caso_numero: str | None = None
        solicitacao_codigo: str | None = None
        solicitacao_ids: list[str] = []
        grupos: list[dict[str, Any]] = []
        status_caso_anterior: str | None = None

        if contexto["tipo"] == "SEM_ETIQUETA":
            unidade_origem = str(entrada.get("unidadeOrigem") or "").strip()
            if not unidade_origem:
                raise HTTPException(status_code=400, detail="Selecione a unidade de origem.")
            etapa = "Recepção (leitura)"
            etapa_codigo = "RECEPCAO"
        elif contexto["tipo"] == "SOLICITACAO":
            solicitacao_ids = list(dict.fromkeys(normalizar_codigo(item) for item in contexto["solicitacaoIds"]))
            for grupo_id in solicitacao_ids:
                solicitacao = await self.provider.buscar_solicitacao(grupo_id)
                if solicitacao is None:
                    raise HTTPException(status_code=404, detail=f"Exame {grupo_id} não encontrado.")
                if solicitacao["situacaoRecepcao"] != "AGUARDANDO_RECEBIMENTO":
                    raise HTTPException(status_code=409, detail=f"O exame {grupo_id} não está aguardando recebimento.")
                grupos.append(solicitacao)
            codigos = {grupo["codigoSolicitacao"] for grupo in grupos}
            if len(codigos) != 1:
                raise HTTPException(status_code=422, detail="Os exames devolvidos devem pertencer à mesma solicitação AGHU.")
            solicitacao_codigo = grupos[0]["codigoSolicitacao"]
            unidade_origem = grupos[0]["unidade"]
            etapa = "Recepção (conferência)"
            etapa_codigo = "RECEPCAO"
        else:
            caso_numero = normalizar_codigo(contexto["casoNumero"])
            caso = await self.provider.buscar_caso(caso_numero)
            if caso is None:
                raise HTTPException(status_code=404, detail=f"Caso {caso_numero} não encontrado.")
            _exigir_caso_ativo(caso, caso_numero, "não conformidade")
            solicitacao_codigo = caso["solicitacao"]["codigoSolicitacao"]
            solicitacao_ids = [caso["solicitacao"]["id"]]
            unidade_origem = caso["solicitacao"]["unidade"]
            etapa_codigo = caso.get("etapaAtual") or "RECEPCAO"
            etapa = ETAPAS[etapa_codigo]
            status_caso_anterior = caso["status"]

        tipo = entrada["tipo"]
        descricao = str(entrada.get("descricao") or "").strip()
        if tipo == "OUTROS" and not descricao:
            raise HTTPException(status_code=400, detail="Descreva a não conformidade.")
        descricao = descricao or TIPOS_NAO_CONFORMIDADE[tipo]
        status_nc = "ABERTA" if entrada["novaAmostraSolicitada"] else "RESOLVIDA"
        nao_conformidade = await self.provider.adicionar_nao_conformidade({
            "casoNumero": caso_numero,
            "solicitacaoCodigo": solicitacao_codigo,
            "solicitacaoIds": solicitacao_ids,
            "tipo": tipo,
            "descricao": descricao,
            "observacao": str(entrada.get("observacao") or "").strip() or None,
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
            "solicitacaoIds": solicitacao_ids,
            "unidadeOrigem": unidade_origem,
            "devolvidoPor": responsavel,
            "novaAmostraSolicitada": entrada["novaAmostraSolicitada"],
            "situacao": "AGUARDANDO_NOVA_AMOSTRA" if entrada["novaAmostraSolicitada"] else "ENCERRADA",
            "devolvidaEm": agora,
        })

        status_solicitacao_anterior: str | None = None
        if solicitacao_codigo and contexto["tipo"] == "SOLICITACAO":
            status_solicitacao_anterior = "AGUARDANDO_RECEBIMENTO"
            for grupo in grupos:
                grupo["situacaoRecepcao"] = "DEVOLVIDA"
                grupo["devolucaoId"] = devolucao["id"]
                await self.provider.salvar_solicitacao(grupo)
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
            for grupo in grupos:
                await self.provider.adicionar_conferencia({
                    "solicitacaoId": grupo["id"],
                    "solicitacaoCodigo": solicitacao_codigo,
                    "amostras": [amostra["numeroAmostra"] for amostra in grupo.get("amostras", [])],
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
            "solicitacaoIds": solicitacao_ids,
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
        """Gera número por modalidade/ano com unicidade no agregado correspondente."""
        ano = datetime.now(timezone.utc).strftime("%y")
        casos = await self.provider.listar_casos()
        maior = 0
        padrao = re.compile(rf"^{re.escape(tipo)}-(\d+)/{ano}$")
        for caso in casos:
            correspondencia = padrao.match(caso["numeroInterno"])
            if correspondencia:
                maior = max(maior, int(correspondencia.group(1)))
            if tipo == "IH":
                for ihq in caso.get("ihqs", []):
                    correspondencia = padrao.match(ihq.get("codigoInternoIhq", ""))
                    if correspondencia:
                        maior = max(maior, int(correspondencia.group(1)))
        return f"{tipo}-{maior + 1:04d}/{ano}"

    @staticmethod
    def _exigir_fonte_disponivel() -> None:
        """Simula indisponibilidade do provedor de solicitações no ambiente local."""
        if not settings.AP_MOCK_REQUESTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Não foi possível consultar as solicitações. Tente novamente.")
