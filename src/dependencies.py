import os
from functools import lru_cache
from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .providers.interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface
from .providers.implementations.solicitacao_csv_provider import SolicitacaoCsvProvider

from .providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from .providers.implementations.paciente_postgres_provider import PacientePostgresProvider
from .providers.implementations.paciente_csv_provider import PacienteCsvProvider
from .resources.database import get_aghu_db_session, get_app_db_session
from .providers.implementations.reception_sqlite_provider import ReceptionSqliteProvider
from .providers.interfaces.reception_provider_interface import ReceptionProviderInterface


def get_reception_provider(
    session: AsyncSession = Depends(get_app_db_session),
) -> ReceptionProviderInterface:
    """Monta provider de estado AP usando a sessão local da aplicação."""
    return ReceptionSqliteProvider(session)

# 1. Funções "getter" simples e independentes (privadas por convenção)
def _get_paciente_postgres_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> PacienteProviderInterface:
    return PacientePostgresProvider(session=session)

def _get_paciente_csv_provider() -> PacienteProviderInterface:
    csv_path = os.getenv("PACIENTE_CSV_PATH", "data/pacientes.csv")
    return PacienteCsvProvider(csv_path=csv_path)

# 2. A FÁBRICA: A única função que o roteador vai conhecer.
def get_paciente_provider(strategy: str) -> Callable[..., PacienteProviderInterface]:
    """
    Esta é uma fábrica. Baseado na string 'strategy', ela não retorna o provedor,
    mas sim a FUNÇÃO DE DEPENDÊNCIA correta que o FastAPI deve usar.
    """
    if strategy.upper() == "POSTGRES":
        return _get_paciente_postgres_provider
    elif strategy.upper() == "CSV":
        return _get_paciente_csv_provider
    else:
        raise ValueError(f"Estratégia de provedor desconhecida: {strategy}")


# --- Solicitações AGHU ---------------------------------------------------------

@lru_cache(maxsize=1)
def _carregar_solicitacao_csv_provider(csv_path: str) -> SolicitacaoCsvProvider:
    """Cria (uma única vez por caminho) o provedor CSV, mantendo o arquivo em memória."""
    return SolicitacaoCsvProvider(csv_path=csv_path)


def _get_solicitacao_csv_provider() -> SolicitacaoProviderInterface:
    """Dependência FastAPI que devolve o provedor CSV de solicitações (singleton)."""
    csv_path = os.getenv("SOLICITACAO_CSV_PATH", "data/privado/solicitacoes.csv")
    try:
        return _carregar_solicitacao_csv_provider(csv_path)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


def get_solicitacao_provider(strategy: str) -> Callable[..., SolicitacaoProviderInterface]:
    """Fábrica: retorna a função de dependência do provedor de solicitações para a estratégia."""
    if strategy.upper() == "CSV":
        return _get_solicitacao_csv_provider
    else:
        raise ValueError(f"Estratégia de provedor desconhecida: {strategy}")
