from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AghuxProviderInterface(ABC):
    """Contrato para cruzamento de dados do formulário com o AGHUX."""

    @abstractmethod
    async def buscar_por_prontuario(self, prontuario: str) -> Optional[Dict[str, Any]]:
        """Retorna o registro AGHUX do prontuário, ou None quando ausente."""
        pass

    @abstractmethod
    async def buscar_por_codigo_solicitacao(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Retorna o registro AGHUX pelo código da solicitação, ou None."""
        pass
