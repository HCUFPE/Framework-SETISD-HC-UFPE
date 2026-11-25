# tests/test_agendamentos.py
"""Testes da gestão de agendamentos (v0.3.0)."""

import json
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.auth.auth import auth_handler
from src.config import settings
from src.helpers.paciente_helper import paciente_chave
from src.helpers.webhook_helper import calcular_assinatura
from src.main import app

FIXTURE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "mocks" / "dadosAghux.json"
ADMIN = ["GLO-SEC-HCPE-SETISD", "Users"]
OPERADOR = ["OPERADOR"]
GESTOR = ["AREA_GESTORA"]
COORDENACAO = ["COORDENACAO"]


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    """Isola o SQLite, fixa o provider MOCK de distância e os segredos do webhook."""
    caminho = tmp_path / "app.db"
    monkeypatch.setenv("APP_DB_URL", f"sqlite+aiosqlite:///{caminho}")
    monkeypatch.setattr(settings, "DISTANCE_PROVIDER_TYPE", "MOCK")
    monkeypatch.setattr(settings, "MOCK_DISTANCE_KM", 12.5)
    monkeypatch.setattr(settings, "FORMS_PROVIDER_TYPE", "MOCK")
    monkeypatch.setattr(settings, "FORMS_WEBHOOK_SECRET", "segredo-teste-agenda")
    monkeypatch.setattr(settings, "FORMS_FORM_ID", "")
    monkeypatch.setattr(settings, "AGHUX_PROVIDER_TYPE", "JSON")
    monkeypatch.setattr(settings, "AGHUX_FIXTURE_PATH", str(FIXTURE))
    with TestClient(app) as test_client:
        yield test_client, caminho


def _headers(grupos):
    token = auth_handler.create_access_token(
        {"username": "usuario-teste", "groups": grupos}
    )
    return {"Authorization": f"Bearer {token}"}


def _agora():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(valor):
    return valor.isoformat()


def _conexao(caminho):
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    return conn


def _inserir_solicitacao(
    caminho,
    *,
    prontuario="15004443",
    nome="MARIA DA SILVA",
    protocolo=None,
    codigo="CMDIP",
    pontuacao=80,
    status="AGUARDANDO_CONTATO",
    aceite=True,
    divergencia=False,
    chave=None,
    cpf_hash=None,
):
    """Insere uma solicitação diretamente no SQLite isolado do teste."""
    sid = str(uuid.uuid4())
    chave = chave or paciente_chave(prontuario=prontuario)
    agora = _agora().replace(tzinfo=None).isoformat()
    protocolo = protocolo or f"PROTO-{sid[:8]}"
    prioridade = "ALTA" if pontuacao >= 70 else "MEDIA" if pontuacao >= 40 else "BAIXA"
    itens = json.dumps([{"codigoExame": codigo, "nomeExame": "CINTILOGRAFIA DO MIOCARDIO"}])
    with _conexao(caminho) as conn:
        conn.execute(
            """INSERT INTO solicitacoes
               (id, protocolo, prontuario, paciente_chave, paciente_nome, telefone,
                cidade, estado, cpf_hash, exame, itens_exame, tipo_exame,
                setor_solicitante, status, pontuacao, prioridade,
                recebida_em, criado_em, atualizado_em)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                protocolo,
                prontuario,
                chave,
                nome,
                "81988888888",
                "Recife",
                "PE",
                cpf_hash,
                "CINTILOGRAFIA DO MIOCARDIO",
                itens,
                "AMBULATORIAL",
                "CARDIOLOGIA",
                status,
                pontuacao,
                prioridade,
                agora,
                agora,
                agora,
            ),
        )
        if aceite:
            conn.execute(
                """INSERT INTO contatos_paciente
                   (id, solicitacao_id, canal, resultado, observacao, operador, realizado_em)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    sid,
                    "TELEFONE",
                    "ACEITE",
                    "Confirmou presença",
                    "operador",
                    agora,
                ),
            )
        if divergencia:
            conn.execute(
                """INSERT INTO divergencias
                   (solicitacao_id, campo, valor_formulario, valor_aghux, tratada, criado_em)
                   VALUES (?,?,?,?,0,?)""",
                (sid, "Telefone", "81988888888", "81977777777", agora),
            )
    return sid, chave


def _inserir_distancia(caminho, chave, km, fonte="MOCK"):
    with _conexao(caminho) as conn:
        conn.execute(
            """INSERT INTO paciente_enderecos
               (id, paciente_chave, cep_cripto, cidade, estado, distancia_km,
                distancia_fonte, calculado_em)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()),
                chave,
                "v1:hash-ficticio",
                "Recife",
                "PE",
                km,
                fonte,
                _agora().replace(tzinfo=None).isoformat(),
            ),
        )


def _criar_slot(cliente, *, minutos=60, duracao=30, capacidade=5, codigo="CMDIP", nome="Cintilografia", unidade="IMAGEM", situacao="DISPONIVEL"):
    inicio = (_agora() + timedelta(minutes=minutos)).replace(second=0, microsecond=0)
    fim = inicio + timedelta(minutes=duracao)
    resposta = cliente.post(
        "/api/admin/agenda/slots",
        json={
            "unidade": unidade,
            "codigoExame": codigo,
            "nomeExame": nome,
            "inicio": _iso(inicio),
            "fim": _iso(fim),
            "capacidade": capacidade,
            "situacao": situacao,
        },
        headers=_headers(ADMIN),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _agendar(cliente, solicitacao_id, slot_id, autor="operador"):
    return cliente.post(
        "/api/agendamentos",
        json={"solicitacaoId": solicitacao_id, "slotId": slot_id, "autor": autor},
        headers=_headers(OPERADOR),
    )


def _calendario(cliente, **params):
    base = {
        "de": _iso(_agora() - timedelta(days=1)),
        "ate": _iso(_agora() + timedelta(days=31)),
    }
    base.update(params)
    resposta = cliente.get("/api/agendamentos/calendario", params=base, headers=_headers(OPERADOR))
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def _slot_no_calendario(calendario, slot_id):
    return next(slot for slot in calendario["slots"] if slot["id"] == slot_id)


# ---------------------------------------------------------------------------
# Casos de teste
# ---------------------------------------------------------------------------

def test_criacao_listagem_e_atualizacao_de_slots(cliente):
    cliente, _ = cliente
    slot = _criar_slot(cliente, capacidade=4)
    assert set(slot) == {
        "id", "unidade", "codigoExame", "nomeExame", "inicio", "fim",
        "capacidade", "ocupadas", "livres", "status",
    }
    assert slot["ocupadas"] == 0 and slot["livres"] == 4
    assert slot["status"] == "DISPONIVEL"

    calendario = _calendario(cliente, unidade="IMAG", codigoExame="CMDIP")
    assert _slot_no_calendario(calendario, slot["id"])["capacidade"] == 4

    alterado = cliente.patch(
        f"/api/admin/agenda/slots/{slot['id']}",
        json={"capacidade": 2, "situacao": "ENCERRADO"},
        headers=_headers(GESTOR),
    )
    assert alterado.status_code == 200
    assert alterado.json()["capacidade"] == 2
    assert alterado.json()["status"] == "ENCERRADO"
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["status"] == "ENCERRADO"


def test_agendar_com_aceite_atualiza_calendario_e_historico(cliente):
    cliente, caminho = cliente
    sid, chave = _inserir_solicitacao(caminho)
    slot = _criar_slot(cliente)

    resposta = _agendar(cliente, sid, slot["id"])
    assert resposta.status_code == 201, resposta.text
    agendamento = resposta.json()
    assert set(agendamento) == {
        "id", "solicitacaoId", "protocolo", "pacienteChave", "pacienteNome",
        "prontuario", "unidade", "exame", "slotId", "dataHora", "status",
        "confirmadoPor", "criadoEm", "justificativa",
    }
    assert agendamento["status"] == "ATIVO"
    assert agendamento["pacienteChave"] == chave

    assert _slot_no_calendario(_calendario(cliente), slot["id"])["ocupadas"] == 1
    historico = cliente.get(f"/api/agendamentos/paciente/{chave}", headers=_headers(OPERADOR))
    assert historico.status_code == 200
    assert [item["status"] for item in historico.json()] == ["ATIVO"]

    with _conexao(caminho) as conn:
        auditoria = conn.execute(
            "SELECT categoria, acao, ip_origem FROM audit_logs WHERE acao='CRIAR_AGENDAMENTO'"
        ).fetchone()
    assert auditoria["categoria"] == "NEGOCIO_CLINICO"
    assert auditoria["ip_origem"]


def test_calendario_ocupadas_ignora_filtro_de_paciente(cliente):
    cliente, caminho = cliente
    sid_a, chave_a = _inserir_solicitacao(caminho, prontuario="10101010", protocolo="PROTO-E")
    sid_b, _ = _inserir_solicitacao(caminho, prontuario="20202020", protocolo="PROTO-F")
    slot = _criar_slot(cliente, capacidade=2)

    assert _agendar(cliente, sid_a, slot["id"]).status_code == 201
    assert _agendar(cliente, sid_b, slot["id"]).status_code == 201

    filtrado = _calendario(cliente, pacienteChave=chave_a)
    assert len(filtrado["agendamentos"]) == 1
    assert filtrado["agendamentos"][0]["pacienteChave"] == chave_a
    assert _slot_no_calendario(filtrado, slot["id"])["ocupadas"] == 2
    assert _slot_no_calendario(filtrado, slot["id"])["livres"] == 0


def test_agendar_sem_aceite_devolve_422(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, aceite=False)
    slot = _criar_slot(cliente)
    resposta = _agendar(cliente, sid, slot["id"])
    assert resposta.status_code == 422
    assert "ACEITE" in resposta.json()["detail"]


def test_vaga_esgotada_devolve_409(cliente):
    cliente, caminho = cliente
    sid_a, _ = _inserir_solicitacao(caminho, prontuario="11111111", protocolo="PROTO-A")
    sid_b, _ = _inserir_solicitacao(caminho, prontuario="22222222", protocolo="PROTO-B")
    slot = _criar_slot(cliente, capacidade=1)

    assert _agendar(cliente, sid_a, slot["id"]).status_code == 201
    conflito = _agendar(cliente, sid_b, slot["id"])
    assert conflito.status_code == 409
    assert "esgotada" in conflito.json()["detail"].lower()
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["ocupadas"] == 1


def test_conflito_mesmo_paciente_devolve_409(cliente):
    cliente, caminho = cliente
    sid_a, chave = _inserir_solicitacao(caminho, prontuario="33333333", protocolo="PROTO-C")
    sid_b, _ = _inserir_solicitacao(
        caminho, prontuario="33333333", protocolo="PROTO-D", chave=chave
    )
    slot_a = _criar_slot(cliente, minutos=60, duracao=30)
    slot_b = _criar_slot(cliente, minutos=75, duracao=30)

    assert _agendar(cliente, sid_a, slot_a["id"]).status_code == 201
    conflito = _agendar(cliente, sid_b, slot_b["id"])
    assert conflito.status_code == 409
    assert "paciente" in conflito.json()["detail"].lower()


def test_remarcacao_devolve_vaga_antiga_na_mesma_transacao(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho)
    slot_a = _criar_slot(cliente, minutos=60)
    slot_b = _criar_slot(cliente, minutos=180)

    criado = _agendar(cliente, sid, slot_a["id"]).json()
    assert _slot_no_calendario(_calendario(cliente), slot_a["id"])["ocupadas"] == 1

    resposta = cliente.post(
        f"/api/agendamentos/{criado['id']}/remarcar",
        json={"slotId": slot_b["id"], "justificativa": "Conflito de agenda do paciente", "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["slotId"] == slot_b["id"]

    calendario = _calendario(cliente)
    assert _slot_no_calendario(calendario, slot_a["id"])["ocupadas"] == 0
    assert _slot_no_calendario(calendario, slot_b["id"])["ocupadas"] == 1

    with _conexao(caminho) as conn:
        linha = conn.execute(
            "SELECT categoria, dados_anteriores, dados_novos, ip_origem FROM audit_logs "
            "WHERE acao='REMARCAR_AGENDAMENTO'"
        ).fetchone()
    assert linha["categoria"] == "NEGOCIO_CLINICO"
    assert slot_a["id"] in linha["dados_anteriores"]
    assert slot_b["id"] in linha["dados_novos"]
    assert linha["ip_origem"]


def test_remarcacao_sem_justificativa_e_422(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho)
    slot_a = _criar_slot(cliente, minutos=60)
    slot_b = _criar_slot(cliente, minutos=180)
    criado = _agendar(cliente, sid, slot_a["id"]).json()

    resposta = cliente.post(
        f"/api/agendamentos/{criado['id']}/remarcar",
        json={"slotId": slot_b["id"], "justificativa": "   ", "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 422


def test_cancelamento_devolve_vaga_e_audita(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho)
    slot = _criar_slot(cliente)
    criado = _agendar(cliente, sid, slot["id"]).json()

    resposta = cliente.post(
        f"/api/agendamentos/{criado['id']}/cancelar",
        json={"justificativa": "Paciente solicitou cancelamento", "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "CANCELADO"
    assert resposta.json()["justificativa"] == "Paciente solicitou cancelamento"
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["ocupadas"] == 0

    with _conexao(caminho) as conn:
        linha = conn.execute(
            "SELECT categoria, dados_anteriores, dados_novos, ip_origem FROM audit_logs "
            "WHERE acao='CANCELAR_AGENDAMENTO'"
        ).fetchone()
    assert linha["categoria"] == "NEGOCIO_CLINICO"
    assert '"ATIVO"' in linha["dados_anteriores"]
    assert '"CANCELADO"' in linha["dados_novos"]
    assert linha["ip_origem"]


def test_sugestoes_ordenadas_por_prioridade_e_distancia(cliente):
    cliente, caminho = cliente
    sid_alta, chave_alta = _inserir_solicitacao(
        caminho, prontuario="44444444", pontuacao=90, protocolo="PROTO-ALTA"
    )
    sid_baixa, chave_baixa = _inserir_solicitacao(
        caminho, prontuario="55555555", pontuacao=40, protocolo="PROTO-BAIXA"
    )
    _inserir_distancia(caminho, chave_alta, 5.0)
    _inserir_distancia(caminho, chave_baixa, 45.0)
    perto = _criar_slot(cliente, minutos=60)
    longe = _criar_slot(cliente, minutos=60 * 24 * 5)

    sugestoes = cliente.get(
        f"/api/agendamentos/sugestoes/{sid_alta}", headers=_headers(OPERADOR)
    )
    assert sugestoes.status_code == 200
    dados = sugestoes.json()
    assert len(dados) == 2
    assert dados[0]["slot"]["id"] == perto["id"]
    assert dados[0]["pontuacao"] >= dados[1]["pontuacao"]
    assert dados[0]["distanciaKm"] == 5.0
    assert dados[0]["distanciaOrigem"] == "MOCK"
    assert any("distância" in motivo.lower() for motivo in dados[0]["motivos"])

    sugestoes_baixa = cliente.get(
        f"/api/agendamentos/sugestoes/{sid_baixa}", headers=_headers(OPERADOR)
    ).json()
    assert sugestoes_baixa[0]["pontuacao"] < dados[0]["pontuacao"]


def test_busca_de_paciente_sem_phi(cliente):
    cliente, caminho = cliente
    sid, chave = _inserir_solicitacao(
        caminho,
        prontuario="66666666",
        nome="ANA BEATRIZ",
        protocolo="PROTO-666",
        cpf_hash="hash-ficticio",
    )
    for termo in ("66666666", "ANA BEATRIZ", "PROTO-666"):
        resposta = cliente.get(
            "/api/agendamentos/pacientes/buscar",
            params={"q": termo},
            headers=_headers(OPERADOR),
        )
        assert resposta.status_code == 200
        resultados = resposta.json()
        assert len(resultados) == 1
        assert set(resultados[0]) == {
            "pacienteChave", "pacienteNome", "prontuario", "agendamentosAtivos",
        }
        assert resultados[0]["pacienteChave"] == chave
        corpo = json.dumps(resultados).lower()
        assert "hash-ficticio" not in corpo
        assert "cpf" not in corpo
    assert sid


def test_rbac_401_e_403_inclusive_coordenacao_somente_leitura(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho)
    slot = _criar_slot(cliente)

    assert cliente.get("/api/agendamentos/calendario").status_code == 401
    assert cliente.post("/api/agendamentos", json={}).status_code == 401
    assert cliente.get(
        "/api/agendamentos/calendario", headers=_headers(["Users"])
    ).status_code == 403
    assert cliente.get(
        "/api/admin/agenda/slots", headers=_headers(OPERADOR)
    ).status_code == 403

    assert cliente.get(
        "/api/agendamentos/calendario", headers=_headers(COORDENACAO)
    ).status_code == 200
    negado = cliente.post(
        "/api/agendamentos",
        json={"solicitacaoId": sid, "slotId": slot["id"], "autor": "coordenacao"},
        headers=_headers(COORDENACAO),
    )
    assert negado.status_code == 403

    with_token_admin = cliente.get(
        "/api/admin/agenda/slots", headers=_headers(ADMIN)
    )
    assert with_token_admin.status_code == 200


def test_endereco_criptografado_e_ausente_em_respostas_e_auditoria(cliente):
    cliente, caminho = cliente
    corpo = json.dumps(
        {
            "formId": "form-agenda",
            "responseId": "resp-agenda-001",
            "submittedAt": "2026-11-25T12:00:00Z",
            "resposta": {
                "prontuario": "77777777",
                "nome": "PACIENTE COM ENDERECO",
                "cep": "12345-678",
                "logradouro": "Rua das Palmeiras",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "Recife",
                "estado": "PE",
                "cpf": "123.456.789-09",
                "codigoExame": "CMDIP",
            },
        }
    ).encode("utf-8")
    timestamp = str(int(time.time()))
    nonce = "nonce-agenda-001"
    headers = {
        "Content-Type": "application/json",
        "X-SAE-Timestamp": timestamp,
        "X-SAE-Nonce": nonce,
        "X-SAE-Signature": calcular_assinatura(
            "segredo-teste-agenda", timestamp, nonce, corpo
        ),
    }
    envio = cliente.post("/api/integracoes/forms/webhook", content=corpo, headers=headers)
    assert envio.status_code == 202, envio.text

    with _conexao(caminho) as conn:
        solicitacao = conn.execute(
            "SELECT id, paciente_chave FROM solicitacoes WHERE prontuario='77777777'"
        ).fetchone()
        endereco = conn.execute(
            "SELECT * FROM paciente_enderecos WHERE paciente_chave=?",
            (solicitacao["paciente_chave"],),
        ).fetchone()
        auditorias = conn.execute(
            "SELECT acao, dados_novos FROM audit_logs WHERE acao='IMPORTAR_RESPOSTA_FORMS'"
        ).fetchall()

    assert solicitacao is not None
    assert len(solicitacao["paciente_chave"]) == 64
    assert endereco is not None
    assert endereco["cep_cripto"].startswith("v1:")
    assert endereco["logradouro_cripto"].startswith("v1:")
    assert endereco["distancia_km"] == 12.5
    assert endereco["distancia_fonte"] == "MOCK"
    assert "12345-678" not in json.dumps(dict(endereco))
    assert "Rua das Palmeiras" not in json.dumps(dict(endereco))
    assert auditorias
    dados_auditoria = json.loads(auditorias[0]["dados_novos"])
    assert dados_auditoria["enderecoInformado"] is True
    assert "12345-678" not in auditorias[0]["dados_novos"]
    assert "Rua das Palmeiras" not in auditorias[0]["dados_novos"]

    busca = cliente.get(
        "/api/agendamentos/pacientes/buscar",
        params={"q": "77777777"},
        headers=_headers(OPERADOR),
    ).json()
    assert "123.456.789-09" not in json.dumps(busca)
    assert "Rua das Palmeiras" not in json.dumps(busca)


def test_validacao_de_divergencias_e_registro_de_contato(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(
        caminho, prontuario="88888888", status="RECEBIDA", divergencia=True
    )
    slot = _criar_slot(cliente)

    contato_prematuro = cliente.post(
        f"/api/solicitacoes/{sid}/contatos",
        json={"canal": "TELEFONE", "resultado": "ACEITE", "operador": "operador"},
        headers=_headers(OPERADOR),
    )
    assert contato_prematuro.status_code == 422

    with _conexao(caminho) as conn:
        divergencia_id = conn.execute(
            "SELECT id FROM divergencias WHERE solicitacao_id=?", (sid,)
        ).fetchone()["id"]

    validacao = cliente.post(
        f"/api/solicitacoes/{sid}/validacao",
        json={"justificativas": {str(divergencia_id): "Telefone conferido com o paciente"}},
        headers=_headers(OPERADOR),
    )
    assert validacao.status_code == 200
    assert validacao.json()["status"] == "AGUARDANDO_CONTATO"
    assert validacao.json()["divergenciasTratadas"] == 1

    contato = cliente.post(
        f"/api/solicitacoes/{sid}/contatos",
        json={
            "canal": "TELEFONE",
            "resultado": "ACEITE",
            "observacao": "Confirmou o horário",
            "operador": "operador",
        },
        headers=_headers(OPERADOR),
    )
    assert contato.status_code == 201
    assert contato.json()["resultado"] == "ACEITE"
    assert _agendar(cliente, sid, slot["id"]).status_code == 201

    with _conexao(caminho) as conn:
        acoes = {
            linha["acao"]
            for linha in conn.execute("SELECT acao FROM audit_logs").fetchall()
        }
    assert {"VALIDAR_DIVERGENCIAS", "REGISTRAR_CONTATO_PACIENTE", "CRIAR_AGENDAMENTO"} <= acoes


@pytest.mark.asyncio
async def test_falha_transitoria_do_osm_nao_fica_em_cache(monkeypatch):
    """Uma queda de rede não pode manter a distância indisponível por dias."""
    from src.providers.implementations.distance_provider import (
        _CACHE,
        OpenStreetMapDistanceProvider,
    )

    _CACHE.clear()
    provedor = OpenStreetMapDistanceProvider()
    tentativas = {"total": 0}

    async def consultar(endereco):
        tentativas["total"] += 1
        if tentativas["total"] == 1:
            raise ConnectionError("rede indisponível")
        return -8.05, -34.88, 15.0

    monkeypatch.setattr(provedor, "_consultar", consultar)
    endereco = {"logradouro": "Rua de Teste", "cidade": "Recife", "estado": "PE"}

    primeiro = await provedor.calcular(endereco)
    assert primeiro.fonte == "INDISPONIVEL"
    assert primeiro.distancia_km is None

    segundo = await provedor.calcular(endereco)
    assert tentativas["total"] == 2
    assert segundo.fonte == "OSM"
    assert segundo.distancia_km == 15.0
