# tests/test_health.py

def test_health_check_endpoint(client):
    """
    Testa se a rota /api/health responde status 200 e traz as informações de saúde.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data
    assert "databases" in data
