# tests/test_integracao_forms.py
"""Testes da integração Microsoft Forms → AGHUX (TASK-026 a TASK-032)."""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.auth.auth import auth_handler
from src.config import settings
from src.helpers.crypto_helper import decrypt_phi, encrypt_phi, mask_phi
from src.helpers.webhook_helper import calcular_assinatura
from src.main import app

SEGREDO = "segredo-webhook-de-teste"
FIXTURE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "mocks" / "dadosAghux.json"


@pytest.fixture
def integration_client(tmp_path, monkeypatch):
    """Isola o banco SQLite e fixa os segredos/provedores da integração."""
    monkeypatch.setenv("APP_DB_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setattr(settings, "FORMS_WEBHOOK_SECRET", SEGREDO)
    monkeypatch.setattr(settings, "FORMS_PROVIDER_TYPE", "MOCK")
    monkeypatch.setattr(settings, "AGHUX_PROVIDER_TYPE", "JSON")
    monkeypatch.setattr(settings, "AGHUX_FIXTURE_PATH", str(FIXTURE))
    monkeypatch.setattr(settings, "FORMS_FORM_ID", "")
    with TestClient(app) as cliente:
        yield cliente


def _headers(corpo: bytes, nonce: str, timestamp: str | None = None, assinatura: str | None = None):
    timestamp = timestamp or str(int(time.time()))
    assinatura = assinatura or calcular_assinatura(SEGREDO, timestamp, nonce, corpo)
    return {
        "Content-Type": "application/json",
        "X-SAE-Timestamp": timestamp,
        "X-SAE-Nonce": nonce,
        "X-SAE-Signature": assinatura,
    }


def _enviar(cliente, *, response_id, nonce, corpo_resposta=None, headers=None):
    payload = {
        "formId": "form-teste",
        "responseId": response_id,
        "submittedAt": "2026-11-25T12:34:56Z",
        "resposta": corpo_resposta or {
            "prontuario": "15004443",
            "nome": "MARIA B5586253 3A 0948 BB0DC",
            "telefone": "81988888888",
            "cidade": "Recife",
            "estado": "Pernambuco",
            "codigoExame": "CMDIP",
            "nomeExame": "CINTILOGRAFIA DO MIOCARDIO COM DIPIRIDAMOL",
            "cpf": "123.456.789-09",
        },
    }
    corpo = json.dumps(payload).encode("utf-8")
    return cliente.post(
        "/api/integracoes/forms/webhook",
        content=corpo,
        headers=headers or _headers(corpo, nonce),
    )


def _token_admin(cliente):
    resposta = cliente.post(
        "/api/login", data={"username": "admin", "password": "admin"}
    )
    assert resposta.status_code == 200
    return resposta.json()["access_token"]


def _eventos(cliente):
    resposta = cliente.get(
        "/api/integracoes/forms/eventos",
        headers={"Authorization": f"Bearer {_token_admin(cliente)}"},
    )
    assert resposta.status_code == 200
    return resposta.json()


def test_webhook_valido_cria_solicitacao_e_divergencia(integration_client):
    resposta = _enviar(integration_client, response_id="resp-001", nonce="nonce-001")
    assert resposta.status_code == 202
    assert resposta.json()["status"] == "ACEITO"

    eventos = _eventos(integration_client)
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["responseId"] == "resp-001"
    assert evento["status"] == "PROCESSADA"
    assert evento["solicitacaoId"]
    assert evento["divergencias"] == 1  # telefone diverges do AGHUX
    assert "cpf" not in json.dumps(evento)
    assert "123.456.789-09" not in json.dumps(evento)


def test_webhook_assinatura_invalida_e_rejeitado(integration_client):
    resposta = _enviar(
        integration_client,
        response_id="resp-002",
        nonce="nonce-002",
        headers={"X-SAE-Timestamp": str(int(time.time())), "X-SAE-Nonce": "nonce-002", "X-SAE-Signature": "sha256=errada"},
    )
    assert resposta.status_code == 401
    assert _eventos(integration_client) == []


def test_webhook_timestamp_fora_da_janela_e_rejeitado(integration_client):
    timestamp = str(int(time.time()) - 3600)
    corpo = json.dumps({"formId": "form-teste", "responseId": "resp-003"}).encode("utf-8")
    resposta = integration_client.post(
        "/api/integracoes/forms/webhook",
        content=corpo,
        headers=_headers(corpo, "nonce-003", timestamp=timestamp),
    )
    assert resposta.status_code == 401


def test_nonce_reutilizado_e_rejeitado(integration_client):
    primeira = _enviar(integration_client, response_id="resp-004", nonce="nonce-unico")
    assert primeira.status_code == 202
    segunda = _enviar(integration_client, response_id="resp-005", nonce="nonce-unico")
    assert segunda.status_code == 401
    assert len(_eventos(integration_client)) == 1


def test_response_id_duplicado_nao_cria_novo_evento(integration_client):
    assert _enviar(integration_client, response_id="resp-006", nonce="nonce-006").status_code == 202
    duplicado = _enviar(integration_client, response_id="resp-006", nonce="nonce-007")
    assert duplicado.status_code == 200
    assert duplicado.json()["status"] == "DUPLICADO"
    assert len(_eventos(integration_client)) == 1


def test_endpoint_administrativo_exige_token_e_rbac(integration_client):
    assert integration_client.get("/api/integracoes/forms/eventos").status_code == 401

    token_usuario = auth_handler.create_access_token(
        {"username": "operador", "groups": ["Users"]}
    )
    resposta = integration_client.get(
        "/api/integracoes/forms/eventos",
        headers={"Authorization": f"Bearer {token_usuario}"},
    )
    assert resposta.status_code == 403


def test_reprocessamento_nao_duplica_evento(integration_client):
    assert _enviar(integration_client, response_id="resp-008", nonce="nonce-008").status_code == 202
    token = _token_admin(integration_client)
    resposta = integration_client.post(
        "/api/integracoes/forms/eventos/resp-008/reprocessar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "PROCESSADA"
    assert len(_eventos(integration_client)) == 1


def test_evento_sem_correspondencia_no_aghux_gera_alerta(integration_client):
    resposta = _enviar(
        integration_client,
        response_id="resp-009",
        nonce="nonce-009",
        corpo_resposta={"prontuario": "00000000", "nome": "PACIENTE NAO CADASTRADO", "codigoExame": "RX"},
    )
    assert resposta.status_code == 202
    evento = _eventos(integration_client)[0]
    assert evento["status"] == "PROCESSADA"
    assert evento["alertas"] >= 1


def test_cripto_phi_nao_revela_valor_original():
    cifrado = encrypt_phi("123.456.789-09")
    assert cifrado and cifrado.startswith("v1:")
    assert "123.456.789-09" not in cifrado
    assert decrypt_phi(cifrado) == "123.456.789-09"
    assert mask_phi("123.456.789-09") == "***.8909"
