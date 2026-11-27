from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ExameProviderInterface(ABC):
    """Interface (contrato) para provedores de dados de solicitações de exames do AGHU."""

    @abstractmethod
    async def listar_exames(self) -> List[Dict[str, Any]]:
        """Deve retornar uma lista de solicitações de exames."""
        pass

    @abstractmethod
    async def buscar_por_solicitacao(
        self, codigo_solicitacao: str
    ) -> List[Dict[str, Any]]:
        """Deve retornar os itens de exame associados a um código de solicitação."""
        pass

    @abstractmethod
    async def buscar_por_prontuario(self, prontuario: str) -> List[Dict[str, Any]]:
        """Deve retornar as solicitações de exames associadas a um prontuário."""
        pass

    @abstractmethod
    async def buscar_por_nome(self, nome: str) -> List[Dict[str, Any]]:
        """Deve retornar as solicitações cujo nome do paciente contém o trecho informado (mín. 3 caracteres)."""
        pass
