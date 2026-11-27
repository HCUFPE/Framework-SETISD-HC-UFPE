"""
Fixtures compartilhadas dos testes de API da Fila de Exames (TASK-010)
=====================================================================
Sobe a aplicação com SQLite temporário (isolado de ``data/app.db``), autentica
com o provedor Mock, carrega as regras do seed inicial e aponta o provedor
AGHU para um CSV de teste controlado.
"""

import csv
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.auth.auth import MockAuthProvider, auth_handler
from src.main import app
from src.models import AcompanhamentoFila, AuditLog, IncompatibilidadeExame, RegraExame, RegraPrioridade
from src.providers.implementations.exame_csv_provider import ExameCsvProvider
from src.resources.seed_exames import (
    INCOMPATIBILIDADES_EXAMES_INICIAIS,
    REGRAS_EXAMES_INICIAIS,
    REGRAS_PRIORIDADE_INICIAIS,
)
from src.routers import exames as exames_router

CABECALHO_AGHU = [
    "prontuario", "nome", "telefone", "cidade", "estado", "codigo_solicitacao", "data_solicitao",
    "unidade_solicitante", "codigo_exame", "nome_exame", "id_funcionario", "nome_funcionario",
]

LINHAS_AGHU = [
    ["1001", "MARIA ANONIMIZADA UM", "", "RECIFE", "PE", "900001", "2026-11-02 08:00:00",
     "GASTROENTEROLOGIA", "COLONO", "COLONOSCOPIA COM BIOPSIA, SE NECESSARIO", "1", "DR. A"],
    ["1001", "MARIA ANONIMIZADA UM", "", "RECIFE", "PE", "900002", "2026-11-03 08:00:00",
     "CLINICA MEDICA", "HEMO", "HEMOGRAMA COMPLETO", "1", "DR. A"],
    ["2002", "JOSE ANONIMIZADO DOIS", "", "RECIFE", "PE", "900010", "2026-11-20 08:00:00",
     "ONCOLOGIA CLINICA", "USAX", "ULTRASSONOGRAFIA DE ABDOME TOTAL", "2", "DR. B"],
    ["3003", "ANA ANONIMIZADA TRES", "", "OLINDA", "PE", "900011", "2026-11-01 08:00:00",
     "AMBULATORIO GERAL", "USAX", "ULTRASSONOGRAFIA DE ABDOME TOTAL", "3", "DR. C"],
    ["4004", "PEDRO ANONIMIZADO QUATRO", "", "CARUARU", "PE", "900020", "2026-11-05 08:00:00",
     "CARDIOLOGIA", "INR", "COAGULOGRAMA / TEMPO DE PROTROMBINA (INR)", "4", "DR. D"],
    ["5005", "LUCIA ANONIMIZADA CINCO", "", "RECIFE", "PE", "900030", "2026-11-06 08:00:00",
     "GINECOLOGIA", "RXMM1", "MAMOGRAFIA BILATERAL DIGITAL", "5", "DR. E"],
]


@dataclass
class FilaApi:
    """Acesso de teste à API e ao SQLite temporário."""

    client: TestClient
    headers: dict[str, str]
    engine: Engine

    def inserir(self, **campos: Any) -> int:
        """Insere um item em ``acompanhamento_fila`` e retorna o id."""
        padrao: dict[str, Any] = {
            "codigo_solicitacao": "999999",
            "codigo_exame": "USAX",
            "prontuario": None,
            "nome_paciente": "PACIENTE TESTE",
            "regiao_geografica": "CAPITAL",
            "municipio": "RECIFE",
            "status_higienizacao": "VALIDA",
            "status_operacional": "NA_FILA",
        }
        padrao.update(campos)
        with Session(self.engine) as session:
            item = AcompanhamentoFila(**padrao)
            session.add(item)
            session.commit()
            return item.id

    def item(self, item_id: int) -> AcompanhamentoFila:
        """Lê um item diretamente do banco."""
        with Session(self.engine) as session:
            return session.get(AcompanhamentoFila, item_id)

    def audit_logs(self) -> list[dict[str, Any]]:
        """Lê os registros de auditoria com JSON desserializado."""
        with Session(self.engine) as session:
            logs = session.scalars(select(AuditLog).order_by(AuditLog.id)).all()
            return [
                {
                    "usuario": log.usuario,
                    "categoria": log.categoria,
                    "acao": log.acao,
                    "recurso": log.recurso,
                    "ip_origem": log.ip_origem,
                    "dados_anteriores": json.loads(log.dados_anteriores) if log.dados_anteriores else None,
                    "dados_novos": json.loads(log.dados_novos) if log.dados_novos else None,
                }
                for log in logs
            ]


def _carregar_seed(engine: Engine) -> None:
    """Insere as regras do seed inicial no SQLite temporário."""
    with Session(engine) as session:
        session.add_all(RegraPrioridade(**r) for r in REGRAS_PRIORIDADE_INICIAIS)
        session.add_all(RegraExame(**r) for r in REGRAS_EXAMES_INICIAIS)
        session.flush()
        session.add_all(IncompatibilidadeExame(**r) for r in INCOMPATIBILIDADES_EXAMES_INICIAIS)
        session.commit()


@pytest.fixture
def fila_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FilaApi]:
    """Aplicação com banco temporário, login mock, seed e CSV AGHU de teste."""
    db_path = tmp_path / "fila_test.db"
    dsn = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("SQLITE_DSN", dsn)
    monkeypatch.setenv("APP_DB_URL", dsn)
    monkeypatch.setenv("POSTGRES_DSN", "")
    monkeypatch.setattr(auth_handler, "provider", MockAuthProvider())

    csv_path = tmp_path / "aghu_teste.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, quoting=csv.QUOTE_ALL)
        escritor.writerow(CABECALHO_AGHU)
        escritor.writerows(LINHAS_AGHU)
    app.dependency_overrides[exames_router.provider_aghu] = lambda: ExameCsvProvider(csv_path=str(csv_path))

    try:
        with TestClient(app) as client:
            engine = create_engine(f"sqlite:///{db_path}")
            try:
                _carregar_seed(engine)
                login = client.post("/api/login", data={"username": "admin", "password": "admin"})
                assert login.status_code == 200, login.text
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                yield FilaApi(client=client, headers=headers, engine=engine)
            finally:
                engine.dispose()
    finally:
        app.dependency_overrides.pop(exames_router.provider_aghu, None)
