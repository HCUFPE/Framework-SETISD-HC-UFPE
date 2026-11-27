"""Testes diretos de API para persistência, regras e RBAC da Recepção."""

import asyncio
import json
import sqlite3
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


def entrada(solicitacao_id: str = "7712301:HP", tipo: str = "HP") -> dict:
    """Monta payload válido para receber um grupo fictício de exame."""
    return {
        "solicitacaoId": solicitacao_id,
        "tipoExame": tipo,
        "urgente": tipo == "CO",
        "procedimento": "Biópsia endoscópica",
    }


def receber(client, solicitacao_id: str = "7712301:HP", tipo: str = "HP") -> dict:
    """Cria caso usando identidade que possui a permissão de recebimento."""
    resposta = client.post(
        "/api/ap/recebimentos",
        headers=token(client, "recepcionista"),
        json=entrada(solicitacao_id, tipo),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_grupo_revisao(client, codigo: str, prontuario: str) -> str:
    """Insere uma solicitação fictícia de Revisão para testar o recebimento derivado."""
    grupo_id = f"{codigo}:REVISAO"
    payload = {
        "id": grupo_id,
        "codigoSolicitacao": codigo,
        "tipoExameSugerido": "REVISAO",
        "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO",
        "dataSolicitacao": "2026-01-01T10:00:00",
        "prontuario": prontuario,
        "nomePaciente": "PACIENTE DE TESTE",
        "amostras": [{"numeroAmostra": "1", "descricaoMaterial": "Lâmina para revisão"}],
    }
    database = client.app.state.app_db.engine.url.database
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO ap_solicitacoes "
            "(id, codigo_solicitacao, tipo_exame, situacao_recepcao, data_solicitacao, payload) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (grupo_id, codigo, "REVISAO", "AGUARDANDO_RECEBIMENTO", payload["dataSolicitacao"], json.dumps(payload)),
        )
    return grupo_id


def criar_grupo_hp_para_ihq(client, codigo: str = "7712356") -> str:
    """Adiciona HP ao pedido IHQ de fixture para testar a origem obrigatória da mesma solicitação."""
    grupo_id = f"{codigo}:HP"
    payload = {
        "id": grupo_id,
        "codigoSolicitacao": codigo,
        "tipoExameSugerido": "HP",
        "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO",
        "dataSolicitacao": "2026-01-01T10:00:00",
        "prontuario": "23155281",
        "nomePaciente": "NEIDE CAMPELO SARMENTO",
        "amostras": [{"numeroAmostra": "2", "descricaoMaterial": "Biópsia gástrica"}],
    }
    database = client.app.state.app_db.engine.url.database
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO ap_solicitacoes "
            "(id, codigo_solicitacao, tipo_exame, situacao_recepcao, data_solicitacao, payload) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (grupo_id, codigo, "HP", "AGUARDANDO_RECEBIMENTO", payload["dataSolicitacao"], json.dumps(payload)),
        )
    return grupo_id


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


def test_recebimento_revisao_vincula_e_projeta_origem_e_derivado(client):
    headers = token(client, "recepcionista")
    origem = receber(client)
    grupo = criar_grupo_revisao(client, "7712398", origem["solicitacao"]["prontuario"])

    resposta = client.post(
        "/api/ap/recebimentos",
        headers=headers,
        json={
            "solicitacaoId": grupo,
            "tipoExame": "REVISAO",
            "urgente": False,
            "procedimento": "Revisão de lâmina",
            "casoOrigemNumero": origem["numeroInterno"],
            "tipoDerivacao": "REVISAO",
        },
    )

    assert resposta.status_code == 201, resposta.text
    revisao = resposta.json()
    assert revisao["numeroInterno"].startswith("REV-")
    assert revisao["casoOrigemNumero"] == origem["numeroInterno"]
    assert revisao["casoOrigem"]["numeroInterno"] == origem["numeroInterno"]
    assert revisao["etapaAtual"] == "MICROSCOPIA"

    detalhe_origem = client.get(f"/api/ap/casos/{origem['numeroInterno']}", headers=headers).json()
    assert any(item["numeroInterno"] == revisao["numeroInterno"] for item in detalhe_origem["examesDerivados"])
    assert any(item["evento"] == "EXAME_DERIVADO_VINCULADO" for item in detalhe_origem["historico"])
    assert any(item["evento"] == "CASO_ORIGEM_VINCULADO" for item in revisao["historico"])


def test_revisao_recusa_origem_terminal_e_prontuario_divergente(client):
    headers = token(client, "recepcionista")
    origem = receber(client)
    grupo = criar_grupo_revisao(client, "7712397", "PRONTUARIO-DIFERENTE")
    corpo = {
        "solicitacaoId": grupo,
        "tipoExame": "REVISAO",
        "urgente": False,
        "procedimento": "Revisão de lâmina",
        "casoOrigemNumero": origem["numeroInterno"],
        "tipoDerivacao": "REVISAO",
    }

    divergente = client.post("/api/ap/recebimentos", headers=headers, json=corpo)
    assert divergente.status_code == 422
    assert "prontuário divergente" in divergente.json()["detail"]

    confirmada = client.post(
        "/api/ap/recebimentos", headers=headers, json={**corpo, "divergenciaConfirmada": True}
    )
    assert confirmada.status_code == 201, confirmada.text


def test_revisao_nao_altera_estado_da_origem_ao_cancelar_derivado(client):
    headers = token(client, "recepcionista")
    origem = receber(client)
    grupo = criar_grupo_revisao(client, "7712396", origem["solicitacao"]["prontuario"])
    revisao = client.post(
        "/api/ap/recebimentos",
        headers=headers,
        json={
            "solicitacaoId": grupo,
            "tipoExame": "REVISAO",
            "urgente": False,
            "procedimento": "Revisão de lâmina",
            "casoOrigemNumero": origem["numeroInterno"],
            "tipoDerivacao": "REVISAO",
        },
    ).json()
    cancelamento = client.post(
        "/api/ap/casos/cancelamento",
        headers=token(client, "recepcao-coordenacao"),
        json={"numeroInterno": revisao["numeroInterno"], "motivo": "Revisão não necessária"},
    )

    assert cancelamento.status_code == 200, cancelamento.text
    origem_atualizada = client.get(f"/api/ap/casos/{origem['numeroInterno']}", headers=headers).json()
    assert origem_atualizada["status"] == "RECEBIDO"
    assert any(item["status"] == "CANCELADO" for item in origem_atualizada["examesDerivados"])


def test_revisao_reverte_persistencia_quando_auditoria_falha(client, monkeypatch):
    headers = token(client, "recepcionista")
    origem = receber(client)
    grupo = criar_grupo_revisao(client, "7712395", origem["solicitacao"]["prontuario"])

    async def falhar_auditoria(**_kwargs):
        raise RuntimeError("Falha simulada de auditoria")

    monkeypatch.setattr("src.controllers.reception_controller.registrar_auditoria", falhar_auditoria)
    with pytest.raises(RuntimeError, match="Falha simulada"):
        client.post(
            "/api/ap/recebimentos",
            headers=headers,
            json={
                "solicitacaoId": grupo,
                "tipoExame": "REVISAO",
                "urgente": False,
                "procedimento": "Revisão de lâmina",
                "casoOrigemNumero": origem["numeroInterno"],
                "tipoDerivacao": "REVISAO",
            },
        )

    grupos = client.get("/api/ap/solicitacoes/7712395/exames", headers=headers).json()
    revisao = next(item for item in grupos if item["id"] == grupo)
    casos = client.get("/api/ap/casos", headers=headers).json()
    assert revisao["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"
    assert all(item["tipoExame"] != "REVISAO" for item in casos)


def test_revisao_recusa_caso_de_origem_cancelado(client):
    origem = receber(client)
    client.post(
        "/api/ap/casos/cancelamento",
        headers=token(client, "recepcao-coordenacao"),
        json={"numeroInterno": origem["numeroInterno"], "motivo": "Caso encerrado"},
    )
    grupo = criar_grupo_revisao(client, "7712394", origem["solicitacao"]["prontuario"])
    resposta = client.post(
        "/api/ap/recebimentos",
        headers=token(client, "recepcionista"),
        json={
            "solicitacaoId": grupo,
            "tipoExame": "REVISAO",
            "urgente": False,
            "procedimento": "Revisão de lâmina",
            "casoOrigemNumero": origem["numeroInterno"],
            "tipoDerivacao": "REVISAO",
        },
    )
    assert resposta.status_code == 422
    assert "não pode receber Revisão" in resposta.json()["detail"]


def test_cancelamento_de_exame_preserva_grupo_irmao_e_audita(client):
    headers = token(client, "recepcao-coordenacao")
    resposta = client.post(
        "/api/ap/solicitacoes/cancelamento",
        headers=headers,
        json={"solicitacaoId": "7712301:CG", "motivo": "Exame não necessário"},
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["situacaoRecepcao"] == "CANCELADA"
    assert resposta.json()["cancelamento"]["canceladoPor"]["login"] == "recepcao-coordenacao"

    leitura = client.get("/api/ap/solicitacoes/7712301002", headers=headers).json()
    assert leitura["tipo"] == "PENDENTE"
    assert [grupo["id"] for grupo in leitura["exames"]] == ["7712301:HP"]
    assert leitura["amostraBipadaSituacao"]["situacaoRecepcao"] == "CANCELADA"

    logs = client.get("/api/ap/auditoria", headers=headers).json()
    log = next(item for item in logs if item["acao"] == "SOLICITACAO_EXAME_CANCELADA")
    assert log["recurso"] == "solicitacao_exame:7712301:CG"
    assert log["ipOrigem"]


def test_cancelamento_total_exige_permissao_motivo_e_estado_pendente(client):
    sem_permissao = client.post(
        "/api/ap/solicitacoes/cancelamento",
        headers=token(client, "recepcionista"),
        json={"solicitacaoId": "7712301:HP", "motivo": "Não será processado"},
    )
    assert sem_permissao.status_code == 403

    headers = token(client, "recepcao-coordenacao")
    sem_motivo = client.post(
        "/api/ap/solicitacoes/cancelamento",
        headers=headers,
        json={"solicitacaoId": "7712301:HP", "motivo": "  "},
    )
    assert sem_motivo.status_code == 400

    for tipo in ("HP", "CG"):
        resposta = client.post(
            "/api/ap/solicitacoes/cancelamento",
            headers=headers,
            json={"solicitacaoId": f"7712301:{tipo}", "motivo": f"Cancelar {tipo}"},
        )
        assert resposta.status_code == 200, resposta.text

    leitura = client.get("/api/ap/solicitacoes/7712301", headers=headers).json()
    assert leitura["tipo"] == "CANCELADA"
    assert len(leitura["cancelamentos"]) == 2

    duplicado = client.post(
        "/api/ap/solicitacoes/cancelamento",
        headers=headers,
        json={"solicitacaoId": "7712301:HP", "motivo": "De novo"},
    )
    inexistente = client.post(
        "/api/ap/solicitacoes/cancelamento",
        headers=headers,
        json={"solicitacaoId": "9999999:HP", "motivo": "Não existe"},
    )
    assert duplicado.status_code == 409
    assert inexistente.status_code == 404


def test_api_mantem_carga_ap_completa_e_recepcionista_consulta_devolucoes(demo_client):
    headers = token(demo_client, "recepcionista")

    casos = demo_client.get("/api/ap/casos", headers=headers)
    pendentes = demo_client.get("/api/ap/solicitacoes/pendentes", headers=headers)
    rejeicao = demo_client.get("/api/ap/solicitacoes/7712045", headers=headers)
    devolucoes = demo_client.get("/api/ap/devolucoes", headers=headers)

    assert casos.status_code == 200 and len(casos.json()) == 19
    assert pendentes.status_code == 200 and len(pendentes.json()) == 11
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
    assert caso["conferencia"]["solicitacaoId"] == "7712301:HP"
    assert caso["conferencia"]["amostras"] == ["1"]
    assert len(caso["materiais"]) == 1
    assert caso["historico"][0]["usuario"]["login"] == "recepcionista"

    # Nova chamada usa outra sessão HTTP e lê o estado persistido.
    detalhe = client.get(f"/api/ap/casos/{caso['numeroInterno']}", headers=headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["numeroInterno"] == caso["numeroInterno"]
    assert detalhe.json()["solicitacao"]["situacaoRecepcao"] == "RECEBIDA"
    leitura_parcial = client.get("/api/ap/solicitacoes/7712301", headers=headers).json()
    assert leitura_parcial["tipo"] == "PENDENTE"
    assert [item["id"] for item in leitura_parcial["exames"]] == ["7712301:CG"]

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


def test_tipo_divergente_retorna_detail_e_nao_persiste(client):
    headers = token(client, "recepcionista")
    payload = entrada(tipo="CG")
    resposta = client.post("/api/ap/recebimentos", headers=headers, json=payload)

    assert resposta.status_code == 422
    assert resposta.json()["detail"]
    assert client.get("/api/ap/casos", headers=headers).json() == []
    assert client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json() == 7


def test_nao_conformidade_cria_devolucao_e_atualiza_solicitacao_atomicamente(client):
    headers = token(client, "recepcionista")
    payload = {
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:HP", "7712301:CG"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": True,
        "observacao": "Identificação fictícia ilegível nas etiquetas.",
        "responsavel": {"login": "falso", "nome": "Usuário falso"},
    }
    resposta = client.post("/api/ap/nao-conformidades", headers=headers, json=payload)

    assert resposta.status_code == 201, resposta.text
    devolucao = resposta.json()
    assert devolucao["rejeicaoNaRecepcao"] is True
    assert devolucao["naoConformidade"]["registradoPor"]["login"] == "recepcionista"
    leitura = client.get("/api/ap/solicitacoes/7712301", headers=headers).json()
    assert leitura["tipo"] == "DEVOLVIDA"
    assert leitura["tipoNaoConformidade"] == "IDENTIFICACAO_ILEGIVEL"
    grupos = client.get("/api/ap/solicitacoes/7712301/exames", headers=headers).json()
    assert {item["situacaoRecepcao"] for item in grupos} == {"DEVOLVIDA"}

    auditoria = client.get("/api/ap/auditoria", headers=token(client, "recepcao-coordenacao")).json()
    evento = next(item for item in auditoria if item["acao"] == "NAO_CONFORMIDADE_DEVOLUCAO")
    assert evento["usuario"]["login"] == "recepcionista"
    assert evento["dadosNovos"]["situacaoDevolucao"] == "AGUARDANDO_NOVA_AMOSTRA"


def test_nao_conformidade_em_caso_muda_status_e_registra_historico(client):
    headers = token(client, "recepcionista")
    caso = receber(client)
    resposta = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "CASO", "casoNumero": caso["numeroInterno"]},
        "tipo": "EXAME_NAO_CORRESPONDE_MATERIAL",
        "observacao": "Material fictício incompatível.",
        "novaAmostraSolicitada": False,
    })

    assert resposta.status_code == 201, resposta.text
    detalhe = client.get(f"/api/ap/casos/{caso['numeroInterno']}", headers=headers).json()
    assert detalhe["status"] == "DEVOLVIDO"
    assert len(detalhe["naoConformidades"]) == 1
    assert len(detalhe["devolucoes"]) == 1
    assert [item["evento"] for item in detalhe["historico"]][-2:] == ["NAO_CONFORMIDADE", "DEVOLUCAO"]


def test_rejeicao_regularizada_reabre_grupo_preserva_metadados_e_associa_novo_caso(client):
    headers = token(client, "recepcionista")
    rejeicao = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:HP"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": True,
        "observacao": "Etiqueta fictícia ilegível.",
    })
    assert rejeicao.status_code == 201, rejeicao.text
    devolucao = rejeicao.json()
    alterada = client.patch(
        f"/api/ap/devolucoes/{devolucao['id']}/situacao",
        headers=headers,
        json={"situacao": "NOVA_AMOSTRA_RECEBIDA"},
    )
    assert alterada.status_code == 200, alterada.text

    pendentes = client.get("/api/ap/solicitacoes/pendentes", headers=headers).json()
    grupo_pendente = next(item for item in pendentes if item["id"] == "7712301:HP")
    meta = grupo_pendente["devolucaoRegularizada"]
    assert grupo_pendente["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"
    assert meta["id"] == devolucao["id"]
    assert meta["devolvidaEm"] == devolucao["devolvidaEm"]
    auditoria = client.get("/api/ap/auditoria", headers=token(client, "recepcao-coordenacao")).json()
    evento_auditoria = next(item for item in auditoria if item["acao"] == "DEVOLUCAO_SITUACAO_ATUALIZADA")
    assert evento_auditoria["dadosAnteriores"]["solicitacoes"][0]["situacaoRecepcao"] == "DEVOLVIDA"
    assert evento_auditoria["dadosNovos"]["solicitacoes"][0]["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"
    assert evento_auditoria["ipOrigem"] == "testclient"

    for codigo in ("7712301", "7712301-1", "7712301001"):
        leitura = client.get(f"/api/ap/solicitacoes/{codigo}", headers=headers).json()
        assert leitura["tipo"] == "PENDENTE"
        grupo = next(item for item in leitura["exames"] if item["id"] == "7712301:HP")
        assert grupo["devolucaoRegularizada"]["id"] == devolucao["id"]

    caso = client.post("/api/ap/recebimentos", headers=headers, json=entrada("7712301:HP", "HP"))
    assert caso.status_code == 201, caso.text
    detalhe = client.get(f"/api/ap/casos/{caso.json()['numeroInterno']}", headers=headers).json()
    assert len(detalhe["naoConformidades"]) == 1
    assert len(detalhe["devolucoes"]) == 1
    assert any(evento["evento"] == "FLUXO_REABERTO" for evento in detalhe["historico"])
    assert detalhe["devolucoes"][0]["devolvidaEm"] == devolucao["devolvidaEm"]


def test_regularizacao_reabre_caso_devolvido_no_estado_anterior(client):
    headers = token(client, "recepcionista")
    caso_original = receber(client)
    rejeicao = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "CASO", "casoNumero": caso_original["numeroInterno"]},
        "tipo": "EXAME_NAO_CORRESPONDE_MATERIAL",
        "novaAmostraSolicitada": True,
    })
    assert rejeicao.status_code == 201, rejeicao.text
    devolucao = rejeicao.json()
    reaberta = client.patch(
        f"/api/ap/devolucoes/{devolucao['id']}/situacao",
        headers=headers,
        json={"situacao": "NOVA_AMOSTRA_RECEBIDA"},
    )
    assert reaberta.status_code == 200, reaberta.text
    detalhe = client.get(f"/api/ap/casos/{caso_original['numeroInterno']}", headers=headers).json()
    assert detalhe["status"] == "RECEBIDO"
    assert [evento["evento"] for evento in detalhe["historico"]][-1] == "FLUXO_REABERTO"


def test_regularizacao_ihq_associa_historico_ao_caso_de_origem(client):
    headers = token(client, "recepcionista")
    caso = receber(client)
    rejeicao = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712356:IHQ"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": True,
    })
    assert rejeicao.status_code == 201, rejeicao.text
    devolucao = rejeicao.json()
    regularizada = client.patch(
        f"/api/ap/devolucoes/{devolucao['id']}/situacao",
        headers=headers,
        json={"situacao": "NOVA_AMOSTRA_RECEBIDA"},
    )
    assert regularizada.status_code == 200, regularizada.text
    vinculada = client.post("/api/ap/recebimentos/ihq", headers=headers, json={
        "solicitacaoId": "7712356:IHQ",
        "casoOrigemNumero": caso["numeroInterno"],
        "divergenciaConfirmada": True,
    })
    assert vinculada.status_code == 201, vinculada.text
    assert any(
        exame["tipo"] == "IHQ" and exame["codigoInterno"] == vinculada.json()["ihq"]["codigoInternoIhq"]
        for exame in vinculada.json()["caso"]["examesDerivados"]
    )
    detalhe = client.get(f"/api/ap/casos/{caso['numeroInterno']}", headers=headers).json()
    assert len(detalhe["naoConformidades"]) == 1
    assert len(detalhe["devolucoes"]) == 1
    assert any(evento["evento"] == "FLUXO_REABERTO" for evento in detalhe["historico"])


def test_devolucao_de_multiplos_grupos_fica_associada_a_cada_caso_criado(client):
    headers = token(client, "recepcionista")
    rejeicao = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:HP", "7712301:CG"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": True,
    })
    assert rejeicao.status_code == 201, rejeicao.text
    devolucao = rejeicao.json()
    reaberta = client.patch(
        f"/api/ap/devolucoes/{devolucao['id']}/situacao",
        headers=headers,
        json={"situacao": "NOVA_AMOSTRA_RECEBIDA"},
    )
    assert reaberta.status_code == 200, reaberta.text

    casos = [
        client.post("/api/ap/recebimentos", headers=headers, json=entrada("7712301:HP", "HP")).json(),
        client.post("/api/ap/recebimentos", headers=headers, json=entrada("7712301:CG", "CG")).json(),
    ]
    for caso in casos:
        detalhe = client.get(f"/api/ap/casos/{caso['numeroInterno']}", headers=headers).json()
        assert len(detalhe["naoConformidades"]) == 1
        assert len(detalhe["devolucoes"]) == 1
        assert any(evento["evento"] == "FLUXO_REABERTO" for evento in detalhe["historico"])


def test_regressao_da_devolucao_e_bloqueada_apos_receber_ou_cancelar_grupo(client):
    headers = token(client, "recepcionista")
    rejeicao = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:HP"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": True,
    })
    devolucao_id = rejeicao.json()["id"]
    client.patch(f"/api/ap/devolucoes/{devolucao_id}/situacao", headers=headers, json={"situacao": "NOVA_AMOSTRA_RECEBIDA"})
    assert client.post("/api/ap/recebimentos", headers=headers, json=entrada("7712301:HP", "HP")).status_code == 201
    regressao = client.patch(
        f"/api/ap/devolucoes/{devolucao_id}/situacao",
        headers=headers,
        json={"situacao": "AGUARDANDO_NOVA_AMOSTRA"},
    )
    assert regressao.status_code == 409

    rejeicao_cancelada = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:CG"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": True,
    })
    devolucao_cancelada_id = rejeicao_cancelada.json()["id"]
    client.patch(f"/api/ap/devolucoes/{devolucao_cancelada_id}/situacao", headers=headers, json={"situacao": "NOVA_AMOSTRA_RECEBIDA"})
    cancelamento = client.post("/api/ap/solicitacoes/cancelamento", headers=token(client, "recepcao-coordenacao"), json={
        "solicitacaoId": "7712301:CG",
        "motivo": "Cancelamento após a regularização",
    })
    assert cancelamento.status_code == 200
    regressao_cancelada = client.patch(
        f"/api/ap/devolucoes/{devolucao_cancelada_id}/situacao",
        headers=headers,
        json={"situacao": "AGUARDANDO_NOVA_AMOSTRA"},
    )
    assert regressao_cancelada.status_code == 409


def test_devolucao_encerrada_nao_pode_ser_reaberta(client):
    headers = token(client, "recepcionista")
    rejeicao = client.post("/api/ap/nao-conformidades", headers=headers, json={
        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:HP"]},
        "tipo": "IDENTIFICACAO_ILEGIVEL",
        "novaAmostraSolicitada": False,
    })
    assert rejeicao.status_code == 201, rejeicao.text
    resposta = client.patch(
        f"/api/ap/devolucoes/{rejeicao.json()['id']}/situacao",
        headers=headers,
        json={"situacao": "NOVA_AMOSTRA_RECEBIDA"},
    )
    assert resposta.status_code == 409
    grupos = client.get("/api/ap/solicitacoes/7712301/exames", headers=headers).json()
    grupo = next(item for item in grupos if item["id"] == "7712301:HP")
    assert grupo["situacaoRecepcao"] == "DEVOLVIDA"


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
    caso = receber(client, "7712340:CO", "CO")
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


def test_ihq_com_hp_pendente_exige_hp_recebido_na_conferencia(client):
    headers = token(client, "recepcionista")
    hp_id = criar_grupo_hp_para_ihq(client)
    caso_de_outra_solicitacao = receber(client)
    corpo_ihq = {
        "solicitacaoId": "7712356:IHQ",
        "casoOrigemNumero": caso_de_outra_solicitacao["numeroInterno"],
    }

    antes_do_hp = client.post("/api/ap/recebimentos/ihq", headers=headers, json=corpo_ihq)
    assert antes_do_hp.status_code == 422
    assert "Receba o HP" in antes_do_hp.json()["detail"]

    hp = receber(client, hp_id, "HP")
    recebida = client.post(
        "/api/ap/recebimentos/ihq",
        headers=headers,
        json={**corpo_ihq, "casoOrigemNumero": hp["numeroInterno"]},
    )
    assert recebida.status_code == 201, recebida.text
    assert recebida.json()["solicitacao"]["ihqCasoNumero"] == hp["numeroInterno"]


def test_ihq_com_hp_recebido_recusa_origem_de_outra_solicitacao(client):
    headers = token(client, "recepcionista")
    hp_id = criar_grupo_hp_para_ihq(client)
    hp_da_solicitacao = receber(client, hp_id, "HP")
    outro_hp = receber(client)

    recusada = client.post(
        "/api/ap/recebimentos/ihq",
        headers=headers,
        json={
            "solicitacaoId": "7712356:IHQ",
            "casoOrigemNumero": outro_hp["numeroInterno"],
        },
    )
    assert recusada.status_code == 422
    assert "HP da mesma" in recusada.json()["detail"]

    aceita = client.post(
        "/api/ap/recebimentos/ihq",
        headers=headers,
        json={
            "solicitacaoId": "7712356:IHQ",
            "casoOrigemNumero": hp_da_solicitacao["numeroInterno"],
        },
    )
    assert aceita.status_code == 201, aceita.text
    assert aceita.json()["solicitacao"]["ihqCasoNumero"] == hp_da_solicitacao["numeroInterno"]


def test_ihq_sem_hp_na_solicitacao_permite_origem_manual(client):
    headers = token(client, "recepcionista")
    caso_existente = receber(client)

    resposta = client.post(
        "/api/ap/recebimentos/ihq",
        headers=headers,
        json={
            "solicitacaoId": "7712356:IHQ",
            "casoOrigemNumero": caso_existente["numeroInterno"],
            "divergenciaConfirmada": True,
        },
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["solicitacao"]["ihqCasoNumero"] == caso_existente["numeroInterno"]


def test_ihq_manual_preserva_permissoes_e_impressao_nao_tem_endpoint(client):
    headers = token(client, "recepcionista")
    caso = receber(client)
    entrada_ihq = {
        "solicitacaoId": "7712356:IHQ",
        "casoOrigemNumero": caso["numeroInterno"],
        "divergenciaConfirmada": True,
    }
    ihq = client.post("/api/ap/recebimentos/ihq", headers=headers, json=entrada_ihq)
    assert ihq.status_code == 201, ihq.text
    assert ihq.json()["ihq"]["solicitacaoAghuCodigo"] == "7712356"
    dados_etiqueta = ihq.json()["solicitacao"]
    assert dados_etiqueta["tipoExameSugerido"] == "IHQ"
    assert dados_etiqueta["situacaoRecepcao"] == "RECEBIDA"
    assert dados_etiqueta["amostras"]
    assert dados_etiqueta["ihqCodigo"] == ihq.json()["ihq"]["codigoInternoIhq"]
    assert dados_etiqueta["ihqCasoNumero"] == caso["numeroInterno"]
    assert ihq.json()["ihq"]["codigoInternoIhq"] != caso["numeroInterno"]

    impressao = client.post("/api/ap/casos/impressoes", headers=headers, json={
        "numeroInterno": caso["numeroInterno"], "tipo": "ETIQUETAS", "amostras": ["1"],
    })
    assert impressao.status_code == 405
    assert all(
        evento["evento"] not in {"ETIQUETAS_IMPRESSAS", "FICHA_IMPRESSA"}
        for evento in ihq.json()["caso"]["historico"]
    )

    for username in [nome for nome in PERFIS_MOCK if nome != "recepcionista"]:
        assert client.post("/api/ap/recebimentos/ihq", headers=token(client, username), json=entrada_ihq).status_code == 403
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
    assert client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json() == 7


# ---------------------------------------------------------------------------
# Testes de leitura de código de barras AGHU de 10 dígitos
# ---------------------------------------------------------------------------


def test_leitura_10_digitos_decompoe_e_retorna_pendente_com_metadados(client):
    """Código contínuo de 10 dígitos: 7712301 + amostra 001 → solicitação PENDENTE com amostraBipada."""
    headers = token(client, "recepcionista")
    # Amostra "1" pertence ao grupo HP da solicitação 7712301
    leitura = client.get("/api/ap/solicitacoes/7712301001", headers=headers).json()
    assert leitura["tipo"] == "PENDENTE"
    assert leitura["codigoSolicitacao"] == "7712301"
    assert leitura["amostraBipada"] == "001"
    assert leitura["grupoSelecionadoId"] == "7712301:HP"
    assert len(leitura["examesFiltrados"]) == 1
    assert leitura["examesFiltrados"][0]["id"] == "7712301:HP"
    # Todos os exames pendentes continuam na resposta (retrocompatibilidade)
    assert len(leitura["exames"]) == 2


def test_leitura_10_digitos_tolerante_zeros_a_esquerda(client):
    """Amostra "002" na etiqueta corresponde à amostra "2" do grupo CG."""
    headers = token(client, "recepcionista")
    leitura = client.get("/api/ap/solicitacoes/7712301002", headers=headers).json()
    assert leitura["tipo"] == "PENDENTE"
    assert leitura["amostraBipada"] == "002"
    assert leitura["grupoSelecionadoId"] == "7712301:CG"
    assert leitura["examesFiltrados"][0]["id"] == "7712301:CG"


def test_leitura_10_digitos_amostra_inexistente_retorna_pendente_sem_filtro(client):
    """Amostra "099" inexistente: solicitação encontrada, mas sem filtro de grupo."""
    headers = token(client, "recepcionista")
    leitura = client.get("/api/ap/solicitacoes/7712301099", headers=headers).json()
    assert leitura["tipo"] == "PENDENTE"
    assert leitura["amostraBipada"] == "099"
    assert leitura["grupoSelecionadoId"] is None
    assert leitura["examesFiltrados"] == []


def test_leitura_10_digitos_codigo_inexistente_retorna_nao_encontrada(client):
    """10 dígitos cujos primeiros 7 não existem: retorna NAO_ENCONTRADA."""
    headers = token(client, "recepcionista")
    leitura = client.get("/api/ap/solicitacoes/9999999001", headers=headers).json()
    assert leitura["tipo"] == "NAO_ENCONTRADA"


def test_leitura_10_digitos_amostra_ja_recebida_com_outro_pendente(client):
    """Bipa amostra "1" (HP) já recebida; grupo CG continua pendente → PENDENTE + amostraBipadaSituacao."""
    headers = token(client, "recepcionista")
    # Receber HP (amostra 1) primeiro
    receber(client, "7712301:HP", "HP")

    leitura = client.get("/api/ap/solicitacoes/7712301001", headers=headers).json()
    assert leitura["tipo"] == "PENDENTE"
    assert leitura["amostraBipada"] == "001"
    # O grupo HP já foi recebido, logo grupoSelecionadoId é None
    assert leitura["grupoSelecionadoId"] is None
    assert leitura["examesFiltrados"] == []
    assert leitura["amostraBipadaSituacao"] is not None
    assert leitura["amostraBipadaSituacao"]["situacaoRecepcao"] == "RECEBIDA"
    assert leitura["amostraBipadaSituacao"]["tipoExame"] == "HP"
    # O grupo CG pendente permanece em exames
    assert len(leitura["exames"]) == 1
    assert leitura["exames"][0]["id"] == "7712301:CG"


def test_leitura_codigo_puro_e_hifen_continuam_funcionando(client):
    """Retrocompatibilidade: código puro e código-amostra preservam comportamento existente."""
    headers = token(client, "recepcionista")
    # Código puro (7 dígitos)
    puro = client.get("/api/ap/solicitacoes/7712301", headers=headers).json()
    assert puro["tipo"] == "PENDENTE"
    assert "amostraBipada" not in puro

    # Formato código-amostra com hífen
    hifen = client.get("/api/ap/solicitacoes/7712301-1", headers=headers).json()
    assert hifen["tipo"] == "PENDENTE"
    assert hifen["amostraBipada"] == "1"
    assert hifen["grupoSelecionadoId"] == "7712301:HP"

    # Formato chave de grupo com :TIPO
    chave = client.get("/api/ap/solicitacoes/7712301:HP", headers=headers).json()
    assert chave["tipo"] == "PENDENTE"
    assert "amostraBipada" not in chave


def test_recebimento_concorrente_nao_gera_numero_interno_duplicado(client):
    headers = token(client, "recepcionista")
    payloads = [entrada("7712301:HP"), entrada("7712301:HP")]

    def enviar(payload):
        return client.post("/api/ap/recebimentos", headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        respostas = list(executor.map(enviar, payloads))

    assert sorted(resposta.status_code for resposta in respostas) == [201, 409]
    assert len(client.get("/api/ap/casos", headers=headers).json()) == 1
    assert client.get("/api/ap/solicitacoes/pendentes/contagem", headers=headers).json() == 7


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
                assert await provider.contar_solicitacoes_pendentes() == 7

                solicitacao = await provider.buscar_solicitacao(fixture[0]["id"])
                solicitacao["situacaoRecepcao"] = "RECEBIDA"
                await provider.salvar_solicitacao(solicitacao)
                await provider.seed_solicitacoes(fixture)
                persistida = await provider.buscar_solicitacao(fixture[0]["id"])
                assert persistida["situacaoRecepcao"] == "RECEBIDA"
                assert await provider.listar_exames_da_solicitacao("7712301")
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
                assert await provider.contar_solicitacoes_pendentes() == 8
                assert len(await provider.listar_devolucoes()) == 3
                solicitacao = await provider.buscar_solicitacao("7712301:HP")
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

                assert await provider.contar_solicitacoes_pendentes() == 7
                assert await provider.listar_casos() == []
                event.remove(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)

                event.listen(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)
                with pytest.raises(RuntimeError, match="Falha simulada"):
                    await controller.cancelar_exame_solicitacao(
                        "7712301:CG",
                        "Exame dispensado",
                        {"username": "recepcao-coordenacao"},
                        "192.0.2.10",
                    )
                assert (await provider.buscar_solicitacao("7712301:CG"))["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"
                assert await provider.contar_solicitacoes_pendentes() == 7
                event.remove(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)

                devolucao = await controller.registrar_nao_conformidade(
                    {
                        "contexto": {"tipo": "SOLICITACAO", "solicitacaoIds": ["7712301:HP"]},
                        "tipo": "IDENTIFICACAO_ILEGIVEL",
                        "novaAmostraSolicitada": True,
                    },
                    {"username": "recepcionista", "displayName": ["Recepcionista SAP"]},
                    "192.0.2.10",
                )
                event.listen(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)
                with pytest.raises(RuntimeError, match="Falha simulada"):
                    await controller.atualizar_situacao_devolucao(
                        devolucao["id"],
                        "NOVA_AMOSTRA_RECEBIDA",
                        {"username": "recepcionista", "displayName": ["Recepcionista SAP"]},
                        "192.0.2.10",
                    )
                event.remove(session.sync_session, "before_commit", falhar_ao_confirmar_auditoria)
                assert (await provider.buscar_solicitacao("7712301:HP"))["situacaoRecepcao"] == "DEVOLVIDA"
                devolucoes = await provider.listar_devolucoes()
                assert next(item for item in devolucoes if item["id"] == devolucao["id"])["situacao"] == "AGUARDANDO_NOVA_AMOSTRA"
        finally:
            await engine.dispose()

    asyncio.run(executar())
