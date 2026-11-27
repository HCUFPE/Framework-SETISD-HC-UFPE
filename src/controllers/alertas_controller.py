"""
Detector de Conflitos, Preparo e Janelas de Retorno (TASK-009)
==============================================================
Gera alertas estruturados (``tipo``, ``severidade``, ``mensagem``) para um item
da fila a partir das tabelas configuráveis ``regras_exames`` e
``incompatibilidades_exames`` e dos demais exames do mesmo prontuário.

Tipos (contrato ``TipoAlerta`` do frontend): ``INCOMPATIBILIDADE``,
``JANELA_RETORNO``, ``ANTECEDENCIA_PREPARO``, ``JEJUM_CLINICO``,
``IDADE_MAMOGRAFIA``, ``PRAZO_24H_VENCIDO`` e ``DUPLICIDADE``.

Todas as funções são puras: o instante de referência (``agora``, UTC sem fuso)
é recebido como parâmetro e a saída é ordenada de forma estável.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping, Optional

from .priorizacao_controller import normalizar_texto

SEVERIDADE_ORDEM: dict[str, int] = {"ALTA": 0, "MEDIA": 1, "INFO": 2}
STATUS_INATIVOS: frozenset[str] = frozenset({"CANCELADO"})
ORIGEM_FILA = "FILA"


def _alerta(tipo: str, severidade: str, mensagem: str) -> dict[str, str]:
    """Monta um alerta no formato do contrato ``IAlertaExame``."""
    return {"tipo": tipo, "severidade": severidade, "mensagem": mensagem}


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


def _como_data(valor: Any) -> Optional[date]:
    """Converte date/datetime/ISO string em ``date`` (ou ``None``)."""
    convertido = _como_datetime(valor)
    return convertido.date() if convertido else None


def _dias(n: int) -> str:
    """Formata quantidade de dias no singular/plural."""
    return f"{n} dia" if n == 1 else f"{n} dias"


def _fmt_data(valor: datetime | date) -> str:
    """Formata data no padrão brasileiro."""
    return valor.strftime("%d/%m/%Y")


def _ativo(registro: Mapping[str, Any]) -> bool:
    """Indica se uma regra/registro está ativo e não excluído logicamente."""
    return bool(registro.get("ativo", True)) and registro.get("deleted_at") is None


def _nome_exame(
    codigo: Optional[str],
    nome_informado: Optional[str],
    regras_exames: Mapping[str, Mapping[str, Any]],
) -> str:
    """Resolve o nome legível de um exame (regra cadastrada > nome informado > código)."""
    regra = regras_exames.get(normalizar_texto(codigo))
    if regra and regra.get("nome_exame"):
        return str(regra["nome_exame"])
    return str(nome_informado or codigo or "exame")


def _exame_considerado(exame: Mapping[str, Any]) -> bool:
    """Ignora exames cancelados ou excluídos."""
    return exame.get("status_operacional") not in STATUS_INATIVOS and exame.get("deleted_at") is None


def _alertas_incompatibilidade(
    item: Mapping[str, Any],
    outros_exames: list[Mapping[str, Any]],
    regras_exames: Mapping[str, Mapping[str, Any]],
    incompatibilidades: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Cruza o exame do item com os demais exames do prontuário contra a matriz."""
    codigo_item = normalizar_texto(item.get("codigo_exame"))
    if not codigo_item:
        return []

    matriz: dict[frozenset[str], list[Mapping[str, Any]]] = {}
    for inc in incompatibilidades:
        if not _ativo(inc):
            continue
        par = frozenset(
            {normalizar_texto(inc.get("codigo_exame_origem")), normalizar_texto(inc.get("codigo_exame_conflitante"))}
        )
        matriz.setdefault(par, []).append(inc)

    nome_item = _nome_exame(item.get("codigo_exame"), item.get("nome_exame"), regras_exames)
    data_item = _como_datetime(item.get("data_agendada_aghu"))
    alertas: list[dict[str, str]] = []
    for outro in outros_exames:
        codigo_outro = normalizar_texto(outro.get("codigo_exame"))
        if not codigo_outro or codigo_outro == codigo_item:
            continue
        for inc in matriz.get(frozenset({codigo_item, codigo_outro}), []):
            nome_outro = _nome_exame(outro.get("codigo_exame"), outro.get("nome_exame"), regras_exames)
            intervalo = int(inc.get("intervalo_minimo_dias") or 0)
            tipo_conflito = inc.get("tipo_conflito")
            limite = max(intervalo, 1) if tipo_conflito == "MESMO_DIA" else intervalo
            prefixo = f"{nome_item} × {nome_outro}: {inc.get('motivo')}"
            data_outro = _como_datetime(outro.get("data_agendada"))
            if data_item and data_outro:
                distancia = abs((data_item.date() - data_outro.date()).days)
                if distancia < limite:
                    alertas.append(
                        _alerta(
                            "INCOMPATIBILIDADE",
                            "ALTA",
                            f"{prefixo} Agendados com {_dias(distancia)} de intervalo "
                            f"(mínimo {_dias(limite)}).",
                        )
                    )
                continue
            orientacao = (
                "Não agendar no mesmo dia."
                if tipo_conflito == "MESMO_DIA"
                else f"Respeitar intervalo mínimo de {_dias(intervalo)}."
            )
            alertas.append(_alerta("INCOMPATIBILIDADE", "MEDIA", f"{prefixo} {orientacao}"))
    return alertas


def _alertas_duplicidade(
    item: Mapping[str, Any], outros_exames: list[Mapping[str, Any]]
) -> list[dict[str, str]]:
    """Sinaliza status DUPLICADA ou outro item ativo da fila com o mesmo exame."""
    if item.get("status_higienizacao") == "DUPLICADA":
        return [_alerta("DUPLICIDADE", "ALTA", "Solicitação marcada como duplicada na higienização.")]
    codigo_item = normalizar_texto(item.get("codigo_exame"))
    if codigo_item and item.get("prontuario"):
        for outro in outros_exames:
            if outro.get("origem") == ORIGEM_FILA and normalizar_texto(outro.get("codigo_exame")) == codigo_item:
                return [
                    _alerta(
                        "DUPLICIDADE",
                        "ALTA",
                        f"Prontuário já possui outro item ativo na fila para o mesmo exame "
                        f"(solicitação {outro.get('codigo_solicitacao')}).",
                    )
                ]
    return []


def _alerta_janela_retorno(
    item: Mapping[str, Any], regra: Mapping[str, Any], agora: datetime
) -> list[dict[str, str]]:
    """Valida a data do exame contra a janela máxima antes do retorno médico."""
    janela = regra.get("janela_retorno_max_horas")
    retorno = _como_data(item.get("data_retorno_medico"))
    if janela is None or retorno is None:
        return []
    janela = int(janela)
    retorno_dt = datetime.combine(retorno, datetime.min.time())
    agendada = _como_datetime(item.get("data_agendada_aghu"))
    nome = regra.get("nome_exame") or item.get("codigo_exame")
    if agendada:
        horas_antes = (retorno_dt - agendada).total_seconds() / 3600
        if horas_antes < 0:
            return [
                _alerta(
                    "JANELA_RETORNO",
                    "ALTA",
                    f"{nome} agendado para depois do retorno médico de {_fmt_data(retorno)}.",
                )
            ]
        if horas_antes > janela:
            return [
                _alerta(
                    "JANELA_RETORNO",
                    "ALTA",
                    f"{nome} agendado {horas_antes / 24:.0f} dias antes do retorno de {_fmt_data(retorno)}; "
                    f"o máximo é {janela}h ({janela / 24:g} dias).",
                )
            ]
        return []
    if retorno < agora.date():
        return [
            _alerta(
                "JANELA_RETORNO",
                "ALTA",
                f"Retorno médico de {_fmt_data(retorno)} já passou sem o exame {nome} agendado.",
            )
        ]
    inicio = retorno_dt - timedelta(hours=janela)
    return [
        _alerta(
            "JANELA_RETORNO",
            "INFO",
            f"Agendar {nome} entre {_fmt_data(inicio)} e o retorno de {_fmt_data(retorno)} "
            f"(até {janela}h antes).",
        )
    ]


def _alerta_antecedencia(
    item: Mapping[str, Any], regra: Mapping[str, Any], agora: datetime
) -> list[dict[str, str]]:
    """Valida a antecedência mínima exigida para o preparo do exame."""
    minimo = int(regra.get("antecedencia_minima_dias") or 0)
    if minimo <= 0:
        return []
    nome = regra.get("nome_exame") or item.get("codigo_exame")
    agendada = _como_datetime(item.get("data_agendada_aghu"))
    if agendada:
        base = _como_datetime(item.get("contato_iniciado_em")) or agora
        dias = (agendada.date() - base.date()).days
        if dias < minimo:
            return [
                _alerta(
                    "ANTECEDENCIA_PREPARO",
                    "ALTA",
                    f"{nome} agendado com {_dias(max(dias, 0))} de antecedência; "
                    f"o preparo exige no mínimo {_dias(minimo)}.",
                )
            ]
        return []
    orientacoes = f" {regra['orientacoes_preparo']}" if regra.get("orientacoes_preparo") else ""
    return [
        _alerta(
            "ANTECEDENCIA_PREPARO",
            "INFO",
            f"{nome} exige antecedência mínima de {_dias(minimo)} para preparo.{orientacoes}",
        )
    ]


def _alerta_jejum(item: Mapping[str, Any], regra: Mapping[str, Any]) -> list[dict[str, str]]:
    """Sinaliza jejum e prioridade matutina para pacientes diabéticos."""
    if not regra.get("exige_jejum"):
        return []
    nome = regra.get("nome_exame") or item.get("codigo_exame")
    if item.get("flag_diabetico_jejum") and regra.get("priorizar_manha_diabetico"):
        return [
            _alerta(
                "JEJUM_CLINICO",
                "MEDIA",
                f"Paciente diabético: {nome} exige jejum; agendar nos primeiros horários da manhã.",
            )
        ]
    return [_alerta("JEJUM_CLINICO", "INFO", f"{nome} exige jejum.")]


def _idade(nascimento: date, referencia: date) -> int:
    """Calcula a idade em anos completos."""
    return referencia.year - nascimento.year - (
        (referencia.month, referencia.day) < (nascimento.month, nascimento.day)
    )


def _alerta_idade(
    item: Mapping[str, Any], regra: Mapping[str, Any], agora: datetime
) -> list[dict[str, str]]:
    """Sinaliza idade mínima de alerta (ex.: mamografia a partir de 40 anos)."""
    minima = regra.get("idade_minima_alerta")
    if minima is None:
        return []
    minima = int(minima)
    nome = regra.get("nome_exame") or item.get("codigo_exame")
    nascimento = _como_data(item.get("data_nascimento"))
    if nascimento is None:
        return [
            _alerta(
                "IDADE_MAMOGRAFIA",
                "INFO",
                f"Conferir idade do paciente: {nome} é indicado a partir de {minima} anos.",
            )
        ]
    idade = _idade(nascimento, agora.date())
    if idade < minima:
        return [
            _alerta(
                "IDADE_MAMOGRAFIA",
                "MEDIA",
                f"Paciente com {idade} anos; {nome} é indicado a partir de {minima} anos.",
            )
        ]
    return []


def _alerta_prazo_24h(item: Mapping[str, Any], agora: datetime) -> list[dict[str, str]]:
    """Sinaliza prazo de confirmação de 24h vencido."""
    prazo = _como_datetime(item.get("prazo_confirmacao_em"))
    if item.get("status_operacional") == "AGUARDANDO_CONFIRMACAO_24H" and prazo and prazo < agora:
        return [
            _alerta(
                "PRAZO_24H_VENCIDO",
                "ALTA",
                f"Prazo de confirmação venceu em {prazo.strftime('%d/%m/%Y %H:%M')} (UTC); "
                f"liberar a vaga para o próximo da fila.",
            )
        ]
    return []


def detectar_alertas(
    item: Mapping[str, Any],
    outros_exames: Iterable[Mapping[str, Any]],
    regras_exames: Mapping[str, Mapping[str, Any]],
    incompatibilidades: Iterable[Mapping[str, Any]],
    agora: datetime,
) -> list[dict[str, str]]:
    """
    Gera a lista ordenada de alertas de um item da fila.

    Args:
        item: item da fila (exame, prontuário, status, datas, flags clínicas).
        outros_exames: demais exames do mesmo prontuário (``codigo_exame``, ``nome_exame``,
            ``data_agendada``, ``origem`` ``FILA``/``AGHU``, ``status_operacional``).
        regras_exames: regras de exame indexadas por código (``indexar_regras_exames``).
        incompatibilidades: registros de ``incompatibilidades_exames``.
        agora: instante de referência (UTC sem fuso).

    Returns:
        Lista de alertas ordenada por severidade, tipo e mensagem, sem repetições.
    """
    agora = agora.replace(tzinfo=None)
    outros = [o for o in outros_exames if _exame_considerado(o)]

    alertas: list[dict[str, str]] = []
    alertas += _alertas_incompatibilidade(item, outros, regras_exames, incompatibilidades)
    alertas += _alertas_duplicidade(item, outros)
    alertas += _alerta_prazo_24h(item, agora)

    regra = regras_exames.get(normalizar_texto(item.get("codigo_exame")))
    if regra and _ativo(regra):
        alertas += _alerta_janela_retorno(item, regra, agora)
        alertas += _alerta_antecedencia(item, regra, agora)
        alertas += _alerta_jejum(item, regra)
        alertas += _alerta_idade(item, regra, agora)

    unicos = {(a["tipo"], a["severidade"], a["mensagem"]): a for a in alertas}
    return sorted(
        unicos.values(),
        key=lambda a: (SEVERIDADE_ORDEM.get(a["severidade"], 9), a["tipo"], a["mensagem"]),
    )
