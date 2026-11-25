"""
Provedores de distância até o hospital
======================================
`OpenStreetMapDistanceProvider` usa Nominatim (geocoding) e OSRM (roteamento)
via httpx, sem chave paga, com timeout, User-Agent configurável e cache em
memória por hash do endereço. Nenhum log contém endereço ou coordenadas de
paciente: apenas o hash usado como chave de cache.
`MockDistanceProvider` existe somente para testes (DISTANCE_PROVIDER_TYPE=MOCK).
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional, Tuple

import httpx

from ...config import settings
from ..interfaces.distance_provider_interface import DistanceProviderInterface, DistanceResult

logger = logging.getLogger("distance")

CAMPOS_GEOCODING = ("logradouro", "numero", "complemento", "bairro", "cidade", "estado", "cep")
_CACHE: Dict[str, Tuple[float, DistanceResult]] = {}


def _texto(endereco: Dict[str, Any], campo: str) -> str:
    """Extrai um campo de endereço sem registrar seu valor em logs."""
    valor = endereco.get(campo)
    return str(valor).strip() if valor is not None else ""


def _hash_endereco(endereco: Dict[str, Any]) -> str:
    """Hash HMAC do endereço usado como chave de cache e identificador de log."""
    partes = [f"{campo}={_texto(endereco, campo).lower()}" for campo in CAMPOS_GEOCODING]
    chave = hashlib.sha256(settings.chave_cripto() + b"sae-hc:distance-cache").digest()
    return hmac.new(chave, "|".join(partes).encode("utf-8"), hashlib.sha256).hexdigest()


def _coordenadas_hospital() -> Tuple[float, float]:
    """Retorna latitude/longitude configuradas do hospital."""
    return float(settings.HOSPITAL_LATITUDE), float(settings.HOSPITAL_LONGITUDE)


class MockDistanceProvider(DistanceProviderInterface):
    """Distância determinística para testes; não inventa coordenadas."""

    async def calcular(self, endereco: Dict[str, Any]) -> DistanceResult:
        """Devolve a distância configurada com fonte MOCK."""
        return DistanceResult(
            latitude=None,
            longitude=None,
            distancia_km=float(settings.MOCK_DISTANCE_KM),
            fonte="MOCK",
        )


class OpenStreetMapDistanceProvider(DistanceProviderInterface):
    """Geocodifica o endereço no Nominatim e consulta a rota no OSRM."""

    async def calcular(self, endereco: Dict[str, Any]) -> DistanceResult:
        """Consulta OSM/OSRM com cache por hash; falhas viram INDISPONIVEL."""
        chave = _hash_endereco(endereco)
        expira, cached = _CACHE.get(chave, (0.0, None))
        if cached is not None and expira > time.monotonic():
            return cached

        try:
            latitude, longitude, distancia = await self._consultar(endereco)
        except Exception as exc:  # rede, parser ou configuração inválida
            # Nunca registrar endereço, URL com query ou mensagem que o contenha.
            logger.warning(
                "Distância indisponível (hash=%s, erro=%s).", chave, type(exc).__name__
            )
            # Falha transitória não entra em cache: uma queda de rede não pode
            # manter a distância indisponível por todo o TTL do cache.
            return DistanceResult(
                latitude=None, longitude=None, distancia_km=None, fonte="INDISPONIVEL"
            )

        resultado = DistanceResult(
            latitude=latitude,
            longitude=longitude,
            distancia_km=distancia,
            fonte="OSM",
        )
        ttl_segundos = max(0.0, float(settings.DISTANCE_CACHE_TTL_HOURS)) * 3600
        _CACHE[chave] = (time.monotonic() + ttl_segundos, resultado)
        return resultado

    async def _consultar(self, endereco: Dict[str, Any]) -> Tuple[float, float, float]:
        """Executa geocoding + roteamento e retorna (lat, lon, km)."""
        query = ", ".join(
            parte
            for campo in CAMPOS_GEOCODING
            if (parte := _texto(endereco, campo))
        )
        if not query:
            raise ValueError("Endereço vazio não pode ser geocodificado.")
        hospital_lat, hospital_lon = _coordenadas_hospital()

        headers = {"User-Agent": settings.OSM_USER_AGENT, "Accept": "application/json"}
        timeout = float(settings.DISTANCE_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as cliente:
            geocoding = await cliente.get(
                settings.OSM_NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 1},
            )
            geocoding.raise_for_status()
            resultados = geocoding.json()
            if not isinstance(resultados, list) or not resultados:
                raise LookupError("Endereço não localizado no Nominatim.")
            latitude = float(resultados[0]["lat"])
            longitude = float(resultados[0]["lon"])

            url_rota = (
                f"{settings.OSM_OSRM_URL.rstrip('/')}/route/v1/driving/"
                f"{longitude},{latitude};{hospital_lon},{hospital_lat}"
            )
            rota = await cliente.get(url_rota, params={"overview": "false"})
            rota.raise_for_status()
            corpo = rota.json()
            rotas = corpo.get("routes") or []
            if not rotas:
                raise LookupError("Rota não encontrada no OSRM.")
            return latitude, longitude, round(float(rotas[0]["distance"]) / 1000, 2)
