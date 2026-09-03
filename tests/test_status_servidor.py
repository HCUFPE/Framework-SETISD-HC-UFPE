# tests/test_status_servidor.py

def test_status_servidor_e_bancos(client):
    """
    Testa se o servidor web FastAPI e a infraestrutura de banco de dados estão online e respondendo (Status Check).
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data
    assert "databases" in data
