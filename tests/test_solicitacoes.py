# tests/test_solicitacoes.py
"""Testes do módulo de solicitações AGHU usando APENAS o CSV fictício de fixtures."""
import os

import pandas as pd
import pytest

from src.main import app
from src.auth.auth import auth_handler
from src.dependencies import _get_solicitacao_csv_provider
from src.providers.implementations import solicitacao_csv_provider as provider_module
from src.providers.implementations.solicitacao_csv_provider import SolicitacaoCsvProvider
from src.controllers.solicitacao_controller import _mapear_linha

FIXTURE_CSV = os.path.join(os.path.dirname(__file__), "fixtures", "solicitacoes_teste.csv")


@pytest.fixture
def api(client):
    """TestClient com o provedor de solicitações apontando para o CSV fictício."""
    provider = SolicitacaoCsvProvider(csv_path=FIXTURE_CSV)
    app.dependency_overrides[_get_solicitacao_csv_provider] = lambda: provider
    yield client
    app.dependency_overrides.pop(_get_solicitacao_csv_provider, None)


@pytest.fixture
def headers():
    """Cabeçalho Authorization com um token de acesso válido."""
    token = auth_handler.create_access_token({"username": "admin"})
    return {"Authorization": f"Bearer {token}"}


def test_mapeamento_de_uma_linha(api, headers):
    """Uma linha do CSV vira um SolicitacaoAghu em camelCase com os campos convertidos."""
    resp = api.get("/api/solicitacoes/900002", headers=headers)
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) == 1
    item = itens[0]
    assert item["id"] == "900002-1"
    assert item["codigoSolicitacao"] == "900002"
    assert item["prontuario"] == "0000002"
    assert item["nomePaciente"] == "PACIENTE TESTE DOIS"
    assert item["dataNascimento"] == "1975-07-01"
    assert item["dataSolicitacao"] == "2026-02-20"
    assert item["origem"] == "INTERNACAO"
    assert item["tipoExameSugerido"] == "CG"
    assert item["siglaExame"] == "CITOP"
    assert item["statusAghuDescricao"] == "A EXECUTAR"
    assert item["situacaoRecepcao"] == "AGUARDANDO_RECEBIMENTO"
    assert item["sexo"] is None
    assert item["nomeSolicitante"] is None
    assert item["informacoesClinicas"] == "Linha fictícia um\nlinha fictícia dois"
    assert item["numeroAmostra"] == "1"
    assert item["codigoLab"] == "LAB1"
    assert item["convenio"] == "SUS"


def test_mapeia_revisao_por_sigla_ou_nome_do_exame():
    linha = {
        "sigla_exame": "REVLA",
        "codigo_solicitacao": "900010",
        "numero_amostra": "1",
        "nome_exame": "REVISÃO DE LÂMINA",
    }

    resultado = _mapear_linha(linha)

    assert resultado is not None
    assert resultado["tipoExameSugerido"] == "REVISAO"


def test_origens_mapeadas(api, headers):
    """As quatro origens do AGHU são convertidas para os códigos do SAP."""
    itens = api.get("/api/solicitacoes", headers=headers).json()
    origens = {i["codigoSolicitacao"]: i["origem"] for i in itens}
    assert origens["900001"] == "AMBULATORIO"
    assert origens["900002"] == "INTERNACAO"
    assert origens["900003"] == "CIRURGIA"
    assert origens["900004"] == "EXTERNO"


def test_lista_ignora_sigla_fora_do_mapa_e_ordena_desc(api, headers):
    """Siglas fora do mapa são descartadas e a lista vem da mais recente para a mais antiga."""
    resp = api.get("/api/solicitacoes", headers=headers)
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) == 8
    assert all(i["siglaExame"] != "HEMOG" for i in itens)
    datas = [i["dataSolicitacao"] for i in itens]
    assert datas == sorted(datas, reverse=True)
    assert itens[0]["codigoSolicitacao"] == "900006"


def test_filtro_por_periodo(api, headers):
    """O filtro por período é inclusivo nas duas pontas."""
    resp = api.get(
        "/api/solicitacoes",
        params={"data_inicio": "2026-02-20", "data_fim": "2026-04-15"},
        headers=headers,
    )
    assert resp.status_code == 200
    codigos = {i["codigoSolicitacao"] for i in resp.json()}
    assert codigos == {"900002", "900003", "900004"}


def test_filtro_por_tipo(api, headers):
    """O filtro por tipo devolve só os itens daquele tipo."""
    itens = api.get("/api/solicitacoes", params={"tipo": "HP"}, headers=headers).json()
    assert {i["codigoSolicitacao"] for i in itens} == {"900001", "900006"}
    assert all(i["tipoExameSugerido"] == "HP" for i in itens)


def test_limite(api, headers):
    """O parâmetro limite corta a lista e valores acima de 1000 são rejeitados."""
    itens = api.get("/api/solicitacoes", params={"limite": 2}, headers=headers).json()
    assert len(itens) == 2
    assert {i["codigoSolicitacao"] for i in itens} == {"900006", "900004"}
    resp = api.get("/api/solicitacoes", params={"limite": 1001}, headers=headers)
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_limite_conta_solicitacoes_sem_cortar_amostras(api, headers):
    """O limite conta solicitações distintas e devolve todas as amostras de cada uma."""
    itens = api.get("/api/solicitacoes", params={"limite": 5}, headers=headers).json()
    codigos = {i["codigoSolicitacao"] for i in itens}
    assert codigos == {"900006", "900004", "900003", "900002", "900001"}
    assert sorted(i["numeroAmostra"] for i in itens if i["codigoSolicitacao"] == "900001") == ["1", "2"]


def test_unidade_sem_caractere_invisivel(api, headers):
    """A unidade vem sem zero-width space nem espaços nas pontas."""
    itens = api.get("/api/solicitacoes/900007", headers=headers).json()
    assert len(itens) == 2
    assert all(i["unidade"] == "UNIDADE TESTE G" for i in itens)
    assert {i["codStatusItem"] for i in itens} == {"LI", "AC"}


def test_ids_unicos_na_lista(api, headers):
    """Cada registro tem id "<codigo>-<amostra>" único, mesmo com código repetido."""
    itens = api.get("/api/solicitacoes", headers=headers).json()
    ids = [i["id"] for i in itens]
    assert len(ids) == len(set(ids))
    assert all(i["id"] == f'{i["codigoSolicitacao"]}-{i["numeroAmostra"]}' for i in itens)


def test_solicitacao_com_duas_amostras_pelo_codigo(api, headers):
    """Pelo código da solicitação, retorna todas as amostras."""
    resp = api.get("/api/solicitacoes/900001", headers=headers)
    assert resp.status_code == 200
    itens = resp.json()
    assert {i["id"] for i in itens} == {"900001-1", "900001-2"}
    assert {i["codigoSolicitacao"] for i in itens} == {"900001"}
    assert sorted(i["tipoExameSugerido"] for i in itens) == ["HP", "IHQ"]


def test_solicitacao_pelo_id_composto(api, headers):
    """Pelo id composto, retorna só aquela amostra."""
    resp = api.get("/api/solicitacoes/900001-2", headers=headers)
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) == 1
    assert itens[0]["id"] == "900001-2"
    assert itens[0]["numeroAmostra"] == "2"
    assert itens[0]["tipoExameSugerido"] == "IHQ"


def test_solicitacao_inexistente_retorna_404(api, headers):
    """Código/id inexistente (ou só com siglas fora do mapa) retorna 404 com detail."""
    for codigo in ("999999", "900005", "900001-9", "999999-1"):
        resp = api.get(f"/api/solicitacoes/{codigo}", headers=headers)
        assert resp.status_code == 404
        assert "detail" in resp.json()


def test_rotas_exigem_autenticacao(api):
    """Sem token, as rotas de solicitações retornam 401."""
    assert api.get("/api/solicitacoes").status_code == 401
    assert api.get("/api/solicitacoes/900001").status_code == 401


@pytest.mark.asyncio
async def test_provider_le_o_csv_uma_unica_vez(monkeypatch):
    """O CSV é lido só na construção do provedor, não a cada consulta."""
    chamadas = {"n": 0}
    original = pd.read_csv

    def read_csv_contado(*args, **kwargs):
        chamadas["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(provider_module.pd, "read_csv", read_csv_contado)
    provider = SolicitacaoCsvProvider(csv_path=FIXTURE_CSV)
    await provider.listar_solicitacoes()
    await provider.listar_solicitacoes()
    await provider.obter_itens_por_codigo("900001")
    assert chamadas["n"] == 1
