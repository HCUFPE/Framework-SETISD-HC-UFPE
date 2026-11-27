"""
Testes da Máquina de Estados da Confirmação em 24h e Auditoria (TASK-010 / CARE-RF008)
=====================================================================================
"""

from datetime import datetime, timedelta, timezone

import pytest

from tests.fila_fixtures import FilaApi, fila_api  # noqa: F401 - fixture


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _patch(api: FilaApi, item_id: int, **corpo: object):
    return api.client.patch(f"/api/exames/fila/{item_id}/status", json=corpo, headers=api.headers)


def _dt(valor: str) -> datetime:
    return datetime.fromisoformat(valor).replace(tzinfo=None)


def test_iniciar_aguardo_calcula_prazo_exato_de_24h_e_audita(fila_api: FilaApi) -> None:
    item = fila_api.inserir(codigo_solicitacao="900010", codigo_exame="USAX", prontuario="2002")
    antes = _agora()
    resposta = _patch(fila_api, item, statusOperacional="AGUARDANDO_CONFIRMACAO_24H")
    depois = _agora()

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    contato = _dt(corpo["contatoIniciadoEm"])
    prazo = _dt(corpo["prazoConfirmacaoEm"])
    assert corpo["statusOperacional"] == "AGUARDANDO_CONFIRMACAO_24H"
    assert antes <= contato <= depois
    assert prazo - contato == timedelta(hours=24)

    logs = fila_api.audit_logs()
    assert len(logs) == 1
    log = logs[0]
    assert log["usuario"] == "admin"
    assert log["categoria"] == "NEGOCIO_CLINICO"
    assert log["acao"] == "ALTERAR_STATUS_FILA"
    assert log["recurso"] == f"acompanhamento_fila:{item}"
    assert log["ip_origem"]
    assert log["dados_anteriores"] == {
        "status_operacional": "NA_FILA",
        "contato_iniciado_em": None,
        "prazo_confirmacao_em": None,
    }
    assert log["dados_novos"]["status_operacional"] == "AGUARDANDO_CONFIRMACAO_24H"
    assert log["dados_novos"]["prazo_confirmacao_em"] is not None


def test_confirmar_agendamento_com_data_e_preparo(fila_api: FilaApi) -> None:
    item = fila_api.inserir(status_operacional="AGUARDANDO_CONFIRMACAO_24H",
                            contato_iniciado_em=_agora(), prazo_confirmacao_em=_agora() + timedelta(hours=24))
    resposta = _patch(fila_api, item, statusOperacional="CONFIRMADO_AGENDADO_AGHU",
                      dataAgendadaAghu="2026-12-10T08:30:00-03:00", preparoOrientado=True,
                      observacoes="Preparo enviado por WhatsApp")
    assert resposta.status_code == 200, resposta.text
    salvo = fila_api.item(item)
    assert salvo.status_operacional == "CONFIRMADO_AGENDADO_AGHU"
    assert salvo.data_agendada_aghu == datetime(2026, 12, 10, 11, 30)  # convertido para UTC
    assert salvo.preparo_orientado is True
    assert salvo.observacoes == "Preparo enviado por WhatsApp"


def test_confirmar_sem_data_retorna_400_sem_alterar_nem_auditar(fila_api: FilaApi) -> None:
    item = fila_api.inserir(status_operacional="AGUARDANDO_CONFIRMACAO_24H")
    resposta = _patch(fila_api, item, statusOperacional="CONFIRMADO_AGENDADO_AGHU")
    assert resposta.status_code == 400
    assert "data" in resposta.json()["detail"].lower()
    assert fila_api.item(item).status_operacional == "AGUARDANDO_CONFIRMACAO_24H"
    assert fila_api.audit_logs() == []


@pytest.mark.parametrize(
    ("atual", "novo"),
    [
        ("NA_FILA", "CONFIRMADO_AGENDADO_AGHU"),
        ("NA_FILA", "SEM_RESPOSTA_24H"),
        ("CONFIRMADO_AGENDADO_AGHU", "NA_FILA"),
        ("CANCELADO", "NA_FILA"),
        ("SEM_RESPOSTA_24H", "CONFIRMADO_AGENDADO_AGHU"),
    ],
)
def test_transicoes_invalidas_retornam_400(fila_api: FilaApi, atual: str, novo: str) -> None:
    item = fila_api.inserir(status_operacional=atual)
    resposta = _patch(fila_api, item, statusOperacional=novo, dataAgendadaAghu="2026-12-10T08:00:00")
    assert resposta.status_code == 400
    assert "não permitida" in resposta.json()["detail"]
    assert fila_api.item(item).status_operacional == atual
    assert fila_api.audit_logs() == []


def test_sem_resposta_e_retorno_a_fila_limpa_prazos(fila_api: FilaApi) -> None:
    agora = _agora()
    item = fila_api.inserir(status_operacional="AGUARDANDO_CONFIRMACAO_24H",
                            contato_iniciado_em=agora - timedelta(hours=30),
                            prazo_confirmacao_em=agora - timedelta(hours=6))
    assert _patch(fila_api, item, statusOperacional="SEM_RESPOSTA_24H").status_code == 200
    resposta = _patch(fila_api, item, statusOperacional="NA_FILA")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["statusOperacional"] == "NA_FILA"
    assert corpo["contatoIniciadoEm"] is None and corpo["prazoConfirmacaoEm"] is None
    assert [log["dados_novos"]["status_operacional"] for log in fila_api.audit_logs()] == [
        "SEM_RESPOSTA_24H", "NA_FILA",
    ]


def test_cancelar_a_partir_da_fila(fila_api: FilaApi) -> None:
    item = fila_api.inserir()
    assert _patch(fila_api, item, statusOperacional="CANCELADO").status_code == 200
    assert fila_api.item(item).status_operacional == "CANCELADO"


def test_item_nao_valido_nao_muda_status(fila_api: FilaApi) -> None:
    item = fila_api.inserir(status_higienizacao="DUPLICADA")
    resposta = _patch(fila_api, item, statusOperacional="AGUARDANDO_CONFIRMACAO_24H")
    assert resposta.status_code == 400
    assert fila_api.audit_logs() == []


def test_status_de_item_inexistente_retorna_404(fila_api: FilaApi) -> None:
    assert _patch(fila_api, 99999, statusOperacional="CANCELADO").status_code == 404


def test_status_desconhecido_retorna_400(fila_api: FilaApi) -> None:
    item = fila_api.inserir()
    assert _patch(fila_api, item, statusOperacional="AGENDADO").status_code == 400


def test_prazo_vencido_gera_alerta_na_fila(fila_api: FilaApi) -> None:
    agora = _agora()
    item = fila_api.inserir(status_operacional="AGUARDANDO_CONFIRMACAO_24H",
                            contato_iniciado_em=agora - timedelta(hours=25),
                            prazo_confirmacao_em=agora - timedelta(minutes=5))
    corpo = {i["id"]: i for i in fila_api.client.get("/api/exames/fila", headers=fila_api.headers).json()}
    alertas = corpo[item]["alertas"]
    assert {"tipo": "PRAZO_24H_VENCIDO", "severidade": "ALTA"}.items() <= alertas[0].items()
