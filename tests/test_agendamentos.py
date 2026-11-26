# tests/test_agendamentos.py
"""Testes da gestão de agendamentos (v0.7.0)."""

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
CHEFIA = ["CHEFIA"]
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


def _gerar_proposta(cliente):
    """Executa a simulação e devolve a proposta pendente criada."""
    resposta = cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 201, resposta.text
    return cliente.get(
        "/api/agendamentos/calendario",
        params={"de": _iso(_agora() - timedelta(days=1)),
                "ate": _iso(_agora() + timedelta(days=31))},
        headers=_headers(OPERADOR),
    ).json()["agendamentos"][0]


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


def _agendar_da_fila(cliente, sid, slot_id, grupos=OPERADOR):
    return cliente.post(
        f"/api/solicitacoes/{sid}/agendar",
        json={"slotId": slot_id, "autor": "operador"},
        headers=_headers(grupos),
    )


def test_agendar_da_fila_solicitacao_recebida_sem_aceite(cliente):
    """RN-07: a vaga é marcada antes do contato, então RECEBIDA agenda sem aceite prévio."""
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, status="RECEBIDA", aceite=False)
    slot = _criar_slot(cliente)

    resposta = _agendar_da_fila(cliente, sid, slot["id"])
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status"] == "ATIVO"
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["ocupadas"] == 1
    with _conexao(caminho) as conn:
        solicitacao = conn.execute("SELECT status FROM solicitacoes WHERE id=?", (sid,)).fetchone()
        auditoria = conn.execute(
            "SELECT categoria FROM audit_logs WHERE acao='AGENDAR_DA_FILA'"
        ).fetchone()
    assert solicitacao["status"] == "AGUARDANDO_CONTATO"
    assert auditoria["categoria"] == "NEGOCIO_CLINICO"


def test_agendar_da_fila_com_divergencia_pendente_devolve_422(cliente):
    """RN-04 continua valendo na fila: divergência pendente bloqueia o agendamento."""
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, status="RECEBIDA", aceite=False, divergencia=True)
    slot = _criar_slot(cliente)

    resposta = _agendar_da_fila(cliente, sid, slot["id"])
    assert resposta.status_code == 422
    assert "divergências" in resposta.json()["detail"]
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["ocupadas"] == 0


def test_agendar_da_fila_exige_solicitacao_recebida(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, status="AGUARDANDO_CONTATO")
    slot = _criar_slot(cliente)

    resposta = _agendar_da_fila(cliente, sid, slot["id"])
    assert resposta.status_code == 422
    assert "recebidas" in resposta.json()["detail"]


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


def _status_solicitacao(caminho, sid):
    with _conexao(caminho) as conn:
        return conn.execute(
            "SELECT status FROM solicitacoes WHERE id=?", (sid,)
        ).fetchone()["status"]


def test_contato_aceite_e_recusa_atualizam_novos_status(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(
        caminho, prontuario="88888881", status="RECEBIDA", divergencia=True, aceite=False
    )
    with _conexao(caminho) as conn:
        divergencia_id = conn.execute(
            "SELECT id FROM divergencias WHERE solicitacao_id=?", (sid,)
        ).fetchone()["id"]
    validacao = cliente.post(
        f"/api/solicitacoes/{sid}/validacao",
        json={"justificativas": {str(divergencia_id): "Telefone validado"}},
        headers=_headers(OPERADOR),
    )
    assert validacao.status_code == 200

    aceite = cliente.post(
        f"/api/solicitacoes/{sid}/contatos",
        json={"canal": "TELEFONE", "resultado": "ACEITE", "operador": "operador"},
        headers=_headers(OPERADOR),
    )
    assert aceite.status_code == 201
    assert _status_solicitacao(caminho, sid) == "AGUARDANDO_CONFIRMACAO"

    recusa = cliente.post(
        f"/api/solicitacoes/{sid}/contatos",
        json={"canal": "TELEFONE", "resultado": "SEM_RESPOSTA", "operador": "operador"},
        headers=_headers(OPERADOR),
    )
    assert recusa.status_code == 201
    assert _status_solicitacao(caminho, sid) == "AGUARDANDO_REAGENDAMENTO"


def test_simulacao_gera_proposta_confirmavel_que_ocupa_vaga(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, prontuario="88888882")
    slot = _criar_slot(cliente, capacidade=2)

    simulacao = cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    assert simulacao.status_code == 201, simulacao.text
    assert simulacao.json()["geradas"] == 1
    assert simulacao.json()["dias"] == 30

    proposta = cliente.get(
        "/api/agendamentos/calendario",
        params={"de": _iso(_agora() - timedelta(days=1)),
                "ate": _iso(_agora() + timedelta(days=31))},
        headers=_headers(OPERADOR),
    ).json()["agendamentos"][0]
    assert proposta["status"] == "PROPOSTO"
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["livres"] == 1
    assert _status_solicitacao(caminho, sid) == "AGUARDANDO_CONFIRMACAO"

    confirmada = cliente.post(
        f"/api/agendamentos/{proposta['id']}/confirmar",
        json={"autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    assert confirmada.status_code == 200, confirmada.text
    assert confirmada.json()["status"] == "ATIVO"
    assert _status_solicitacao(caminho, sid) == "AGENDADA"

    with _conexao(caminho) as conn:
        acoes = {
            linha["acao"]
            for linha in conn.execute("SELECT acao FROM audit_logs").fetchall()
        }
    assert {"GERAR_PROPOSTA_AGENDA", "CONFIRMAR_PROPOSTA_AGENDA"} <= acoes


def test_mover_proposta_ajusta_horario_sem_confirmar(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, prontuario="88888890")
    primeiro = _criar_slot(cliente, minutos=60, capacidade=2)
    segundo = _criar_slot(cliente, minutos=120, capacidade=2)
    proposta = _gerar_proposta(cliente)
    assert proposta["slotId"] == primeiro["id"]

    resposta = cliente.post(
        f"/api/agendamentos/{proposta['id']}/mover",
        json={"slotId": segundo["id"], "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 200, resposta.text
    movida = resposta.json()
    assert movida["status"] == "PROPOSTO"
    assert movida["slotId"] == segundo["id"]
    assert movida["dataHora"] == segundo["inicio"]
    assert _status_solicitacao(caminho, sid) == "AGUARDANDO_CONFIRMACAO"

    calendario = _calendario(cliente)
    assert _slot_no_calendario(calendario, primeiro["id"])["ocupadas"] == 0
    assert _slot_no_calendario(calendario, primeiro["id"])["livres"] == 2
    assert _slot_no_calendario(calendario, segundo["id"])["ocupadas"] == 1
    assert _slot_no_calendario(calendario, segundo["id"])["livres"] == 1

    with _conexao(caminho) as conn:
        acoes = {
            linha["acao"]
            for linha in conn.execute("SELECT acao FROM audit_logs").fetchall()
        }
    assert "MOVER_PROPOSTA_AGENDA" in acoes

    mesma_vaga = cliente.post(
        f"/api/agendamentos/{proposta['id']}/mover",
        json={"slotId": segundo["id"], "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert mesma_vaga.status_code == 422


def test_mover_proposta_rejeita_destino_invalido_e_respeita_rbac(cliente):
    cliente, caminho = cliente
    _inserir_solicitacao(caminho, prontuario="88888891")
    _criar_slot(cliente, minutos=60, capacidade=2)
    outro_exame = _criar_slot(cliente, minutos=120, capacidade=2, codigo="RX", nome="Raio-X")
    proposta = _gerar_proposta(cliente)

    # Coordenação é somente leitura.
    assert cliente.post(
        f"/api/agendamentos/{proposta['id']}/mover",
        json={"slotId": outro_exame["id"], "autor": "coordenacao"},
        headers=_headers(COORDENACAO),
    ).status_code == 403

    # A vaga de destino precisa corresponder ao exame solicitado.
    incompativel = cliente.post(
        f"/api/agendamentos/{proposta['id']}/mover",
        json={"slotId": outro_exame["id"], "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert incompativel.status_code == 422

    # Vaga de destino esgotada por um agendamento ativo de outro paciente.
    cheia = _criar_slot(cliente, minutos=180, capacidade=1)
    outro_sid, _ = _inserir_solicitacao(caminho, prontuario="88888892")
    assert _agendar(cliente, outro_sid, cheia["id"]).status_code == 201
    esgotada = cliente.post(
        f"/api/agendamentos/{proposta['id']}/mover",
        json={"slotId": cheia["id"], "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert esgotada.status_code == 409

    # Somente propostas pendentes podem ser movidas.
    confirmada = cliente.post(
        f"/api/agendamentos/{proposta['id']}/confirmar",
        json={"autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert confirmada.status_code == 200, confirmada.text
    ativo = cliente.post(
        f"/api/agendamentos/{proposta['id']}/mover",
        json={"slotId": outro_exame["id"], "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert ativo.status_code == 422


def test_nao_confirmacao_devolve_vaga_e_vai_para_reagendamento(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, prontuario="88888883")
    slot = _criar_slot(cliente, capacidade=1)
    cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    proposta = cliente.get(
        "/api/agendamentos/calendario",
        params={"de": _iso(_agora() - timedelta(days=1)),
                "ate": _iso(_agora() + timedelta(days=31))},
        headers=_headers(OPERADOR),
    ).json()["agendamentos"][0]

    resposta = cliente.post(
        f"/api/agendamentos/{proposta['id']}/nao-confirmado",
        json={"justificativa": "Paciente não confirmou", "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status"] == "CANCELADO"
    assert _status_solicitacao(caminho, sid) == "AGUARDANDO_REAGENDAMENTO"
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["livres"] == 1


def test_novos_endpoints_de_proposta_respeitam_rbac(cliente):
    cliente, caminho = cliente
    _inserir_solicitacao(caminho, prontuario="88888884")
    _criar_slot(cliente, capacidade=2)
    assert cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "coordenacao"},
        headers=_headers(COORDENACAO),
    ).status_code == 403
    assert cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "usuario"},
        headers=_headers(["Users"]),
    ).status_code == 403

    assert cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "operador"},
        headers=_headers(OPERADOR),
    ).status_code == 201
    proposta = cliente.get(
        "/api/agendamentos/calendario",
        params={"de": _iso(_agora() - timedelta(days=1)),
                "ate": _iso(_agora() + timedelta(days=31))},
        headers=_headers(OPERADOR),
    ).json()["agendamentos"][0]

    assert cliente.post(
        f"/api/agendamentos/{proposta['id']}/confirmar",
        json={"autor": "coordenacao"},
        headers=_headers(COORDENACAO),
    ).status_code == 403
    assert cliente.post(
        f"/api/agendamentos/{proposta['id']}/confirmar",
        json={"autor": "usuario"},
        headers=_headers(["Users"]),
    ).status_code == 403
    assert cliente.post(
        f"/api/agendamentos/{proposta['id']}/nao-confirmado",
        json={"justificativa": "Sem retorno", "autor": "coordenacao"},
        headers=_headers(COORDENACAO),
    ).status_code == 403
    assert cliente.post(
        f"/api/agendamentos/{proposta['id']}/nao-confirmado",
        json={"justificativa": "Sem retorno", "autor": "usuario"},
        headers=_headers(["Users"]),
    ).status_code == 403


def test_nao_confirmacao_exige_justificativa(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho, prontuario="88888885")
    slot = _criar_slot(cliente, capacidade=1)
    cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    proposta = cliente.get(
        "/api/agendamentos/calendario",
        params={"de": _iso(_agora() - timedelta(days=1)),
                "ate": _iso(_agora() + timedelta(days=31))},
        headers=_headers(OPERADOR),
    ).json()["agendamentos"][0]
    resposta = cliente.post(
        f"/api/agendamentos/{proposta['id']}/nao-confirmado",
        json={"justificativa": "   ", "autor": "chefia"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 422
    assert _status_solicitacao(caminho, sid) == "AGUARDANDO_CONFIRMACAO"
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["livres"] == 0


def test_simulacao_ordena_por_prioridade_e_distribui_entre_dias(cliente):
    cliente, caminho = cliente
    primeiro = _criar_slot(cliente, minutos=60, capacidade=1, unidade="IMAGEM-A")
    segundo = _criar_slot(
        cliente, minutos=60 + 24 * 60, capacidade=1, unidade="IMAGEM-B"
    )
    sid_alta, _ = _inserir_solicitacao(
        caminho, prontuario="90000001", protocolo="PROTO-ALTA", pontuacao=90
    )
    sid_media, _ = _inserir_solicitacao(
        caminho, prontuario="90000002", protocolo="PROTO-MEDIA", pontuacao=50
    )

    simulacao = cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "chefia"},
        headers=_headers(CHEFIA),
    )
    assert simulacao.status_code == 201, simulacao.text
    dados = simulacao.json()
    assert dados["geradas"] == 2
    assert [item["protocolo"] for item in dados["propostas"]] == [
        "PROTO-ALTA", "PROTO-MEDIA"
    ]
    assert [item["prioridade"] for item in dados["propostas"]] == ["ALTA", "MEDIA"]
    assert dados["propostas"][0]["dataHora"] == primeiro["inicio"]
    assert dados["propostas"][1]["dataHora"] == segundo["inicio"]
    assert dados["propostas"][0]["dataHora"][:10] != dados["propostas"][1]["dataHora"][:10]
    assert all(
        set(item) == {
            "agendamentoId", "solicitacaoId", "protocolo", "pacienteNome", "prontuario",
            "prioridade", "pontuacao", "unidadeSolicitante", "exames", "status",
            "statusSolicitacao", "dataHora", "unidade", "nomeExame", "recebidaEm",
            "tempoNaFilaHoras",
        }
        for item in dados["propostas"]
    )

    fila = cliente.get(
        "/api/agendamentos/propostas", headers=_headers(OPERADOR)
    )
    assert fila.status_code == 200, fila.text
    assert [item["protocolo"] for item in fila.json()] == ["PROTO-ALTA", "PROTO-MEDIA"]
    calendario = _calendario(cliente)
    assert _slot_no_calendario(calendario, primeiro["id"])["ocupadas"] == 1
    assert _slot_no_calendario(calendario, primeiro["id"])["livres"] == 0
    assert _slot_no_calendario(calendario, segundo["id"])["ocupadas"] == 1
    assert _slot_no_calendario(calendario, segundo["id"])["livres"] == 0

    # Uma nova execução não pode ignorar as reservas feitas pela anterior.
    _inserir_solicitacao(
        caminho, prontuario="90000003", protocolo="PROTO-TERCEIRO", pontuacao=70
    )
    segunda_simulacao = cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "chefia"},
        headers=_headers(CHEFIA),
    )
    assert segunda_simulacao.status_code == 201, segunda_simulacao.text
    assert segunda_simulacao.json()["geradas"] == 0
    assert len(cliente.get(
        "/api/agendamentos/propostas", headers=_headers(OPERADOR)
    ).json()) == 2
    assert _status_solicitacao(caminho, sid_alta) == "AGUARDANDO_CONFIRMACAO"
    assert _status_solicitacao(caminho, sid_media) == "AGUARDANDO_CONFIRMACAO"


def test_chefia_pode_editar_disponibilidade_de_vagas(cliente):
    cliente, caminho = cliente
    slot = _criar_slot(cliente, capacidade=3)

    assert cliente.get(
        "/api/admin/agenda/slots", headers=_headers(CHEFIA)
    ).status_code == 200

    novo = cliente.post(
        "/api/admin/agenda/slots",
        json={
            "unidade": "IMAGEM",
            "codigoExame": "CMDIP",
            "nomeExame": "Cintilografia",
            "inicio": _iso(_agora() + timedelta(minutes=120)),
            "fim": _iso(_agora() + timedelta(minutes=150)),
            "capacidade": 2,
            "situacao": "DISPONIVEL",
        },
        headers=_headers(CHEFIA),
    )
    assert novo.status_code == 201, novo.text

    alterado = cliente.patch(
        f"/api/admin/agenda/slots/{slot['id']}",
        json={
            "unidade": "IMAGEM-CENTRAL",
            "codigoExame": "CMDIP",
            "nomeExame": "Cintilografia do miocárdio",
            "capacidade": 5,
            "status": "ENCERRADO",
        },
        headers=_headers(CHEFIA),
    )
    assert alterado.status_code == 200, alterado.text
    assert alterado.json()["unidade"] == "IMAGEM-CENTRAL"
    assert alterado.json()["capacidade"] == 5
    assert alterado.json()["status"] == "ENCERRADO"

    with _conexao(caminho) as conn:
        acoes = {
            linha["acao"]
            for linha in conn.execute(
                "SELECT acao FROM audit_logs WHERE categoria='CONFIGURACAO'"
            ).fetchall()
        }
    assert {"CRIAR_SLOT_AGENDA", "ATUALIZAR_SLOT_AGENDA"} <= acoes


def test_capacidade_da_vaga_nao_pode_cair_abaixo_das_ocupadas(cliente):
    cliente, caminho = cliente
    sid_a, _ = _inserir_solicitacao(caminho, prontuario="90000004", protocolo="PROTO-OCUPADA")
    sid_b, _ = _inserir_solicitacao(
        caminho, prontuario="90000005", protocolo="PROTO-OCUPADA-2"
    )
    slot = _criar_slot(cliente, capacidade=3)
    assert _agendar(cliente, sid_a, slot["id"]).status_code == 201
    assert _agendar(cliente, sid_b, slot["id"]).status_code == 201

    resposta = cliente.patch(
        f"/api/admin/agenda/slots/{slot['id']}",
        json={"capacidade": 1},
        headers=_headers(GESTOR),
    )
    assert resposta.status_code == 422
    assert "ocupadas" in resposta.json()["detail"]
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["capacidade"] == 3


def test_chefia_pode_remover_vaga_vazia_com_auditoria(cliente):
    cliente, caminho = cliente
    slot = _criar_slot(cliente, situacao="ENCERRADO")
    assert slot["status"] == "ENCERRADO"

    resposta = cliente.delete(
        f"/api/admin/agenda/slots/{slot['id']}", headers=_headers(CHEFIA)
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["id"] == slot["id"]
    assert cliente.delete(
        f"/api/admin/agenda/slots/{slot['id']}", headers=_headers(CHEFIA)
    ).status_code == 404
    assert all(
        item["id"] != slot["id"] for item in cliente.get(
            "/api/admin/agenda/slots", headers=_headers(CHEFIA)
        ).json()
    )
    assert all(item["id"] != slot["id"] for item in _calendario(cliente)["slots"])

    with _conexao(caminho) as conn:
        linhas = conn.execute(
            "SELECT acao, dados_anteriores FROM audit_logs WHERE acao='REMOVER_SLOT_AGENDA'"
        ).fetchall()
    assert len(linhas) == 1
    assert "CMDIP" in linhas[0]["dados_anteriores"]


def test_remocao_de_vaga_ocupada_e_bloqueada(cliente):
    cliente, caminho = cliente
    sid, _ = _inserir_solicitacao(caminho)
    slot = _criar_slot(cliente, capacidade=2)
    assert _agendar(cliente, sid, slot["id"]).status_code == 201

    resposta = cliente.delete(
        f"/api/admin/agenda/slots/{slot['id']}", headers=_headers(GESTOR)
    )
    assert resposta.status_code == 409
    assert "agendamentos ativos ou propostas" in resposta.json()["detail"]
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["capacidade"] == 2

    with _conexao(caminho) as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS total FROM audit_logs WHERE acao='REMOVER_SLOT_AGENDA'"
        ).fetchone()["total"]
    assert total == 0


def test_coordenacao_nao_pode_remover_vaga(cliente):
    cliente, _ = cliente
    slot = _criar_slot(cliente)
    assert cliente.delete(
        f"/api/admin/agenda/slots/{slot['id']}", headers=_headers(COORDENACAO)
    ).status_code == 403
    assert _slot_no_calendario(_calendario(cliente), slot["id"])["status"] == "DISPONIVEL"


def test_copia_de_semana_preserva_configuracao_e_e_idempotente(cliente):
    cliente, caminho = cliente
    slot = _criar_slot(cliente, capacidade=4, situacao="ENCERRADO")
    data_slot = datetime.fromisoformat(slot["inicio"][:10])
    origem = (data_slot - timedelta(days=data_slot.weekday())).date().isoformat()
    destino = (datetime.fromisoformat(origem) + timedelta(days=7)).date().isoformat()
    corpo = {"origem": slot["inicio"][:10], "destino": destino, "codigoExame": "CMDIP"}

    resposta = cliente.post(
        "/api/admin/agenda/copiar-semana", json=corpo, headers=_headers(CHEFIA)
    )
    assert resposta.status_code == 200, resposta.text
    resultado = resposta.json()
    assert resultado["origem"] == origem
    assert resultado["destino"] == destino
    assert resultado["total"] == 1 and resultado["ignoradas"] == 0
    assert len(resultado["criadas"]) == 1

    copia = resultado["criadas"][0]
    assert copia["id"] != slot["id"]
    assert copia["unidade"] == slot["unidade"]
    assert copia["codigoExame"] == slot["codigoExame"]
    assert copia["nomeExame"] == slot["nomeExame"]
    assert copia["capacidade"] == 4
    assert copia["status"] == "ENCERRADO"
    data_copia = (data_slot + timedelta(days=7)).date().isoformat()
    assert copia["inicio"][:10] == data_copia
    assert copia["inicio"][11:19] == slot["inicio"][11:19]
    assert copia["fim"][:10] == data_copia
    assert copia["fim"][11:19] == slot["fim"][11:19]

    repetida = cliente.post(
        "/api/admin/agenda/copiar-semana", json=corpo, headers=_headers(GESTOR)
    )
    assert repetida.status_code == 200, repetida.text
    assert repetida.json()["criadas"] == []
    assert repetida.json()["ignoradas"] == 1

    with _conexao(caminho) as conn:
        linhas = conn.execute(
            """SELECT acao, dados_anteriores, dados_novos FROM audit_logs
               WHERE acao='COPIAR_SEMANA_SLOT_AGENDA'"""
        ).fetchall()
    assert len(linhas) == 2
    assert copia["id"] in linhas[0]["dados_novos"]
    assert "CMDIP" in linhas[0]["dados_anteriores"]

    slots_admin = cliente.get(
        "/api/admin/agenda/slots", headers=_headers(CHEFIA)
    ).json()
    assert {item["id"] for item in slots_admin} == {slot["id"], copia["id"]}


def test_coordenacao_nao_pode_copiar_semana(cliente):
    cliente, _ = cliente
    slot = _criar_slot(cliente)
    data_slot = datetime.fromisoformat(slot["inicio"][:10])
    destino = (data_slot + timedelta(days=7)).date().isoformat()
    resposta = cliente.post(
        "/api/admin/agenda/copiar-semana",
        json={"origem": slot["inicio"][:10], "destino": destino},
        headers=_headers(COORDENACAO),
    )
    assert resposta.status_code == 403
    assert len(cliente.get(
        "/api/admin/agenda/slots", headers=_headers(CHEFIA)
    ).json()) == 1


def test_copia_de_semana_valida_intervalo(cliente):
    cliente, _ = cliente
    slot = _criar_slot(cliente)
    origem = slot["inicio"][:10]
    assert cliente.post(
        "/api/admin/agenda/copiar-semana",
        json={"origem": origem, "destino": origem},
        headers=_headers(GESTOR),
    ).status_code == 422
    assert cliente.post(
        "/api/admin/agenda/copiar-semana",
        json={"origem": origem, "destino": "data-invalida"},
        headers=_headers(GESTOR),
    ).status_code == 422
    origem_vazia = (datetime.fromisoformat(origem) + timedelta(days=28)).date().isoformat()
    destino_vazio = (datetime.fromisoformat(origem_vazia) + timedelta(days=7)).date().isoformat()
    resposta = cliente.post(
        "/api/admin/agenda/copiar-semana",
        json={"origem": origem_vazia, "destino": destino_vazio},
        headers=_headers(GESTOR),
    )
    assert resposta.status_code == 422
    assert "origem" in resposta.json()["detail"]


def test_edicao_em_lote_altera_status_multiplos_agendamentos(cliente):
    cliente, caminho = cliente
    # Cria 3 solicitações com aceite e gera propostas para elas.
    ids = []
    for i in range(3):
        sid, _ = _inserir_solicitacao(caminho, prontuario=f"900001{i:02d}")
        _criar_slot(cliente, minutos=60 + i * 30, capacidade=2)
    # Gera propostas (pode gerar mais de uma se houver múltiplas solicitações elegíveis)
    resposta = cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    assert resposta.status_code == 201, resposta.text
    propostas = resposta.json()["propostas"]
    assert len(propostas) >= 1, "Esperava pelo menos uma proposta gerada."
    ids = [item["agendamentoId"] for item in propostas]

    # Edição em lote: operador não pode (403).
    nao_permitido = cliente.post(
        "/api/agendamentos/lote",
        json={
            "agendamentoIds": ids,
            "novoStatus": "ATIVO",
            "justificativa": "Lote de teste",
            "autor": "operador",
        },
        headers=_headers(OPERADOR),
    )
    assert nao_permitido.status_code == 403

    # Chefia pode.
    resposta_lote = cliente.post(
        "/api/agendamentos/lote",
        json={
            "agendamentoIds": ids,
            "novoStatus": "ATIVO",
            "justificativa": "Confirmação em lote da chefia.",
            "autor": "chefia",
        },
        headers=_headers(CHEFIA),
    )
    assert resposta_lote.status_code == 200, resposta_lote.text
    dados = resposta_lote.json()
    assert dados["processados"] == len(ids)
    assert dados["novoStatus"] == "ATIVO"
    assert len(dados["itens"]) == len(ids)

    # Verifica que os agendamentos realmente mudaram.
    calendario = _calendario(cliente)
    for item in dados["itens"]:
        ag = next((a for a in calendario["agendamentos"] if a["id"] == item["agendamentoId"]), None)
        assert ag is not None, f"Agendamento {item['agendamentoId']} não encontrado no calendário."
        assert ag["status"] == "ATIVO"

    # Auditoria: cada item deve ter um log ALTERAR_STATUS_LOTE.
    with _conexao(caminho) as conn:
        acoes = {
            linha["acao"]
            for linha in conn.execute("SELECT acao FROM audit_logs").fetchall()
        }
    assert "ALTERAR_STATUS_LOTE" in acoes


def test_edicao_em_lote_exige_justificativa(cliente):
    cliente, caminho = cliente
    _inserir_solicitacao(caminho, prontuario="90000201")
    _criar_slot(cliente, minutos=60, capacidade=2)
    cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    propostas = cliente.post(
        "/api/agendamentos/lote",
        json={
            "agendamentoIds": ["id-inexistente"],
            "novoStatus": "ATIVO",
            "justificativa": "",
            "autor": "chefia",
        },
        headers=_headers(CHEFIA),
    )
    assert propostas.status_code in (400, 422)


def test_edicao_em_lote_sem_ids_devolve_erro(cliente):
    cliente, caminho = cliente
    resposta = cliente.post(
        "/api/agendamentos/lote",
        json={
            "agendamentoIds": [],
            "novoStatus": "ATIVO",
            "justificativa": "Sem itens.",
            "autor": "chefia",
        },
        headers=_headers(CHEFIA),
    )
    assert resposta.status_code in (400, 422)


def test_edicao_em_lote_bloqueia_coordenacao(cliente):
    cliente, caminho = cliente
    _inserir_solicitacao(caminho, prontuario="90000202")
    _criar_slot(cliente, minutos=60, capacidade=2)
    cliente.post(
        "/api/agendamentos/propostas/gerar",
        json={"dias": 30, "autor": "operador"},
        headers=_headers(OPERADOR),
    )
    resposta = cliente.post(
        "/api/agendamentos/lote",
        json={
            "agendamentoIds": ["id-inexistente"],
            "novoStatus": "CANCELADO",
            "justificativa": "Tentativa de coordenação.",
            "autor": "coordenacao",
        },
        headers=_headers(COORDENACAO),
    )
    assert resposta.status_code == 403
