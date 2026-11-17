# tests/conftest.py
import pytest
import os
import sys

# Ensure src directory is in sys.path for test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Fixture de teste que fornece um TestClient configurado para fazer requisições à aplicação FastAPI.
    """
    test_dsn = f"sqlite+aiosqlite:///{(tmp_path / 'app.db').as_posix()}"
    monkeypatch.setenv("APP_DB_URL", test_dsn)
    monkeypatch.setenv("SQLITE_DSN", test_dsn)
    monkeypatch.setattr("src.config.settings.AP_REQUEST_FIXTURE", "minimal")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def demo_client(tmp_path, monkeypatch):
    """TestClient com a carga completa da demonstração AP já existente no frontend."""
    test_dsn = f"sqlite+aiosqlite:///{(tmp_path / 'demo.db').as_posix()}"
    monkeypatch.setenv("APP_DB_URL", test_dsn)
    monkeypatch.setenv("SQLITE_DSN", test_dsn)
    monkeypatch.setattr("src.config.settings.AP_REQUEST_FIXTURE", "demo")
    with TestClient(app) as test_client:
        yield test_client
