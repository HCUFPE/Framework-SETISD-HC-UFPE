"""
Testes de API da Fila de Exames: listagem, detalhe, vinculação e busca ativa (TASK-010)
======================================================================================
"""

from datetime import datetime, timedelta, timezone

from tests.fila_fixtures import FilaApi, fila_api  # noqa: F401 - fixture

CAMPOS_ITEM_FILA = {
    "id", "codigoSolicitacao", "codigoExame", "nomeExame", "prontuario", "nomePaciente",
    "telefoneContato", "municipio", "regiaoGeografica", "utilizaTfd", "unidadeSolicitante",
    "dataSolicitacao", "dataRetornoMedico", "statusHigienizacao", "statusOperacional",
    "scorePrioridade", "motivosPrioridade", "alertas", "contatoIniciadoEm", "prazoConfirmacaoEm",
    "dataAgendadaAghu", "preparoOrientado",
}


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fila_basica(api: FilaApi) -> tuple[int, int]:
    """Insere um item de rotina (mais antigo) e um da Oncologia (mais recente)."""
    rotina = api.inserir(codigo_solicitacao="900011", codigo_exame="USAX", prontuario="3003",
                         unidade_solicitante="AMBULATORIO GERAL", nome_paciente="ANA ANONIMIZADA TRES",
                         municipio="OLINDA", regiao_geografica="RMR")
    onco = api.inserir(codigo_solicitacao="900010", codigo_exame="USAX", prontuario="2002",
                       unidade_solicitante="ONCOLOGIA CLINICA", nome_paciente="JOSE ANONIMIZADO DOIS")
    return rotina, onco


# ---------------------------------------------------------------------------
# Segurança
# ---------------------------------------------------------------------------


def test_rotas_exigem_token(fila_api: FilaApi) -> None:
    for metodo, rota in [("get", "/api/exames/fila"), ("get", "/api/exames/fila/1"),
                         ("patch", "/api/exames/fila/1/status"), ("get", "/api/exames/aghu/buscar?prontuario=1")]:
        resposta = getattr(fila_api.client, metodo)(rota)
        assert resposta.status_code == 401, rota


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------


def test_fila_ordenada_com_contrato_camel_case(fila_api: FilaApi) -> None:
    rotina, onco = _fila_basica(fila_api)
    resposta = fila_api.client.get("/api/exames/fila", headers=fila_api.headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert [i["id"] for i in corpo] == [onco, rotina]
    assert set(corpo[0]) == CAMPOS_ITEM_FILA
    assert corpo[0]["motivosPrioridade"][0] == "Oncologia +100"
    assert corpo[0]["nomeExame"] == "ULTRASSONOGRAFIA DE ABDOME TOTAL"
    assert corpo[0]["dataSolicitacao"].startswith("2026-11-20")
    assert resposta.headers["X-Total-Count"] == "2"


def test_itens_finalizados_e_nao_validos_ficam_fora_por_padrao(fila_api: FilaApi) -> None:
    ativo = fila_api.inserir(codigo_solicitacao="1")
    fila_api.inserir(codigo_solicitacao="2", status_operacional="CONFIRMADO_AGENDADO_AGHU",
                     data_agendada_aghu=_agora() + timedelta(days=3))
    fila_api.inserir(codigo_solicitacao="3", status_operacional="CANCELADO")
    fila_api.inserir(codigo_solicitacao="4", status_higienizacao="NAO_ENCONTRADA")
    excluido = fila_api.inserir(codigo_solicitacao="5", deleted_at=_agora())

    ids = [i["id"] for i in fila_api.client.get("/api/exames/fila", headers=fila_api.headers).json()]
    assert ids == [ativo]
    assert excluido not in ids

    confirmados = fila_api.client.get(
        "/api/exames/fila?status_operacional=CONFIRMADO_AGENDADO_AGHU", headers=fila_api.headers
    ).json()
    assert [i["codigoSolicitacao"] for i in confirmados] == ["2"]
    nao_encontradas = fila_api.client.get(
        "/api/exames/fila?status_higienizacao=NAO_ENCONTRADA", headers=fila_api.headers
    ).json()
    assert [i["codigoSolicitacao"] for i in nao_encontradas] == ["4"]


def test_filtro_regiao_preserva_score(fila_api: FilaApi) -> None:
    _fila_basica(fila_api)
    completa = {i["id"]: i for i in fila_api.client.get("/api/exames/fila", headers=fila_api.headers).json()}
    filtrada = fila_api.client.get("/api/exames/fila?regiao=CAPITAL", headers=fila_api.headers).json()
    assert len(filtrada) == 1 and filtrada[0]["regiaoGeografica"] == "CAPITAL"
    for item in filtrada:
        assert item["scorePrioridade"] == completa[item["id"]]["scorePrioridade"]
        assert item["motivosPrioridade"] == completa[item["id"]]["motivosPrioridade"]


def test_filtros_tfd_busca_e_exame(fila_api: FilaApi) -> None:
    rotina, onco = _fila_basica(fila_api)
    tfd = fila_api.inserir(codigo_solicitacao="7", codigo_exame="INR", utiliza_tfd=True,
                           municipio="PESQUEIRA", regiao_geografica="INTERIOR")
    get = lambda q: [i["id"] for i in fila_api.client.get(f"/api/exames/fila?{q}", headers=fila_api.headers).json()]
    assert get("apenas_tfd=true") == [tfd]
    assert get("busca=3003") == [rotina]
    assert get("busca=jose") == [onco]
    assert get("codigo_exame=INR") == [tfd]
    assert get("municipio=olinda") == [rotina]


def test_apenas_24h_vencidos(fila_api: FilaApi) -> None:
    agora = _agora()
    vencido = fila_api.inserir(codigo_solicitacao="1", status_operacional="AGUARDANDO_CONFIRMACAO_24H",
                               contato_iniciado_em=agora - timedelta(hours=25),
                               prazo_confirmacao_em=agora - timedelta(hours=1))
    fila_api.inserir(codigo_solicitacao="2", status_operacional="AGUARDANDO_CONFIRMACAO_24H",
                     contato_iniciado_em=agora, prazo_confirmacao_em=agora + timedelta(hours=23))
    fila_api.inserir(codigo_solicitacao="3")
    corpo = fila_api.client.get("/api/exames/fila?apenas_24h_vencidos=true", headers=fila_api.headers).json()
    assert [i["id"] for i in corpo] == [vencido]
    assert "PRAZO_24H_VENCIDO" in {a["tipo"] for a in corpo[0]["alertas"]}


def test_paginacao_com_total(fila_api: FilaApi) -> None:
    for n in range(3):
        fila_api.inserir(codigo_solicitacao=str(n))
    resposta = fila_api.client.get("/api/exames/fila?limit=2&offset=0", headers=fila_api.headers)
    assert len(resposta.json()) == 2
    assert resposta.headers["X-Total-Count"] == "3"
    segunda = fila_api.client.get("/api/exames/fila?limit=2&offset=2", headers=fila_api.headers)
    assert len(segunda.json()) == 1


def test_parametros_invalidos_retornam_400(fila_api: FilaApi) -> None:
    for q in ["regiao=SERTAO", "status_operacional=XYZ", "limit=0", "offset=-1"]:
        resposta = fila_api.client.get(f"/api/exames/fila?{q}", headers=fila_api.headers)
        assert resposta.status_code == 400, q
        assert "detail" in resposta.json()


def test_listagem_alerta_incompatibilidade_entre_itens_da_fila(fila_api: FilaApi) -> None:
    colono = fila_api.inserir(codigo_solicitacao="900001", codigo_exame="COLONO", prontuario="1001")
    fila_api.inserir(codigo_solicitacao="900002", codigo_exame="HEMO", prontuario="1001")
    corpo = {i["id"]: i for i in fila_api.client.get("/api/exames/fila", headers=fila_api.headers).json()}
    assert "INCOMPATIBILIDADE" in {a["tipo"] for a in corpo[colono]["alertas"]}


# ---------------------------------------------------------------------------
# Detalhe
# ---------------------------------------------------------------------------


def test_detalhe_traz_exames_do_aghu_e_alerta(fila_api: FilaApi) -> None:
    colono = fila_api.inserir(codigo_solicitacao="900001", codigo_exame="COLONO", prontuario="1001",
                              unidade_solicitante="GASTROENTEROLOGIA")
    resposta = fila_api.client.get(f"/api/exames/fila/{colono}", headers=fila_api.headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    outros = corpo["outrosExames"]
    assert [(o["codigoExame"], o["origem"]) for o in outros] == [("HEMO", "AGHU")]
    assert any(a["tipo"] == "INCOMPATIBILIDADE" for a in corpo["alertas"])
    assert "preparo intestinal" in corpo["orientacoesPreparo"]
    assert "Afinidade Clínica Solicitante × Exame +15" in corpo["motivosPrioridade"]


def test_detalhe_inexistente_retorna_404(fila_api: FilaApi) -> None:
    resposta = fila_api.client.get("/api/exames/fila/99999", headers=fila_api.headers)
    assert resposta.status_code == 404
    assert resposta.json()["detail"]


# ---------------------------------------------------------------------------
# Vinculação por busca ativa
# ---------------------------------------------------------------------------


def test_vincular_solicitacao_corrige_item_e_audita(fila_api: FilaApi) -> None:
    item = fila_api.inserir(codigo_solicitacao="81999998888", codigo_exame=None,
                            status_higienizacao="NAO_ENCONTRADA", nome_paciente="PEDRO ANONIMIZADO QUATRO")
    resposta = fila_api.client.patch(
        f"/api/exames/fila/{item}/vincular-solicitacao",
        json={"codigoSolicitacao": "900020", "codigoExame": "INR"},
        headers=fila_api.headers,
    )
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["statusHigienizacao"] == "VALIDA"
    assert corpo["prontuario"] == "4004"
    assert corpo["codigoSolicitacao"] == "900020"

    logs = fila_api.audit_logs()
    assert len(logs) == 1
    assert logs[0]["acao"] == "VINCULAR_SOLICITACAO"
    assert logs[0]["categoria"] == "NEGOCIO_CLINICO"
    assert logs[0]["dados_anteriores"]["codigo_solicitacao"] == "81999998888"
    assert logs[0]["dados_novos"]["status_higienizacao"] == "VALIDA"


def test_vincular_solicitacao_inexistente_retorna_404(fila_api: FilaApi) -> None:
    item = fila_api.inserir(codigo_solicitacao="1", status_higienizacao="NAO_ENCONTRADA")
    resposta = fila_api.client.patch(
        f"/api/exames/fila/{item}/vincular-solicitacao",
        json={"codigoSolicitacao": "123456", "codigoExame": "INR"},
        headers=fila_api.headers,
    )
    assert resposta.status_code == 404
    assert fila_api.item(item).status_higienizacao == "NAO_ENCONTRADA"
    assert fila_api.audit_logs() == []


def test_vincular_gerando_duplicidade_retorna_409(fila_api: FilaApi) -> None:
    fila_api.inserir(codigo_solicitacao="900030", codigo_exame="RXMM1", prontuario="5005")
    item = fila_api.inserir(codigo_solicitacao="1", status_higienizacao="DIVERGENCIA_EXAME")
    resposta = fila_api.client.patch(
        f"/api/exames/fila/{item}/vincular-solicitacao",
        json={"codigoSolicitacao": "900030", "codigoExame": "RXMM1"},
        headers=fila_api.headers,
    )
    assert resposta.status_code == 409


def test_vincular_item_valido_retorna_400(fila_api: FilaApi) -> None:
    item = fila_api.inserir(codigo_solicitacao="1")
    resposta = fila_api.client.patch(
        f"/api/exames/fila/{item}/vincular-solicitacao",
        json={"codigoSolicitacao": "900020", "codigoExame": "INR"},
        headers=fila_api.headers,
    )
    assert resposta.status_code == 400


# ---------------------------------------------------------------------------
# Busca ativa no AGHU
# ---------------------------------------------------------------------------


def test_busca_aghu_por_prontuario_solicitacao_e_nome(fila_api: FilaApi) -> None:
    get = lambda q: fila_api.client.get(f"/api/exames/aghu/buscar?{q}", headers=fila_api.headers)
    por_prontuario = get("prontuario=1001")
    assert por_prontuario.status_code == 200
    assert {r["codigo_exame"] for r in por_prontuario.json()} == {"COLONO", "HEMO"}
    assert [r["codigo_exame"] for r in get("codigo_solicitacao=900020").json()] == ["INR"]
    assert {r["prontuario"] for r in get("nome=anonimizada um").json()} == {"1001"}
    assert get("prontuario=0000").json() == []


def test_busca_aghu_sem_parametros_ou_nome_curto_retorna_400(fila_api: FilaApi) -> None:
    assert fila_api.client.get("/api/exames/aghu/buscar", headers=fila_api.headers).status_code == 400
    assert fila_api.client.get("/api/exames/aghu/buscar?nome=ab", headers=fila_api.headers).status_code == 400
