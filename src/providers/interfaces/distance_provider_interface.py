"""Contrato dos provedores de distância até o hospital (OSM ou MOCK)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DistanceResult:
    """Resultado bruto de geocodificação/roteamento, sem expor o endereço."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distancia_km: Optional[float] = None
    fonte: str = "INDISPONIVEL"  # OSM | MOCK | INDISPONIVEL


class DistanceProviderInterface(ABC):
    """Calcula a distância de um endereço até o hospital configurado."""

    @abstractmethod
    async def calcular(self, endereco: Dict[str, Any]) -> DistanceResult:
        """Devolve a distância em km; falhas retornam fonte INDISPONIVEL."""
        pass
