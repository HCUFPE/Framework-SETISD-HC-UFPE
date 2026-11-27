"""
Controller da Fila de Exames (TASK-010)
=======================================
Orquestra a fila de marcação: carrega itens e regras do SQLite local,
enriquece com dados somente-leitura do AGHU, aplica o motor de priorização
(TASK-008) e o detector de alertas (TASK-009), executa a máquina de estados
da confirmação em 24h e a vinculação por busca ativa, sempre com auditoria.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.audit_helper import registrar_auditoria
from ..providers.interfaces.exame_provider_interface import ExameProviderInterface
from ..providers.interfaces.fila_provider_interface import FilaProviderInterface
from .alertas_controller import detectar_alertas
from .priorizacao_controller import (
    FiltrosFila,
    calcular_prioridade,
    filtrar_fila,
    indexar_regras_exames,
    normalizar_texto,
    priorizar_fila,
)

logger = logging.getLogger("fila")

FUSO_CENTRAL = ZoneInfo("America/Recife")
PRAZO_CONFIRMACAO = timedelta(hours=24)
CATEGORIA_AUDITORIA = "NEGOCIO_CLINICO"

# Fluxo validado com a Central em 06/11 (não é regra configurável pela gestão).
TRANSICOES_PERMITIDAS: dict[str, frozenset[str]] = {
    "NA_FILA": frozenset({"AGUARDANDO_CONFIRMACAO_24H", "CANCELADO"}),
    "AGUARDANDO_CONFIRMACAO_24H": frozenset(
        {"CONFIRMADO_AGENDADO_AGHU", "SEM_RESPOSTA_24H", "CANCELADO"}
    ),
    "SEM_RESPOSTA_24H": frozenset({"NA_FILA", "CANCELADO"}),
    "CONFIRMADO_AGENDADO_AGHU": frozenset(),
    "CANCELADO": frozenset(),
}
STATUS_OPERACIONAIS_PADRAO: frozenset[str] = frozenset(
    {"NA_FILA", "AGUARDANDO_CONFIRMACAO_24H", "SEM_RESPOSTA_24H"}
)
HIGIENIZACAO_VINCULAVEL: frozenset[str] = frozenset({"NAO_ENCONTRADA", "DIVERGENCIA_EXAME"})
TAMANHO_MINIMO_BUSCA_NOME = 3


def agora_utc() -> datetime:
    """Instante atual em UTC sem fuso (padrão de armazenamento do SQLite local)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _utc_sem_fuso(valor: Optional[datetime]) -> Optional[datetime]:
    """Converte datetime para UTC sem fuso; valores sem fuso são tratados como UTC."""
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor
    return valor.astimezone(timezone.utc).replace(tzinfo=None)


def hoje_central(agora: datetime) -> date:
    """Data de calendário da Central (America/Recife) correspondente a ``agora`` (UTC)."""
    return agora.replace(tzinfo=timezone.utc).astimezone(FUSO_CENTRAL).date()


def _chave_aghu(codigo_solicitacao: Any, codigo_exame: Any) -> tuple[str, str]:
    """Chave de cruzamento fila × AGHU."""
    return str(codigo_solicitacao or "").strip(), normalizar_texto(codigo_exame)


async def _indexar_aghu(aghu: ExameProviderInterface) -> dict[tuple[str, str], dict[str, Any]]:
    """Lê o AGHU uma vez e indexa por (solicitação, exame); falha do AGHU não derruba a fila."""
    try:
        linhas = await aghu.listar_exames()
    except Exception as exc:  # noqa: BLE001 - resiliência: fila local continua disponível
        logger.warning("AGHU indisponível para enriquecer a fila: %s", exc)
        return {}
    return {_chave_aghu(l.get("codigo_solicitacao"), l.get("codigo_exame")): l for l in linhas}


def _enriquecer(
    item: dict[str, Any],
    aghu: Mapping[tuple[str, str], Mapping[str, Any]],
    regras_exames: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Completa nome do exame e data de solicitação com o AGHU (ou fallback local)."""
    linha = aghu.get(_chave_aghu(item.get("codigo_solicitacao"), item.get("codigo_exame")))
    regra = regras_exames.get(normalizar_texto(item.get("codigo_exame")))
    enriquecido = dict(item)
    enriquecido["nome_exame"] = (
        (linha or {}).get("nome_exame") or (regra or {}).get("nome_exame") or item.get("exame_informado_forms")
    )
    enriquecido["data_solicitacao"] = (linha or {}).get("data_solicitacao") or item.get("created_at")
    return enriquecido


def _como_outro_exame(item: Mapping[str, Any]) -> dict[str, Any]:
    """Representa um item da fila como 'outro exame' do prontuário."""
    return {
        "codigo_solicitacao": item.get("codigo_solicitacao"),
        "codigo_exame": item.get("codigo_exame"),
        "nome_exame": item.get("nome_exame"),
        "origem": "FILA",
        "data_agendada": item.get("data_agendada_aghu"),
        "status_operacional": item.get("status_operacional"),
        "deleted_at": item.get("deleted_at"),
    }


async def _carregar_regras(
    fila: FilaProviderInterface,
) -> tuple[list[dict[str, Any]], dict[str, Mapping[str, Any]], list[dict[str, Any]]]:
    """Relê as regras configuráveis a cada requisição (sem cache)."""
    return (
        await fila.listar_regras_prioridade(),
        indexar_regras_exames(await fila.listar_regras_exames()),
        await fila.listar_incompatibilidades(),
    )


async def montar_fila(
    fila: FilaProviderInterface,
    aghu: ExameProviderInterface,
    filtros: FiltrosFila,
    apenas_24h_vencidos: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
    agora: Optional[datetime] = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Monta a fila priorizada, filtrada e paginada.

    Returns:
        Tupla ``(itens da página, total após filtros)``.
    """
    agora = agora or agora_utc()
    regras, regras_exames, incompatibilidades = await _carregar_regras(fila)
    indice_aghu = await _indexar_aghu(aghu)

    itens = [_enriquecer(i, indice_aghu, regras_exames) for i in await fila.listar_itens_ativos()]
    priorizados = priorizar_fila(itens, regras, regras_exames, hoje_central(agora))

    selecionados = filtrar_fila(priorizados, filtros)
    if filtros.status_operacional is None:
        selecionados = [i for i in selecionados if i["status_operacional"] in STATUS_OPERACIONAIS_PADRAO]
    if filtros.status_higienizacao is None:
        selecionados = [i for i in selecionados if i["status_higienizacao"] == "VALIDA"]
    if apenas_24h_vencidos:
        selecionados = [
            i
            for i in selecionados
            if i["status_operacional"] == "AGUARDANDO_CONFIRMACAO_24H"
            and i.get("prazo_confirmacao_em") is not None
            and i["prazo_confirmacao_em"] < agora
        ]

    total = len(selecionados)
    pagina = selecionados[offset : offset + limit] if limit is not None else selecionados[offset:]

    por_prontuario: dict[str, list[dict[str, Any]]] = {}
    for item in itens:
        if item.get("prontuario"):
            por_prontuario.setdefault(item["prontuario"], []).append(item)
    for item in pagina:
        outros = [
            _como_outro_exame(o)
            for o in por_prontuario.get(item.get("prontuario") or "", [])
            if o["id"] != item["id"]
        ]
        item["alertas"] = detectar_alertas(item, outros, regras_exames, incompatibilidades, agora)
    return pagina, total


async def obter_detalhe(
    item_id: int,
    fila: FilaProviderInterface,
    aghu: ExameProviderInterface,
    agora: Optional[datetime] = None,
) -> dict[str, Any]:
    """Detalhe do item com outros exames do prontuário (fila + AGHU), alertas e preparo."""
    agora = agora or agora_utc()
    bruto = await fila.obter_item(item_id)
    if bruto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item da fila não encontrado.")

    regras, regras_exames, incompatibilidades = await _carregar_regras(fila)
    prontuario = bruto.get("prontuario")

    linhas_aghu: list[dict[str, Any]] = []
    if prontuario:
        try:
            linhas_aghu = await aghu.buscar_por_prontuario(prontuario)
        except Exception as exc:  # noqa: BLE001 - resiliência
            logger.warning("AGHU indisponível no detalhe do item %s: %s", item_id, exc)
    indice_aghu = {_chave_aghu(l.get("codigo_solicitacao"), l.get("codigo_exame")): l for l in linhas_aghu}

    chave_item = _chave_aghu(bruto.get("codigo_solicitacao"), bruto.get("codigo_exame"))
    indice_item = indice_aghu if chave_item in indice_aghu else await _indexar_aghu_solicitacao(aghu, bruto)
    item = _enriquecer(bruto, indice_item, regras_exames)

    item["score_prioridade"], item["motivos_prioridade"] = calcular_prioridade(
        item, regras, regras_exames, hoje_central(agora)
    )

    itens_prontuario = (
        [_enriquecer(i, indice_aghu, regras_exames) for i in await fila.listar_por_prontuario(prontuario)]
        if prontuario
        else []
    )
    outros = [_como_outro_exame(o) for o in itens_prontuario if o["id"] != item_id]
    chaves_fila = {_chave_aghu(i.get("codigo_solicitacao"), i.get("codigo_exame")) for i in itens_prontuario}
    chaves_fila.add(_chave_aghu(item.get("codigo_solicitacao"), item.get("codigo_exame")))
    for linha in linhas_aghu:
        chave = _chave_aghu(linha.get("codigo_solicitacao"), linha.get("codigo_exame"))
        if chave in chaves_fila:
            continue
        chaves_fila.add(chave)
        outros.append(
            {
                "codigo_solicitacao": linha.get("codigo_solicitacao"),
                "codigo_exame": linha.get("codigo_exame"),
                "nome_exame": linha.get("nome_exame"),
                "origem": "AGHU",
                "data_agendada": None,
                "status_operacional": None,
            }
        )

    item["alertas"] = detectar_alertas(item, outros, regras_exames, incompatibilidades, agora)
    item["outros_exames"] = outros
    regra = regras_exames.get(normalizar_texto(item.get("codigo_exame")))
    item["orientacoes_preparo"] = (regra or {}).get("orientacoes_preparo")
    return item


async def _indexar_aghu_solicitacao(
    aghu: ExameProviderInterface, item: Mapping[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    """Busca a própria solicitação do item no AGHU (quando o prontuário não a trouxe)."""
    try:
        linhas = await aghu.buscar_por_solicitacao(str(item.get("codigo_solicitacao") or ""))
    except Exception as exc:  # noqa: BLE001 - resiliência
        logger.warning("AGHU indisponível ao buscar solicitação: %s", exc)
        return {}
    return {_chave_aghu(l.get("codigo_solicitacao"), l.get("codigo_exame")): l for l in linhas}


def _valores(item: Mapping[str, Any], campos: Mapping[str, Any]) -> dict[str, Any]:
    """Extrai do item os valores atuais dos campos que serão alterados."""
    return {campo: item.get(campo) for campo in campos}


async def atualizar_status(
    item_id: int,
    novo_status: str,
    db: AsyncSession,
    fila: FilaProviderInterface,
    aghu: ExameProviderInterface,
    usuario: str,
    ip_origem: Optional[str],
    data_agendada_aghu: Optional[datetime] = None,
    preparo_orientado: Optional[bool] = None,
    observacoes: Optional[str] = None,
    agora: Optional[datetime] = None,
) -> dict[str, Any]:
    """Aplica uma transição de status da máquina de estados com auditoria."""
    agora = agora or agora_utc()
    item = await fila.obter_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item da fila não encontrado.")
    if item["status_higienizacao"] != "VALIDA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Somente solicitações com higienização VALIDA podem mudar de status "
                f"(atual: {item['status_higienizacao']})."
            ),
        )
    atual = item["status_operacional"]
    if novo_status not in TRANSICOES_PERMITIDAS.get(atual, frozenset()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transição de {atual} para {novo_status} não permitida.",
        )
    data_agendada = _utc_sem_fuso(data_agendada_aghu)
    if novo_status == "CONFIRMADO_AGENDADO_AGHU" and data_agendada is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe a data/hora agendada no AGHU para confirmar o agendamento.",
        )

    campos: dict[str, Any] = {"status_operacional": novo_status}
    if novo_status == "AGUARDANDO_CONFIRMACAO_24H":
        campos["contato_iniciado_em"] = agora
        campos["prazo_confirmacao_em"] = agora + PRAZO_CONFIRMACAO
    elif novo_status == "NA_FILA":
        campos["contato_iniciado_em"] = None
        campos["prazo_confirmacao_em"] = None
    if data_agendada is not None:
        campos["data_agendada_aghu"] = data_agendada
    if preparo_orientado is not None:
        campos["preparo_orientado"] = preparo_orientado
    if observacoes is not None:
        campos["observacoes"] = observacoes

    anteriores = _valores(item, campos)
    await fila.atualizar_item(item_id, campos)
    await registrar_auditoria(
        db=db,
        usuario=usuario,
        categoria=CATEGORIA_AUDITORIA,
        acao="ALTERAR_STATUS_FILA",
        recurso=f"acompanhamento_fila:{item_id}",
        dados_anteriores=anteriores,
        dados_novos=campos,
        ip_origem=ip_origem,
    )
    return await obter_detalhe(item_id, fila, aghu, agora)


async def vincular_solicitacao(
    item_id: int,
    codigo_solicitacao: str,
    codigo_exame: str,
    db: AsyncSession,
    fila: FilaProviderInterface,
    aghu: ExameProviderInterface,
    usuario: str,
    ip_origem: Optional[str],
    agora: Optional[datetime] = None,
) -> dict[str, Any]:
    """Vincula ao item a solicitação correta encontrada no AGHU (somente leitura) com auditoria."""
    item = await fila.obter_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item da fila não encontrado.")
    if item["status_higienizacao"] not in HIGIENIZACAO_VINCULAVEL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Somente itens NAO_ENCONTRADA ou DIVERGENCIA_EXAME podem ser vinculados "
                f"(atual: {item['status_higienizacao']})."
            ),
        )

    codigo_solicitacao = codigo_solicitacao.strip()
    alvo_exame = normalizar_texto(codigo_exame)
    linhas = await aghu.buscar_por_solicitacao(codigo_solicitacao)
    linha = next((l for l in linhas if normalizar_texto(l.get("codigo_exame")) == alvo_exame), None)
    if linha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitação {codigo_solicitacao} com exame {codigo_exame} não encontrada no AGHU.",
        )

    prontuario = linha.get("prontuario")
    exame_aghu = str(linha.get("codigo_exame"))
    if prontuario and await fila.existe_item_ativo(prontuario, exame_aghu, excluir_id=item_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe item ativo na fila para o prontuário {prontuario} e exame {exame_aghu}.",
        )

    campos = {
        "codigo_solicitacao": str(linha.get("codigo_solicitacao")),
        "codigo_exame": exame_aghu,
        "prontuario": prontuario,
        "status_higienizacao": "VALIDA",
    }
    anteriores = _valores(item, campos)
    await fila.atualizar_item(item_id, campos)
    await registrar_auditoria(
        db=db,
        usuario=usuario,
        categoria=CATEGORIA_AUDITORIA,
        acao="VINCULAR_SOLICITACAO",
        recurso=f"acompanhamento_fila:{item_id}",
        dados_anteriores=anteriores,
        dados_novos=campos,
        ip_origem=ip_origem,
    )
    return await obter_detalhe(item_id, fila, aghu, agora)


async def buscar_aghu(
    aghu: ExameProviderInterface,
    prontuario: Optional[str] = None,
    codigo_solicitacao: Optional[str] = None,
    nome: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Busca ativa somente-leitura no AGHU por solicitação, prontuário ou nome (combináveis)."""
    prontuario = (prontuario or "").strip() or None
    codigo_solicitacao = (codigo_solicitacao or "").strip() or None
    nome = " ".join((nome or "").split()) or None
    if not (prontuario or codigo_solicitacao or nome):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe prontuario, codigo_solicitacao ou nome para a busca.",
        )
    if nome and len(nome) < TAMANHO_MINIMO_BUSCA_NOME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A busca por nome exige ao menos {TAMANHO_MINIMO_BUSCA_NOME} caracteres.",
        )

    if codigo_solicitacao:
        resultado = await aghu.buscar_por_solicitacao(codigo_solicitacao)
    elif prontuario:
        resultado = await aghu.buscar_por_prontuario(prontuario)
    else:
        resultado = await aghu.buscar_por_nome(nome or "")

    if prontuario:
        resultado = [r for r in resultado if str(r.get("prontuario") or "") == prontuario]
    if nome:
        alvo = normalizar_texto(nome)
        resultado = [r for r in resultado if alvo in normalizar_texto(r.get("nome"))]
    return resultado


def montar_filtros(**kwargs: Any) -> FiltrosFila:
    """Cria ``FiltrosFila`` ignorando valores vazios."""
    filtros = FiltrosFila()
    valores = {k: v for k, v in kwargs.items() if v not in (None, "")}
    return replace(filtros, **valores)
