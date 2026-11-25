"""Contrato do provedor local de vagas (agenda_slots)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class SlotProviderInterface(ABC):
    """Expõe as vagas locais já convertidas para o DTO `AgendaSlot`."""

    @abstractmethod
    async def listar(
        self,
        *,
        de: Optional[datetime] = None,
        ate: Optional[datetime] = None,
        unidade: str = "",
        codigo_exame: str = "",
    ) -> List[Dict[str, Any]]:
        """Lista vagas ativas no intervalo informado com ocupações calculadas."""
        pass

    @abstractmethod
    async def obter(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Retorna uma vaga pelo id ou None quando inexistente."""
        pass

    @abstractmethod
    async def criar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma vaga (sem commit; o controller audita e confirma)."""
        pass

    @abstractmethod
    async def atualizar(self, slot_id: str, dados: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza uma vaga (sem commit; o controller audita e confirma)."""
        pass
