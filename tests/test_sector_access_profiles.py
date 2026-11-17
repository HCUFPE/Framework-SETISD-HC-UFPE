"""Verificações de autenticação mock e autorização por perfil do Sistema AP."""

from src.auth.authorization import Perfil, Permissao, resolver_permissoes
from src.auth.auth import AuthHandler, MockIdentityProvider


def autenticar(client, usuario: str, senha: str = "demo") -> dict[str, str]:
    resposta = client.post("/api/login", data={"username": usuario, "password": senha})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def test_catalogo_contem_nove_perfis_e_nega_permissoes_desconhecidas():
    assert len(list(Perfil)) == 9
    assert resolver_permissoes(["PERFIL_INEXISTENTE"]) == []
    assert Permissao.DEVOLUCOES_ALTERAR_SITUACAO.value in resolver_permissoes([Perfil.RECEPCIONISTA.value])
    assert Permissao.DEVOLUCOES_ALTERAR_SITUACAO.value in resolver_permissoes([Perfil.COORDENACAO_ADMINISTRADOR.value])
    assert Permissao.DEVOLUCOES_ALTERAR_SITUACAO.value not in resolver_permissoes([Perfil.CITOTECNICO.value])


def test_login_retorna_perfis_e_permissoes_resolvidas(client):
    headers = autenticar(client, "recepcionista")
    resposta = client.get("/api/users/me", headers=headers)

    assert resposta.status_code == 200
    assert resposta.json()["profiles"] == [Perfil.RECEPCIONISTA.value]
    assert Permissao.RECEPCAO_RECEBER.value in resposta.json()["permissions"]
    assert Permissao.DEVOLUCOES_CONSULTAR.value in resposta.json()["permissions"]
    assert Permissao.DEVOLUCOES_ALTERAR_SITUACAO.value in resposta.json()["permissions"]
    assert Permissao.CASOS_CANCELAR.value not in resposta.json()["permissions"]


def test_login_ignora_perfis_e_permissoes_forjados_pelo_cliente(client):
    resposta = client.post("/api/login", data={
        "username": "recepcionista",
        "password": "demo",
        "profiles": Perfil.COORDENACAO_ADMINISTRADOR.value,
        "permissions": Permissao.CASOS_CANCELAR.value,
    })

    assert resposta.status_code == 200
    headers = {"Authorization": f"Bearer {resposta.json()['access_token']}"}
    identidade = client.get("/api/users/me", headers=headers)

    assert identidade.status_code == 200
    assert identidade.json()["profiles"] == [Perfil.RECEPCIONISTA.value]
    assert Permissao.CASOS_CANCELAR.value not in identidade.json()["permissions"]
    assert client.post("/api/ap/casos/cancelamento", headers=headers, json={
        "numeroInterno": "HP-NAO-EXISTE/26",
        "motivo": "Tentativa com permissão forjada",
    }).status_code == 403


def test_identidades_mock_disponibilizam_os_nove_perfis(client):
    resposta = client.get("/api/auth/options")
    assert resposta.status_code == 200
    perfis_disponiveis = {perfil for usuario in resposta.json()["users"] for perfil in usuario["profiles"]}
    assert perfis_disponiveis == {perfil.value for perfil in Perfil}


def test_usuario_sem_perfil_autentica_mas_nao_acessa_endpoint_de_dados(client):
    headers = autenticar(client, "sem-perfil")
    assert client.get("/api/users/me", headers=headers).status_code == 200
    assert client.get("/api/pacientes", headers=headers).status_code == 403


def test_admin_local_nao_tem_permissao_total_por_grupo(client):
    headers = autenticar(client, "admin", "admin")
    assert client.get("/api/admin-only-data", headers=headers).status_code == 200
    assert client.get("/api/admin/ad-user-search/maria.souza", headers=headers).status_code == 200


def test_operacao_admin_recusa_perfil_sem_permissao(client):
    headers = autenticar(client, "recepcionista")
    assert client.get("/api/admin-only-data", headers=headers).status_code == 403


def test_uniao_de_multiplos_perfis(client):
    headers = autenticar(client, "recepcao-coordenacao")
    dados = client.get("/api/users/me", headers=headers).json()
    assert len(dados["profiles"]) == 2
    assert Permissao.RECEPCAO_RECEBER.value in dados["permissions"]
    assert Permissao.DEVOLUCOES_CONSULTAR.value in dados["permissions"]
    assert Permissao.DEVOLUCOES_ALTERAR_SITUACAO.value in dados["permissions"]
    assert Permissao.CASOS_CANCELAR.value in dados["permissions"]


def test_provedor_mock_nao_e_selecionado_em_producao(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("AUTH_PROVIDER", "mock")
    try:
        AuthHandler()
    except RuntimeError as erro:
        assert "proibido em produção" in str(erro)
    else:
        raise AssertionError("O provedor mock foi aceito em produção")


def test_adapter_mock_valida_apenas_identidades_configuradas():
    provider = MockIdentityProvider()
    assert provider.authenticate("citotecnico", "demo")["profiles"] == [Perfil.CITOTECNICO.value]
    assert provider.authenticate("sem-perfil", "demo")["permissions"] == []
