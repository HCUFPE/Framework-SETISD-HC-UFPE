"""
Interface do Provedor da Fila de Exames (SQLite local)
======================================================
Contrato de acesso a ``acompanhamento_fila`` e às tabelas configuráveis
``regras_prioridade``, ``regras_exames`` e ``incompatibilidades_exames``.
Todas as leituras de regras retornam apenas registros ativos e não excluídos.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class FilaProviderInterface(ABC):
    """Contrato de persistência local da fila de exames."""

    @abstractmethod
    async def listar_itens_ativos(self) -> List[Dict[str, Any]]:
        """Retorna todos os itens da fila não excluídos logicamente."""

    @abstractmethod
    async def obter_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um item não excluído pelo id, ou ``None``."""

    @abstractmethod
    async def listar_por_prontuario(self, prontuario: str) -> List[Dict[str, Any]]:
        """Retorna os itens não excluídos de um prontuário."""

    @abstractmethod
    async def existe_item_ativo(
        self, prontuario: str, codigo_exame: str, excluir_id: Optional[int] = None
    ) -> bool:
        """Indica se há outro item válido, não cancelado e não excluído, do mesmo prontuário e exame."""

    @abstractmethod
    async def atualizar_item(self, item_id: int, campos: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica os campos ao item na sessão corrente (sem commit) e retorna o item atualizado."""

    @abstractmethod
    async def listar_regras_prioridade(self) -> List[Dict[str, Any]]:
        """Retorna as regras de prioridade ativas e não excluídas."""

    @abstractmethod
    async def listar_regras_exames(self) -> List[Dict[str, Any]]:
        """Retorna as regras de exame ativas e não excluídas."""

    @abstractmethod
    async def listar_incompatibilidades(self) -> List[Dict[str, Any]]:
        """Retorna as incompatibilidades ativas e não excluídas."""
