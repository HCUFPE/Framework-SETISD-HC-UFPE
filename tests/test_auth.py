# tests/test_auth.py

def test_login_mock_success(client):
    """
    Testa o login com credenciais de mock válidas (admin / admin).
    """
    response = client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_mock_invalid_credentials(client):
    """
    Testa o login com credenciais inválidas.
    """
    response = client.post(
        "/api/login",
        data={"username": "invalid_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

def test_read_users_me_with_token(client):
    """
    Testa a rota /api/users/me enviando um token de acesso válido.
    """
    # 1. Faz login para obter o token
    login_response = client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"}
    )
    token = login_response.json()["access_token"]

    # 2. Chama a rota /api/users/me enviando o Header Authorization
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/users/me", headers=headers)
    
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "admin"
