"""Testes diretos de API para persistência, regras e RBAC da Recepção."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest


PERFIS_MOCK = [
    "recepcionista",
    "macroscopia",
    "processamento",
    "ihq",
    "residente",
    "patologista",
    "citotecnico",
    "arquivo",
    "admin",
]


def token(client, username: str) -> dict[str, str]:
    """Faz login por uma identidade mock configurada e retorna bearer token."""
    resposta = client.post("/api/login", data={"username": username, "password": "demo"})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def conferencia(completa: bool = True) -> dict[str, bool]:
    """Monta os quatro itens exigidos pela conferência existente."""
    return {
        "identificacaoConfere": completa,
        "materialConfere": completa,
        "quantidadeConfere": completa,
        "recipienteAdequado": completa,
    }


def entrada(solicitacao: str = "7712301", tipo: str = "HP") -> dict:
    """Monta payload válido para receber uma solicitação fictícia."""
    return {
        "solicitacaoCodigo": solicitacao,
        "conferencia": conferencia(),
        "tipoExame": tipo,
        "quantidade": 1,
        "urgente": tipo == "CO",
        "motivoUrgencia": "Cirurgia em andamento" if tipo == "CO" else None,
        "procedimento": "Biópsia endoscópica",
    }


def receber(client, solicitacao: str = "7712301", tipo: str = "HP") -> dict:
    """Cria caso usando identidade que possui a permissão de recebimento."""
    resposta = client.post(
        "/api/ap/recebimentos",
        headers=token(client, "recepcionista"),
        json=entrada(solicitacao, tipo),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_rotas_sao_privadas_e_consultas_seguem_catalogo_por_perfil(client):
    assert client.get("/api/ap/casos").status_code == 401
    assert client.get("/api/ap/solicitacoes/pendentes").status_code == 401

    for username in PERFIS_MOCK:
        headers = token(client, username)
        assert client.get("/api/ap/casos", headers=headers).status_code == 200
        assert client.get("/api/ap/solicitacoes/pendentes", headers=headers).status_code == 200

    sem_perfil = token(client, "sem-perfil")
    assert client.get("/api/ap/casos", headers=sem_perfil).status_code == 403
    assert client.get("/api/ap/auditoria", headers=token(client, "recepcionista")).status_code == 403
    assert client.get("/api/ap/auditoria", headers=token(client, "recepcao-coordenacao")).status_code == 200


def test_api_mantem_carga_ap_completa_e_recepcionista_consulta_devolucoes(demo_client):
    headers = token(demo_client, "recepcionista")

    casos = demo_client.get("/api/ap/casos", headers=headers)
    pendentes = demo_client.get("/api/ap/solicitacoes/pendentes", headers=headers)
    rejeicao = demo_client.get("/api/ap/solicitacoes/7712045", headers=headers)
    devolucoes = demo_client.get("/api/ap/devolucoes", headers=headers)

    assert casos.status_code == 200 and len(casos.json()) == 19
    assert pendentes.status_code == 200 and len(pendentes.json()) == 6
    assert rejeicao.status_code == 200 and rejeicao.json()["tipo"] == "DEVOLVIDA"
    assert devolucoes.status_code == 200 and len(devolucoes.json()) == 3


@pytest.mark.parametrize("username", [nome for nome in PERFIS_MOCK if nome != "recepcionista"])
def test_perfis_sem_recepcao_receber_nao_mutam_por_chamada_direta(client, username):
    headers = token(client, username)
    antes = client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json()
    resposta = client.post("/api/ap/recebimentos", headers=headers, json=entrada())
    depois = client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json()

    assert resposta.status_code == 403
    assert resposta.json()["detail"]
    assert depois == antes
    assert client.get("/api/ap/casos", headers=headers).json() == []

    auditoria = client.get("/api/ap/auditoria", headers=token(client, "recepcao-coordenacao"))
    assert auditoria.status_code == 200
    assert auditoria.json() == []


def test_recebimento_persiste_autoria_auditoria_e_impede_repeticao(client):
    headers = token(client, "recepcionista")
    payload = entrada()
    payload["responsavel"] = {"login": "usuario-forjado", "nome": "Autor forjado"}
    resposta = client.post("/api/ap/recebimentos", headers=headers, json=payload)

    assert resposta.status_code == 201, resposta.text
    caso = resposta.json()
    assert caso["responsavelEntrada"] == {"login": "recepcionista", "nome": "Recepcionista SAP"}
    assert caso["conferencia"]["resultado"] == "ACEITA"
    assert len(caso["materiais"]) == 1
    assert caso["historico"][0]["usuario"]["login"] == "recepcionista"

    # Nova chamada usa outra sessão HTTP e lê o estado persistido.
    detalhe = client.get(f"/api/ap/casos/{caso['numeroInterno']}", headers=headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["numeroInterno"] == caso["numeroInterno"]
    assert detalhe.json()["solicitacao"]["situacaoRecepcao"] == "RECEBIDA"
    assert client.get("/api/ap/solicitacoes/7712301", headers=headers).json()["tipo"] == "RECEBIDA"

    duplicada = client.post("/api/ap/recebimentos", headers=headers, json=entrada())
    assert duplicada.status_code == 409

    auditoria = client.get("/api/ap/auditoria", headers=token(client, "recepcao-coordenacao"))
    assert auditoria.status_code == 200
    evento = next(item for item in auditoria.json() if item["acao"] == "ENTRADA_CONFIRMADA")
    assert evento["usuario"]["login"] == "recepcionista"
    assert evento["dadosAnteriores"]["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"
    assert evento["dadosNovos"]["situacaoRecepcao"] == "RECEBIDA"
    assert evento["categoria"] == "NEGOCIO_CLINICO"
    assert evento["recurso"] == f"caso_ap:{caso['numeroInterno']}"
    assert evento["ipOrigem"] == "testclient"


def test_validacao_incompleta_retorna_detail_e_nao_persiste(client):
    headers = token(client, "recepcionista")
    payload = entrada()
    payload["conferencia"] = conferencia(completa=False)
    resposta = client.post("/api/ap/recebimentos", headers=headers, json=payload)

    assert resposta.status_code == 422
    assert resposta.json()["detail"]
    assert client.get("/api/ap/casos", headers=headers).json() == []
    assert client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json() == 5


def test_nao_conformidade_cria_devolucao_e_atualiza_solicitacao_atomicamente(client):
    headers = token(client, "recepcionista")
    payload = {
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoCodigo": "7712301", "conferencia": conferencia(False)},
        "tipo": "IDENTIFICACAO_DIVERGENTE",
        "descricao": "Identificação fictícia divergente na etiqueta.",
        "novaAmostraSolicitada": True,
        "responsavel": {"login": "falso", "nome": "Usuário falso"},
    }
    resposta = client.post("/api/ap/nao-conformidades", headers=headers, json=payload)

    assert resposta.status_code == 201, resposta.text
    devolucao = resposta.json()
    assert devolucao["rejeicaoNaRecepcao"] is True
    assert devolucao["naoConformidade"]["registradoPor"]["login"] == "recepcionista"
    leitura = client.get("/api/ap/solicitacoes/7712301", headers=headers).json()
    assert leitura["tipo"] == "DEVOLVIDA"
    assert leitura["tipoNaoConformidade"] == "IDENTIFICACAO_DIVERGENTE"

    auditoria = client.get("/api/ap/auditoria", headers=token(client, "recepcao-coordenacao")).json()
    evento = next(item for item in auditoria if item["acao"] == "NAO_CONFORMIDADE_DEVOLUCAO")
    assert evento["usuario"]["login"] == "recepcionista"
    assert evento["dadosNovos"]["situacaoDevolucao"] == "AGUARDANDO_NOVA_AMOSTRA"


def test_nao_conformidade_em_caso_muda_status_e_registra_historico(client):
    headers = token(client, "recepcionista")
    caso = receber(client)
    resposta = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "CASO", "casoNumero": caso["numeroInterno"]},
        "tipo": "MATERIAL_INADEQUADO",
        "descricao": "Material fictício inadequado.",
        "novaAmostraSolicitada": False,
    })

    assert resposta.status_code == 201, resposta.text
    detalhe = client.get(f"/api/ap/casos/{caso['numeroInterno']}", headers=headers).json()
    assert detalhe["status"] == "DEVOLVIDO"
    assert len(detalhe["naoConformidades"]) == 1
    assert len(detalhe["devolucoes"]) == 1
    assert [item["evento"] for item in detalhe["historico"]][-2:] == ["NAO_CONFORMIDADE", "DEVOLUCAO"]


def test_cancelamento_exige_permissao_admin_e_motivo(client):
    caso = receber(client)
    numero = caso["numeroInterno"]
    proibida = client.post("/api/ap/casos/cancelamento", headers=token(client, "recepcionista"), json={
        "numeroInterno": numero, "motivo": "Motivo de teste",
    })
    assert proibida.status_code == 403

    cancelada = client.post("/api/ap/casos/cancelamento", headers=token(client, "admin"), json={
        "numeroInterno": numero, "motivo": "Solicitação fictícia duplicada.",
    })
    assert cancelada.status_code == 200, cancelada.text
    assert cancelada.json()["status"] == "CANCELADO"
    assert cancelada.json()["cancelamento"]["canceladoPor"]["login"] == "admin"

    repetida = client.post("/api/ap/casos/cancelamento", headers=token(client, "admin"), json={
        "numeroInterno": numero, "motivo": "Segunda tentativa.",
    })
    assert repetida.status_code == 409


def test_plantao_e_limitado_a_congelacao_e_so_uma_vez(client):
    headers = token(client, "recepcionista")
    caso = receber(client, "7712340", "CO")
    chamada = client.post("/api/ap/casos/acionamentos-plantao", headers=headers, json={
        "numeroInterno": caso["numeroInterno"],
        "responsavel": {"login": "falso", "nome": "Falso"},
    })
    assert chamada.status_code == 200, chamada.text
    assert chamada.json()["historico"][-1]["usuario"]["login"] == "recepcionista"

    repetida = client.post("/api/ap/casos/acionamentos-plantao", headers=headers, json={
        "numeroInterno": caso["numeroInterno"],
    })
    assert repetida.status_code == 409


def test_associacao_ihq_impressao_e_devolucao_seguem_politica_validada(client):
    entrada_ihq = {"solicitacaoCodigo": "7712356", "conferencia": conferencia(), "casoOrigemNumero": "HP-0001/26"}
    impressao = {"numeroInterno": "HP-0001/26", "tipo": "ETIQUETAS"}
    for username in [*PERFIS_MOCK, "sem-perfil"]:
        headers = token(client, username)
        assert client.post("/api/ap/recebimentos/ihq", headers=headers, json=entrada_ihq).status_code == 501
        # O caminho coincide com a rota GET /casos/{numero:path}; como não há POST
        # para registrar impressão, o FastAPI responde 405 (método não permitido).
        assert client.post("/api/ap/casos/impressoes", headers=headers, json=impressao).status_code == 405
        status_consulta = client.get("/api/ap/devolucoes", headers=headers).status_code
        assert status_consulta == (200 if username in {"recepcionista", "admin"} else 403)
        status_atualizacao = client.patch("/api/ap/devolucoes/1/situacao", headers=headers, json={
            "situacao": "NOVA_AMOSTRA_RECEBIDA",
        }).status_code
        assert status_atualizacao == (404 if username in {"recepcionista", "admin"} else 403)

    assert client.post("/api/ap/recebimentos/ihq", json=entrada_ihq).status_code == 401
    assert client.get("/api/ap/devolucoes").status_code == 401

    recepcao_coordenacao = token(client, "recepcao-coordenacao")
    assert client.get("/api/ap/devolucoes", headers=recepcao_coordenacao).status_code == 200


def test_indisponibilidade_mock_afeta_listagem_leitura_mas_nao_contagem(client, monkeypatch):
    headers = token(client, "recepcionista")
    monkeypatch.setattr("src.config.settings.AP_MOCK_REQUESTS_AVAILABLE", False)

    assert client.get("/api/ap/solicitacoes/pendentes", headers=headers).status_code == 503
    leitura = client.get("/api/ap/solicitacoes/7712301", headers=headers)
    assert leitura.status_code == 503
    assert leitura.json()["detail"]
    assert client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json() == 5


def test_recebimento_concorrente_nao_gera_numero_interno_duplicado(client):
    headers = token(client, "recepcionista")
    payloads = [entrada("7712301"), entrada("7712318")]

    def enviar(payload):
        return client.post("/api/ap/recebimentos", headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        respostas = list(executor.map(enviar, payloads))

    assert sorted(resposta.status_code for resposta in respostas) == [201, 409]
    assert len(client.get("/api/ap/casos", headers=headers).json()) == 1
    assert client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json() == 4


def test_seed_de_solicitacoes_e_idempotente_e_preserva_estado_local(tmp_path):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.models.ap_reception import ApSolicitacao  # noqa: F401
    from src.providers.fixtures.reception_requests import solicitacoes_ficticias
    from src.providers.implementations.reception_sqlite_provider import ReceptionSqliteProvider
    from src.resources.database import Base

    async def executar():
        engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'seed.db').as_posix()}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory() as session:
                provider = ReceptionSqliteProvider(session)
                fixture = solicitacoes_ficticias()
                await provider.seed_solicitacoes(fixture)
                await provider.seed_solicitacoes(fixture)
                assert await provider.contar_solicitacoes_pendentes() == len(fixture)

                solicitacao = await provider.buscar_solicitacao(fixture[0]["codigoSolicitacao"])
                solicitacao["situacaoRecepcao"] = "RECEBIDA"
                await provider.salvar_solicitacao(solicitacao)
                await provider.seed_solicitacoes(fixture)
                persistida = await provider.buscar_solicitacao(fixture[0]["codigoSolicitacao"])
                assert persistida["situacaoRecepcao"] == "RECEBIDA"
        finally:
            await engine.dispose()

    asyncio.run(executar())


def test_seed_demo_reaproveita_carga_ap_existente_e_migra_placeholders(tmp_path):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.models.ap_reception import ApSolicitacao  # noqa: F401
    from src.providers.fixtures.reception_requests import carregar_estado_demo, solicitacoes_ficticias
    from src.providers.implementations.reception_sqlite_provider import ReceptionSqliteProvider
    from src.resources.database import Base

    async def executar():
        engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'demo-seed.db').as_posix()}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory() as session:
                provider = ReceptionSqliteProvider(session)
                await provider.seed_solicitacoes(solicitacoes_ficticias())
                estado = carregar_estado_demo()
                await provider.seed_demo_state(estado)

                assert len(await provider.listar_casos()) == len(estado["casos"]) == 19
                assert await provider.contar_solicitacoes_pendentes() == 6
                assert len(await provider.listar_devolucoes()) == 3
                solicitacao = await provider.buscar_solicitacao("7712301")
                assert not solicitacao["nomePaciente"].startswith("PACIENTE FICTÍCIO")

                await provider.seed_demo_state(estado)
                assert len(await provider.listar_casos()) == 19
                assert len(await provider.listar_devolucoes()) == 3
        finally:
            await engine.dispose()

    asyncio.run(executar())


def test_falha_de_auditoria_reverte_mutacao_e_historico(tmp_path):
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.controllers.reception_controller import ReceptionController
    from src.helpers.audit_helper import AuditLog
    from src.models.ap_reception import ApSolicitacao  # noqa: F401
    from src.providers.fixtures.reception_requests import solicitacoes_ficticias
    from src.providers.implementations.reception_sqlite_provider import ReceptionSqliteProvider
    from src.resources.database import Base

    async def executar():
        engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'rollback.db').as_posix()}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory() as session:
                provider = ReceptionSqliteProvider(session)
                await provider.seed_solicitacoes(solicitacoes_ficticias())

                def falhar_ao_confirmar_auditoria(sessao):
                    if any(isinstance(item, AuditLog) for item in sessao.new):
                        raise RuntimeError("Falha simulada na gravação da auditoria")

                event.listen(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)
                controller = ReceptionController(provider, session)
                with pytest.raises(RuntimeError, match="Falha simulada"):
                    await controller.confirmar_entrada(
                        entrada(),
                        {"username": "recepcionista", "displayName": ["Recepcionista SAP"]},
                        "192.0.2.10",
                    )

                assert await provider.contar_solicitacoes_pendentes() == 5
                assert await provider.listar_casos() == []
                event.remove(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)
        finally:
            await engine.dispose()

    asyncio.run(executar())
