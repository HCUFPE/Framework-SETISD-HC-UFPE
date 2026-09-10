# tests/test_auth_ad_search.py
from src.auth.auth import auth_handler

def test_mock_search_ad_user_known_user():
    """Testa a busca direta do método no AuthHandler/MockAuthProvider para usuários conhecidos."""
    res = auth_handler.search_ad_user("joao.silva")
    assert res["exists"] is True
    assert res["username"] == "joao.silva"
    assert res["displayName"] == "João da Silva"
    assert res["email"] == "joao.silva@ebserh.gov.br"
    assert "UTI Adulto" in res["department"]

def test_mock_search_ad_user_dynamic_dotted_name():
    """Testa a busca dinâmica com padrão nome.sobrenome."""
    res = auth_handler.search_ad_user("carlos.eduardo")
    assert res["exists"] is True
    assert res["username"] == "carlos.eduardo"
    assert res["displayName"] == "Carlos Eduardo"
    assert "carlos.eduardo@ebserh.gov.br" in res["email"]

def test_mock_search_ad_user_not_found():
    """Testa a busca para um usuário inexistente sem ponto."""
    res = auth_handler.search_ad_user("inexistentuser999")
    assert res["exists"] is False
    assert res["displayName"] == ""

def test_admin_ad_user_search_endpoint_authenticated(client):
    """Testa o endpoint /api/admin/ad-user-search/{username} com usuário autenticado com perfil Admin."""
    # 1. Faz login como admin
    login_res = client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Chama o endpoint de busca AD
    response = client.get("/api/admin/ad-user-search/maria.souza", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["username"] == "maria.souza"
    assert data["displayName"] == "Maria Souza"
    assert data["email"] == "maria.souza@ebserh.gov.br"
    assert "Bloco Cirúrgico" in data["department"]

def test_admin_ad_user_search_endpoint_unauthorized(client):
    """Testa a rota sem autenticação (deve retornar 401)."""
    response = client.get("/api/admin/ad-user-search/joao.silva")
    assert response.status_code == 401
