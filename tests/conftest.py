# tests/conftest.py
import pytest
import os
import sys

# Ensure src directory is in sys.path for test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    """
    Fixture de teste que fornece um TestClient configurado para fazer requisições à aplicação FastAPI.
    """
    with TestClient(app) as test_client:
        yield test_client
