"""
Testes do Detector de Conflitos, Preparo e Janelas de Retorno (TASK-009)
========================================================================
Cobre os critérios do CARE-RF007 / CARE-UC004: par incompatível
(colonoscopia + sangue), estouro da janela de espirometria (>10 dias / após o
retorno), INR acima de 72h, além de preparo, jejum, idade, prazo 24h e
duplicidade, usando as regras do seed inicial.
"""

from datetime import date, datetime, timedelta
from typing import Any

import pytest

from src.controllers.alertas_controller import detectar_alertas
from src.controllers.priorizacao_controller import indexar_regras_exames
from src.resources.seed_exames import (
    INCOMPATIBILIDADES_EXAMES_INICIAIS,
    REGRAS_EXAMES_INICIAIS,
)

AGORA = datetime(2026, 12, 1, 9, 0)


def _regras_exames(**alteracoes: dict[str, Any]) -> dict[str, Any]:
    """Regras de exame do seed, com alterações opcionais por código."""
    return indexar_regras_exames(
        dict(r, deleted_at=None, **alteracoes.get(r["codigo_exame"], {})) for r in REGRAS_EXAMES_INICIAIS
    )


def _incompat(ativo: bool = True) -> list[dict[str, Any]]:
    """Matriz de incompatibilidades do seed."""
    return [dict(i, deleted_at=None, ativo=ativo) for i in INCOMPATIBILIDADES_EXAMES_INICIAIS]


def _item(codigo_exame: str, **campos: Any) -> dict[str, Any]:
    """Item de fila mínimo."""
    base: dict[str, Any] = {
        "id": 1,
        "codigo_solicitacao": "890001",
        "codigo_exame": codigo_exame,
        "prontuario": "1023456",
        "status_higienizacao": "VALIDA",
        "status_operacional": "NA_FILA",
        "data_agendada_aghu": None,
        "data_retorno_medico": None,
        "contato_iniciado_em": None,
        "prazo_confirmacao_em": None,
        "flag_diabetico_jejum": False,
    }
    base.update(campos)
    return base


def _outro(codigo_exame: str, data_agendada: Any = None, origem: str = "FILA", **campos: Any) -> dict[str, Any]:
    """Outro exame do mesmo prontuário."""
    return {"codigo_exame": codigo_exame, "data_agendada": data_agendada, "origem": origem,
            "codigo_solicitacao": "890099", **campos}


def _tipos(alertas: list[dict[str, str]], tipo: str) -> list[dict[str, str]]:
    return [a for a in alertas if a["tipo"] == tipo]


def _detectar(item: dict[str, Any], outros: list[dict[str, Any]] | None = None, **kw: Any) -> list[dict[str, str]]:
    return detectar_alertas(
        item, outros or [], kw.get("regras", _regras_exames()), kw.get("incompat", _incompat()), AGORA
    )


# ---------------------------------------------------------------------------
# 1. Estrutura
# ---------------------------------------------------------------------------


def test_regra_desativada_nao_gera_alerta() -> None:
    alertas = _detectar(_item("COLONO"), [_outro("HEMO")], incompat=_incompat(ativo=False))
    assert _tipos(alertas, "INCOMPATIBILIDADE") == []


def test_exame_sem_regra_e_sem_outros_exames_nao_gera_alerta() -> None:
    assert _detectar(_item("CMREP")) == []


def test_execucoes_repetidas_sao_identicas_e_ordenadas_por_severidade() -> None:
    item = _item("COLONO", flag_diabetico_jejum=True, data_agendada_aghu=AGORA + timedelta(days=1))
    outros = [_outro("HEMO", AGORA + timedelta(days=1)), _outro("USAX")]
    primeira = _detectar(item, outros)
    assert primeira == _detectar(item, list(reversed(outros)))
    ordem = [a["severidade"] for a in primeira]
    assert ordem == sorted(ordem, key={"ALTA": 0, "MEDIA": 1, "INFO": 2}.__getitem__)
    assert all(set(a) == {"tipo", "severidade", "mensagem"} for a in primeira)


# ---------------------------------------------------------------------------
# 2. Incompatibilidade e duplicidade
# ---------------------------------------------------------------------------


def test_colonoscopia_e_hemograma_pendentes_geram_alerta_media_nos_dois_sentidos() -> None:
    colono = _tipos(_detectar(_item("COLONO"), [_outro("HEMO")]), "INCOMPATIBILIDADE")
    assert len(colono) == 1 and colono[0]["severidade"] == "MEDIA"
    assert "2 dias" in colono[0]["mensagem"]

    hemo = _tipos(_detectar(_item("HEMO"), [_outro("COLONO")]), "INCOMPATIBILIDADE")
    assert len(hemo) == 1 and hemo[0]["severidade"] == "MEDIA"


def test_agendados_com_intervalo_insuficiente_geram_alta() -> None:
    item = _item("COLONO", data_agendada_aghu=datetime(2026, 12, 10, 8))
    alertas = _tipos(_detectar(item, [_outro("HEMO", datetime(2026, 12, 11, 7))]), "INCOMPATIBILIDADE")
    assert [a["severidade"] for a in alertas] == ["ALTA"]


def test_ressonancia_e_oftalmo_no_mesmo_dia_geram_alta() -> None:
    item = _item("RMCRAN", data_agendada_aghu=datetime(2026, 12, 10, 8))
    alertas = _tipos(_detectar(item, [_outro("OFTALM", datetime(2026, 12, 10, 14), origem="AGHU")]), "INCOMPATIBILIDADE")
    assert [a["severidade"] for a in alertas] == ["ALTA"]


def test_intervalo_respeitado_nao_gera_alerta() -> None:
    item = _item("COLONO", data_agendada_aghu=datetime(2026, 12, 10, 8))
    assert _tipos(_detectar(item, [_outro("HEMO", datetime(2026, 12, 15, 8))]), "INCOMPATIBILIDADE") == []


def test_exame_cancelado_nao_e_considerado() -> None:
    outros = [_outro("HEMO", status_operacional="CANCELADO")]
    assert _tipos(_detectar(_item("COLONO"), outros), "INCOMPATIBILIDADE") == []


def test_mesmo_exame_duas_vezes_no_prontuario_gera_duplicidade() -> None:
    alertas = _tipos(_detectar(_item("USAX"), [_outro("USAX")]), "DUPLICIDADE")
    assert [a["severidade"] for a in alertas] == ["ALTA"]


def test_status_duplicada_gera_duplicidade() -> None:
    assert _tipos(_detectar(_item("USAX", status_higienizacao="DUPLICADA")), "DUPLICIDADE")


def test_mesmo_exame_no_aghu_nao_e_duplicidade_da_fila() -> None:
    assert _tipos(_detectar(_item("USAX"), [_outro("USAX", origem="AGHU")]), "DUPLICIDADE") == []


# ---------------------------------------------------------------------------
# 3. Regras por exame
# ---------------------------------------------------------------------------

RETORNO = date(2026, 12, 20)


@pytest.mark.parametrize(
    ("exame", "agendada", "severidade"),
    [
        ("ESPIRO", datetime(2026, 12, 8, 8), "ALTA"),   # 12 dias antes (> 240h)
        ("ESPIRO", datetime(2026, 12, 21, 8), "ALTA"),  # depois do retorno
        ("ESPIRO", datetime(2026, 12, 15, 8), None),    # dentro da janela
        ("INR", datetime(2026, 12, 16, 8), "ALTA"),     # 4 dias antes (> 72h)
        ("INR", datetime(2026, 12, 18, 8), None),       # 2 dias antes
        ("INR", None, "INFO"),                          # sem data
    ],
)
def test_janela_de_retorno(exame: str, agendada: datetime | None, severidade: str | None) -> None:
    item = _item(exame, data_retorno_medico=RETORNO, data_agendada_aghu=agendada,
                 contato_iniciado_em=datetime(2026, 12, 1))
    alertas = _tipos(_detectar(item), "JANELA_RETORNO")
    assert [a["severidade"] for a in alertas] == ([severidade] if severidade else [])


def test_janela_de_retorno_ja_passado_sem_data() -> None:
    item = _item("INR", data_retorno_medico=date(2026, 11, 30))
    assert [a["severidade"] for a in _tipos(_detectar(item), "JANELA_RETORNO")] == ["ALTA"]


def test_colonoscopia_agendada_sem_tempo_de_preparo() -> None:
    item = _item("COLONO", data_agendada_aghu=AGORA + timedelta(days=1))
    alertas = _tipos(_detectar(item), "ANTECEDENCIA_PREPARO")
    assert [a["severidade"] for a in alertas] == ["ALTA"]


def test_colonoscopia_sem_data_recebe_orientacao_de_preparo() -> None:
    alertas = _tipos(_detectar(_item("COLONO")), "ANTECEDENCIA_PREPARO")
    assert [a["severidade"] for a in alertas] == ["INFO"]
    assert "3 dias" in alertas[0]["mensagem"]


def test_diabetico_com_exame_em_jejum_gera_media() -> None:
    alertas = _tipos(_detectar(_item("HEMO", flag_diabetico_jejum=True)), "JEJUM_CLINICO")
    assert [a["severidade"] for a in alertas] == ["MEDIA"]
    assert "manhã" in alertas[0]["mensagem"]


def test_nao_diabetico_com_exame_em_jejum_gera_info() -> None:
    assert [a["severidade"] for a in _tipos(_detectar(_item("HEMO")), "JEJUM_CLINICO")] == ["INFO"]


@pytest.mark.parametrize(
    ("nascimento", "severidade"),
    [(None, "INFO"), (date(1990, 1, 1), "MEDIA"), (date(1970, 1, 1), None)],
)
def test_alerta_etario_mamografia(nascimento: date | None, severidade: str | None) -> None:
    alertas = _tipos(_detectar(_item("RXMM1", data_nascimento=nascimento)), "IDADE_MAMOGRAFIA")
    assert [a["severidade"] for a in alertas] == ([severidade] if severidade else [])


def test_regra_de_exame_desativada_nao_gera_alerta_de_regra() -> None:
    regras = _regras_exames(HEMO={"ativo": False})
    assert _detectar(_item("HEMO", flag_diabetico_jejum=True), regras=regras) == []


@pytest.mark.parametrize(("delta_horas", "esperado"), [(-1, ["ALTA"]), (2, [])])
def test_prazo_24h(delta_horas: int, esperado: list[str]) -> None:
    item = _item("CMREP", status_operacional="AGUARDANDO_CONFIRMACAO_24H",
                 prazo_confirmacao_em=AGORA + timedelta(hours=delta_horas))
    assert [a["severidade"] for a in _tipos(_detectar(item), "PRAZO_24H_VENCIDO")] == esperado
