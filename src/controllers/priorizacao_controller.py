"""
Motor Determinístico de Priorização Clínica da Fila de Exames (TASK-008)
========================================================================
Calcula ``score_prioridade`` e ``motivos_prioridade`` de cada item da fila a
partir das regras configuráveis de ``regras_prioridade`` (nenhum peso é fixo
no código), ordena a fila de forma determinística e aplica filtros
operacionais/geográficos que nunca alteram a pontuação.

Composição do score:
- Grupo clínico principal: MAIOR peso entre as regras ``CLINICA``,
  ``GRUPO_CLINICO`` e ``VULNERAVEL`` que casarem (não se somam).
- Rotina: regra ``GRUPO_CLINICO`` com termo ``ROTINA``, aplicada somente
  quando nenhum outro grupo casar.
- Bônus aditivos: ``AFINIDADE_EXAME`` e ``RETORNO_PROXIMO``.

Todas as funções são puras (sem I/O): recebem itens e regras como dicts e a
data de referência como parâmetro.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping, Optional

logger = logging.getLogger("priorizacao")

TIPOS_GRUPO_CLINICO: frozenset[str] = frozenset({"CLINICA", "GRUPO_CLINICO", "VULNERAVEL"})
TERMO_ROTINA = "ROTINA"
TERMO_HEMODIALISE = "HEMODIALISE"
TAMANHO_MINIMO_TERMO_AFINIDADE = 4

# Palavras genéricas ignoradas na comparação de afinidade (normalização de texto,
# não regra de negócio: não alteram pesos nem quais clínicas têm prioridade).
PALAVRAS_GENERICAS_AFINIDADE: frozenset[str] = frozenset(
    {
        "CLINICA", "CLINICO", "CLINICAS", "EXAME", "EXAMES", "COMPLETO", "COMPLETA",
        "TOTAL", "AMBULATORIO", "AMBULATORIAL", "SERVICO", "UNIDADE", "SETOR",
        "DIGITAL", "BILATERAL", "NECESSARIO", "PARA", "COM", "SEM",
    }
)

_REGEX_RETORNO = re.compile(r"^\s*<=\s*(\d+)\s*$")
_REGEX_SEPARADOR_PALAVRAS = re.compile(r"[^A-Z0-9]+")


@dataclass(frozen=True)
class FiltrosFila:
    """Filtros operacionais e geográficos aplicados sobre a fila já pontuada."""

    codigo_exame: Optional[str] = None
    unidade: Optional[str] = None
    status_operacional: Optional[str] = None
    status_higienizacao: Optional[str] = None
    municipio: Optional[str] = None
    regiao: Optional[str] = None
    apenas_tfd: bool = False
    busca: Optional[str] = None


def normalizar_texto(texto: Optional[str]) -> str:
    """Remove acentos, converte para maiúsculas e colapsa espaços."""
    if not texto:
        return ""
    decomposto = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return " ".join(sem_acento.upper().split())


def _termos_regra(valor_match: Optional[str]) -> list[str]:
    """Separa o ``valor_match`` em termos normalizados (separador vírgula)."""
    return [t for t in (normalizar_texto(p) for p in (valor_match or "").split(",")) if t]


def _palavras(texto: Optional[str]) -> set[str]:
    """Extrai palavras significativas (4+ letras, não genéricas) de um texto."""
    return {
        p
        for p in _REGEX_SEPARADOR_PALAVRAS.split(normalizar_texto(texto))
        if len(p) >= TAMANHO_MINIMO_TERMO_AFINIDADE and p not in PALAVRAS_GENERICAS_AFINIDADE
    }


def _como_data(valor: Any) -> Optional[date]:
    """Converte date/datetime/ISO string em ``date`` (ou ``None``)."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.fromisoformat(str(valor)).date()
    except ValueError:
        return None


def _como_datetime(valor: Any) -> Optional[datetime]:
    """Converte datetime/date/ISO string em ``datetime`` sem fuso (ou ``None``)."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time())
    try:
        return datetime.fromisoformat(str(valor)).replace(tzinfo=None)
    except ValueError:
        return None


def filtrar_regras_ativas(regras: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Mantém apenas regras com ``ativo`` verdadeiro, sem ``deleted_at`` e peso positivo."""
    return [
        r
        for r in regras
        if r.get("ativo", True) and r.get("deleted_at") is None and int(r.get("peso") or 0) > 0
    ]


def _eh_regra_rotina(regra: Mapping[str, Any]) -> bool:
    """Indica se a regra é o grupo de rotina (fallback)."""
    return regra.get("tipo_criterio") == "GRUPO_CLINICO" and TERMO_ROTINA in _termos_regra(
        regra.get("valor_match")
    )


def regra_grupo_casa(regra: Mapping[str, Any], item: Mapping[str, Any]) -> bool:
    """Verifica se uma regra de grupo clínico casa com o item."""
    termos = _termos_regra(regra.get("valor_match"))
    if not termos:
        return False
    texto_item = " | ".join(
        normalizar_texto(item.get(campo))
        for campo in ("especialidade_solicitante", "unidade_solicitante", "grupo_prioritario_manual")
    )
    for termo in termos:
        if termo in texto_item:
            return True
        if termo == TERMO_HEMODIALISE and item.get("flag_hemodialise"):
            return True
    return False


def _bonus_retorno(regra: Mapping[str, Any], item: Mapping[str, Any], hoje: date) -> bool:
    """Retorna True quando o retorno médico está entre hoje e hoje + N dias."""
    correspondencia = _REGEX_RETORNO.match(str(regra.get("valor_match") or ""))
    if not correspondencia:
        logger.warning(
            "Regra RETORNO_PROXIMO %r ignorada: valor_match inválido %r (esperado '<=N').",
            regra.get("codigo"),
            regra.get("valor_match"),
        )
        return False
    retorno = _como_data(item.get("data_retorno_medico"))
    if retorno is None:
        return False
    dias = (retorno - hoje).days
    return 0 <= dias <= int(correspondencia.group(1))


def _bonus_afinidade(
    item: Mapping[str, Any], regras_exames: Mapping[str, Mapping[str, Any]]
) -> bool:
    """Retorna True quando a clínica solicitante compartilha termo com o exame."""
    regra_exame = regras_exames.get(normalizar_texto(item.get("codigo_exame")))
    if not regra_exame:
        return False
    palavras_solicitante = _palavras(item.get("especialidade_solicitante")) | _palavras(
        item.get("unidade_solicitante")
    )
    palavras_exame = _palavras(regra_exame.get("unidade_executora")) | _palavras(
        regra_exame.get("nome_exame")
    )
    return bool(palavras_solicitante & palavras_exame)


def _motivo(regra: Mapping[str, Any]) -> str:
    """Formata o motivo de pontuação de uma regra."""
    return f"{regra.get('nome')} +{int(regra.get('peso') or 0)}"


def indexar_regras_exames(
    regras_exames: Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    """Indexa regras de exame ativas pelo código do exame normalizado."""
    return {
        normalizar_texto(r.get("codigo_exame")): r
        for r in regras_exames
        if r.get("ativo", True) and r.get("deleted_at") is None and r.get("codigo_exame")
    }


def calcular_prioridade(
    item: Mapping[str, Any],
    regras: Iterable[Mapping[str, Any]],
    regras_exames: Mapping[str, Mapping[str, Any]],
    hoje: date,
) -> tuple[int, list[str]]:
    """
    Calcula o score e os motivos de prioridade de um item da fila.

    Args:
        item: dados do item (especialidade, unidade, grupo manual, flags, retorno, exame).
        regras: regras de ``regras_prioridade`` (inativas/excluídas são ignoradas).
        regras_exames: regras de exame indexadas por código (ver ``indexar_regras_exames``).
        hoje: data de referência para o bônus de retorno próximo.

    Returns:
        Tupla ``(score, motivos)``; a soma dos pesos citados nos motivos é igual ao score.
    """
    ativas = filtrar_regras_ativas(regras)

    grupos = [
        r
        for r in ativas
        if r.get("tipo_criterio") in TIPOS_GRUPO_CLINICO
        and not _eh_regra_rotina(r)
        and regra_grupo_casa(r, item)
    ]
    principal: Optional[Mapping[str, Any]] = None
    if grupos:
        principal = min(grupos, key=lambda r: (-int(r["peso"]), str(r.get("codigo") or "")))
    else:
        rotinas = sorted(
            (r for r in ativas if _eh_regra_rotina(r)), key=lambda r: str(r.get("codigo") or "")
        )
        principal = rotinas[0] if rotinas else None

    bonus: list[Mapping[str, Any]] = []
    for regra in ativas:
        tipo = regra.get("tipo_criterio")
        if tipo == "RETORNO_PROXIMO" and _bonus_retorno(regra, item, hoje):
            bonus.append(regra)
        elif tipo == "AFINIDADE_EXAME" and _bonus_afinidade(item, regras_exames):
            bonus.append(regra)
    bonus.sort(key=lambda r: (-int(r["peso"]), str(r.get("nome") or "")))

    aplicadas = ([principal] if principal else []) + bonus
    score = sum(int(r["peso"]) for r in aplicadas)
    return score, [_motivo(r) for r in aplicadas]


def _chave_ordenacao(item: Mapping[str, Any]) -> tuple[int, int, datetime, int]:
    """Chave determinística: score desc, data de solicitação asc (sem data no fim), id asc."""
    data = _como_datetime(item.get("data_solicitacao"))
    return (
        -int(item.get("score_prioridade") or 0),
        0 if data is not None else 1,
        data or datetime.max,
        int(item.get("id") or 0),
    )


def priorizar_fila(
    itens: Iterable[Mapping[str, Any]],
    regras: Iterable[Mapping[str, Any]],
    regras_exames: Mapping[str, Mapping[str, Any]],
    hoje: date,
) -> list[dict[str, Any]]:
    """
    Pontua e ordena a fila de forma determinística.

    Retorna cópias dos itens com ``score_prioridade`` e ``motivos_prioridade``.
    """
    regras_lista = list(regras)
    priorizados: list[dict[str, Any]] = []
    for item in itens:
        score, motivos = calcular_prioridade(item, regras_lista, regras_exames, hoje)
        novo = dict(item)
        novo["score_prioridade"] = score
        novo["motivos_prioridade"] = motivos
        priorizados.append(novo)
    priorizados.sort(key=_chave_ordenacao)
    return priorizados


def _item_atende_filtros(item: Mapping[str, Any], filtros: FiltrosFila) -> bool:
    """Verifica se um item atende a todos os filtros informados."""
    if filtros.codigo_exame and normalizar_texto(item.get("codigo_exame")) != normalizar_texto(
        filtros.codigo_exame
    ):
        return False
    if filtros.unidade and normalizar_texto(filtros.unidade) not in normalizar_texto(
        item.get("unidade_solicitante")
    ):
        return False
    if filtros.status_operacional and item.get("status_operacional") != filtros.status_operacional:
        return False
    if filtros.status_higienizacao and item.get("status_higienizacao") != filtros.status_higienizacao:
        return False
    if filtros.municipio and normalizar_texto(item.get("municipio")) != normalizar_texto(
        filtros.municipio
    ):
        return False
    if filtros.regiao and item.get("regiao_geografica") != filtros.regiao:
        return False
    if filtros.apenas_tfd and not item.get("utiliza_tfd"):
        return False
    if filtros.busca:
        busca = filtros.busca.strip()
        busca_normalizada = normalizar_texto(busca)
        if not (
            busca == str(item.get("prontuario") or "")
            or busca == str(item.get("codigo_solicitacao") or "")
            or (busca_normalizada and busca_normalizada in normalizar_texto(item.get("nome_paciente")))
        ):
            return False
    return True


def filtrar_fila(
    itens_priorizados: Iterable[Mapping[str, Any]], filtros: FiltrosFila
) -> list[dict[str, Any]]:
    """
    Aplica filtros sobre a fila já pontuada, preservando score, motivos e ordem.
    """
    return [dict(item) for item in itens_priorizados if _item_atende_filtros(item, filtros)]
