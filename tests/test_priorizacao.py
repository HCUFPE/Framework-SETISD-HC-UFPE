"""
Testes do Motor Determinístico de Priorização Clínica (TASK-008)
================================================================
Cobre os critérios de avaliação do CARE-RF005 / CARE-UC003:
(1) Oncologia supera rotina mesmo com solicitação mais recente;
(2) alterar um peso no banco altera a ordenação na próxima leitura;
(3) filtro geográfico não altera o score clínico.
"""

from datetime import date, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.controllers.priorizacao_controller import (
    FiltrosFila,
    calcular_prioridade,
    filtrar_fila,
    indexar_regras_exames,
    normalizar_texto,
    priorizar_fila,
    regra_grupo_casa,
)
from src.models import RegraPrioridade
from src.resources.database import Base
from src.resources.seed_exames import REGRAS_EXAMES_INICIAIS, REGRAS_PRIORIDADE_INICIAIS

HOJE = date(2026, 11, 26)


def _regras() -> list[dict[str, Any]]:
    """Regras de prioridade do seed inicial, como dicts ativos."""
    return [dict(r, deleted_at=None) for r in REGRAS_PRIORIDADE_INICIAIS]


def _regras_exames() -> dict[str, Any]:
    """Regras de exame do seed inicial indexadas por código."""
    return indexar_regras_exames(dict(r, deleted_at=None) for r in REGRAS_EXAMES_INICIAIS)


def _item(id_: int, **campos: Any) -> dict[str, Any]:
    """Cria um item de fila mínimo com valores padrão."""
    base: dict[str, Any] = {
        "id": id_,
        "codigo_solicitacao": f"SOL{id_}",
        "codigo_exame": "USAX",
        "prontuario": f"P{id_}",
        "nome_paciente": f"PACIENTE {id_}",
        "especialidade_solicitante": None,
        "unidade_solicitante": "AMBULATORIO GERAL",
        "grupo_prioritario_manual": None,
        "flag_hemodialise": False,
        "data_retorno_medico": None,
        "data_solicitacao": datetime(2026, 11, 1, 8, 0),
        "municipio": "RECIFE",
        "regiao_geografica": "CAPITAL",
        "utiliza_tfd": False,
        "status_operacional": "NA_FILA",
        "status_higienizacao": "VALIDA",
    }
    base.update(campos)
    return base


# ---------------------------------------------------------------------------
# 1. Normalização e casamento de regras
# ---------------------------------------------------------------------------


def test_normalizar_texto_remove_acento_e_maiusculas() -> None:
    assert normalizar_texto("Oncologia Clínica") == "ONCOLOGIA CLINICA"
    assert normalizar_texto("  hemodiálise  ") == "HEMODIALISE"
    assert normalizar_texto(None) == ""


@pytest.mark.parametrize(
    "campos",
    [
        {"especialidade_solicitante": "Oncologia Clínica"},
        {"unidade_solicitante": "ONCOLOGIA CLINICA"},
        {"grupo_prioritario_manual": "oncologia"},
    ],
)
def test_regra_clinica_casa_por_especialidade_unidade_ou_grupo(campos: dict[str, Any]) -> None:
    regra = {"tipo_criterio": "CLINICA", "valor_match": "ONCOLOGIA"}
    assert regra_grupo_casa(regra, _item(1, **campos))


def test_regra_hemodialise_casa_pela_flag() -> None:
    regra = {"tipo_criterio": "GRUPO_CLINICO", "valor_match": "HEMODIALISE"}
    assert regra_grupo_casa(regra, _item(1, flag_hemodialise=True))
    assert not regra_grupo_casa(regra, _item(2))


def test_regra_vulneravel_casa_por_qualquer_termo() -> None:
    regra = {"tipo_criterio": "VULNERAVEL", "valor_match": "CRIANCA,PEDIATRIA"}
    assert regra_grupo_casa(regra, _item(1, unidade_solicitante="PEDIATRIA GERAL"))


@pytest.mark.parametrize("alteracao", [{"ativo": False}, {"deleted_at": datetime(2026, 11, 1)}])
def test_regra_inativa_ou_excluida_nao_pontua(alteracao: dict[str, Any]) -> None:
    regras = [
        dict(r, **alteracao) if r["codigo"] == "CLINICA_ONCOLOGIA" else r for r in _regras()
    ]
    score, motivos = calcular_prioridade(
        _item(1, unidade_solicitante="ONCOLOGIA CLINICA"), regras, {}, HOJE
    )
    assert not any(m.startswith("Oncologia") for m in motivos)
    assert score == 10  # cai para rotina


# ---------------------------------------------------------------------------
# 2. Score e motivos
# ---------------------------------------------------------------------------


def test_grupos_clinicos_nao_se_somam() -> None:
    item = _item(1, unidade_solicitante="NEFROLOGIA", flag_hemodialise=True)
    score, motivos = calcular_prioridade(item, _regras(), {}, HOJE)
    assert score == 75
    assert motivos == ["Hemodiálise +75"]


def test_item_sem_grupo_recebe_rotina() -> None:
    score, motivos = calcular_prioridade(_item(1), _regras(), {}, HOJE)
    assert score == 10
    assert motivos == ["Rotina Ambulatorial +10"]


@pytest.mark.parametrize(
    ("dias", "recebe_bonus"),
    [(10, True), (15, True), (0, True), (30, False), (-1, False), (None, False)],
)
def test_bonus_retorno_proximo(dias: int | None, recebe_bonus: bool) -> None:
    retorno = HOJE + timedelta(days=dias) if dias is not None else None
    score, motivos = calcular_prioridade(_item(1, data_retorno_medico=retorno), _regras(), {}, HOJE)
    assert ("Retorno médico em até 15 dias +20" in motivos) is recebe_bonus
    assert score == (30 if recebe_bonus else 10)


def test_retorno_com_valor_match_invalido_e_ignorado() -> None:
    regras = [
        dict(r, valor_match="quinze") if r["tipo_criterio"] == "RETORNO_PROXIMO" else r
        for r in _regras()
    ]
    score, _ = calcular_prioridade(
        _item(1, data_retorno_medico=HOJE + timedelta(days=3)), regras, {}, HOJE
    )
    assert score == 10


def test_bonus_afinidade_gastroenterologia_colonoscopia() -> None:
    item = _item(1, codigo_exame="COLONO", unidade_solicitante="GASTROENTEROLOGIA")
    score, motivos = calcular_prioridade(item, _regras(), _regras_exames(), HOJE)
    assert "Afinidade Clínica Solicitante × Exame +15" in motivos
    assert score == 25


def test_sem_regra_de_exame_nao_ha_afinidade() -> None:
    item = _item(1, codigo_exame="COLONO", unidade_solicitante="GASTROENTEROLOGIA")
    score, motivos = calcular_prioridade(item, _regras(), {}, HOJE)
    assert score == 10
    assert len(motivos) == 1


def test_motivos_somam_o_score_e_seguem_a_ordem() -> None:
    item = _item(1, unidade_solicitante="ONCOLOGIA CLINICA", data_retorno_medico=HOJE + timedelta(days=5))
    score, motivos = calcular_prioridade(item, _regras(), _regras_exames(), HOJE)
    assert motivos == ["Oncologia +100", "Retorno médico em até 15 dias +20"]
    assert score == 120
    assert sum(int(m.rsplit("+", 1)[1]) for m in motivos) == score


# ---------------------------------------------------------------------------
# 3. Ordenação e filtros
# ---------------------------------------------------------------------------


def test_oncologia_supera_rotina_mesmo_mais_recente() -> None:
    rotina = _item(1, data_solicitacao=datetime(2026, 11, 1))
    onco = _item(2, unidade_solicitante="ONCOLOGIA CLINICA", data_solicitacao=datetime(2026, 11, 20))
    fila = priorizar_fila([rotina, onco], _regras(), {}, HOJE)
    assert [i["id"] for i in fila] == [2, 1]


def test_desempate_pela_data_de_solicitacao_e_id() -> None:
    a = _item(1, data_solicitacao=datetime(2026, 11, 10))
    b = _item(2, data_solicitacao=datetime(2026, 11, 5))
    c = _item(3, data_solicitacao=None)
    d = _item(4, data_solicitacao=datetime(2026, 11, 5))
    fila = priorizar_fila([a, b, c, d], _regras(), {}, HOJE)
    assert [i["id"] for i in fila] == [2, 4, 1, 3]


def test_execucoes_repetidas_produzem_mesma_ordem() -> None:
    itens = [
        _item(1),
        _item(2, unidade_solicitante="TRANSPLANTE RENAL"),
        _item(3, unidade_solicitante="PEDIATRIA"),
        _item(4, unidade_solicitante="ONCOLOGIA CLINICA", data_retorno_medico=HOJE),
    ]
    primeira = priorizar_fila(itens, _regras(), _regras_exames(), HOJE)
    segunda = priorizar_fila(list(reversed(itens)), _regras(), _regras_exames(), HOJE)
    assert primeira == segunda
    assert [i["id"] for i in primeira] == [4, 2, 3, 1]


def test_peso_alterado_no_banco_inverte_a_ordem() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            session.add_all(RegraPrioridade(**r) for r in REGRAS_PRIORIDADE_INICIAIS)
            session.commit()

            def ler_regras() -> list[dict[str, Any]]:
                return [
                    {c: getattr(r, c) for c in ("codigo", "nome", "tipo_criterio", "valor_match", "peso", "ativo", "deleted_at")}
                    for r in session.scalars(select(RegraPrioridade))
                ]

            itens = [_item(1), _item(2, unidade_solicitante="ONCOLOGIA CLINICA")]
            assert [i["id"] for i in priorizar_fila(itens, ler_regras(), {}, HOJE)] == [2, 1]

            rotina = session.scalars(
                select(RegraPrioridade).where(RegraPrioridade.codigo == "GRUPO_ROTINA")
            ).one()
            rotina.peso = 150
            session.commit()

            assert [i["id"] for i in priorizar_fila(itens, ler_regras(), {}, HOJE)] == [1, 2]
    finally:
        engine.dispose()


def _fila_mista() -> list[dict[str, Any]]:
    itens = [
        _item(1, municipio="RECIFE", regiao_geografica="CAPITAL"),
        _item(2, unidade_solicitante="ONCOLOGIA CLINICA", municipio="PESQUEIRA", regiao_geografica="INTERIOR", utiliza_tfd=True),
        _item(3, unidade_solicitante="TRANSPLANTE RENAL", municipio="RECIFE", regiao_geografica="CAPITAL"),
        _item(4, unidade_solicitante="PEDIATRIA", municipio="OLINDA", regiao_geografica="RMR"),
        _item(5, unidade_solicitante="NEFROLOGIA", municipio="Recife", regiao_geografica="CAPITAL", data_retorno_medico=HOJE),
    ]
    return priorizar_fila(itens, _regras(), _regras_exames(), HOJE)


def test_filtro_por_regiao_preserva_score_motivos_e_ordem() -> None:
    completa = _fila_mista()
    filtrada = filtrar_fila(completa, FiltrosFila(regiao="CAPITAL"))
    por_id = {i["id"]: i for i in completa}
    assert [i["id"] for i in filtrada] == [i["id"] for i in completa if i["regiao_geografica"] == "CAPITAL"]
    for item in filtrada:
        assert item["score_prioridade"] == por_id[item["id"]]["score_prioridade"]
        assert item["motivos_prioridade"] == por_id[item["id"]]["motivos_prioridade"]


def test_filtro_tfd() -> None:
    assert [i["id"] for i in filtrar_fila(_fila_mista(), FiltrosFila(apenas_tfd=True))] == [2]


def test_filtro_municipio_ignora_acento_e_caixa() -> None:
    ids = {i["id"] for i in filtrar_fila(_fila_mista(), FiltrosFila(municipio="recife"))}
    assert ids == {1, 3, 5}


def test_busca_por_prontuario_solicitacao_e_nome() -> None:
    fila = _fila_mista()
    assert [i["id"] for i in filtrar_fila(fila, FiltrosFila(busca="P3"))] == [3]
    assert [i["id"] for i in filtrar_fila(fila, FiltrosFila(busca="SOL4"))] == [4]
    assert [i["id"] for i in filtrar_fila(fila, FiltrosFila(busca="paciente 5"))] == [5]


def test_filtros_combinados_exame_unidade_status() -> None:
    fila = _fila_mista()
    filtros = FiltrosFila(codigo_exame="usax", unidade="transplante", status_operacional="NA_FILA", status_higienizacao="VALIDA")
    assert [i["id"] for i in filtrar_fila(fila, filtros)] == [3]
