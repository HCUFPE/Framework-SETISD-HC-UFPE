from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class FormsProviderInterface(ABC):
    """Contrato para obtenção normalizada de uma resposta do Microsoft Forms."""

    @abstractmethod
    async def buscar_resposta(
        self,
        form_id: str,
        response_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Retorna um dicionário com as chaves canônicas do formulário."""
        pass
