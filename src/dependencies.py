import os
from typing import Callable
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from .providers.implementations.paciente_postgres_provider import PacientePostgresProvider
from .providers.implementations.paciente_csv_provider import PacienteCsvProvider
from .resources.database import get_aghu_db_session

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


# --- Recebimento de Amostras ---
from .providers.interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface
from .providers.implementations.solicitacao_postgres_provider import SolicitacaoPostgresProvider
from .providers.implementations.solicitacao_csv_provider import SolicitacaoCsvProvider
from .providers.interfaces.recebimento_provider_interface import RecebimentoProviderInterface
from .providers.implementations.recebimento_sqlalchemy_provider import RecebimentoSqlalchemyProvider
from .resources.database import get_app_db_session


def _get_solicitacao_postgres_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> SolicitacaoProviderInterface:
    """Fornece o provider de leitura de solicitações direto no AGHU."""
    return SolicitacaoPostgresProvider(session=session)


def _get_solicitacao_csv_provider() -> SolicitacaoProviderInterface:
    """Fornece o provider de leitura de solicitações a partir do CSV exportado do AGHU."""
    csv_path = os.getenv("SOLICITACAO_CSV_PATH", "data/solicitacoes_aghu_exemplo.csv")
    return SolicitacaoCsvProvider(csv_path=csv_path)


def get_solicitacao_provider(strategy: str) -> Callable[..., SolicitacaoProviderInterface]:
    """Fábrica: retorna a função de dependência do provider de solicitações escolhido."""
    if strategy.upper() == "POSTGRES":
        return _get_solicitacao_postgres_provider
    elif strategy.upper() == "CSV":
        return _get_solicitacao_csv_provider
    else:
        raise ValueError(f"Estratégia de provedor desconhecida: {strategy}")


def get_recebimento_provider(
    session: AsyncSession = Depends(get_app_db_session)
) -> RecebimentoProviderInterface:
    """Fornece o provider de persistência do recebimento no banco local."""
    return RecebimentoSqlalchemyProvider(session=session)
