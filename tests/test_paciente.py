# tests/test_paciente.py

def test_listar_pacientes(client):
    """
    Testa o endpoint de listagem de pacientes.
    """
    # 1. Obter token de login
    login_response = client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Requisitar listagem de pacientes
    response = client.get("/api/pacientes", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
