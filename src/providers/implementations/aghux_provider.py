"""
Provedores de cruzamento com o AGHUX
=====================================
`AghuxJsonProvider` consome o fixture versionado gerado a partir do export real
(576 itens / 493 solicitações). `AghuProvider` é o ponto de extensão para a
consulta futura ao PostgreSQL do AGHU.
"""

import json
import os
import re
from typing import Any, Dict, Optional

from ...config import settings
from ..interfaces.aghux_provider_interface import AghuxProviderInterface


def _chave(texto: Optional[str]) -> str:
    """Normaliza identificadores removendo espaços e pontuação."""
    return re.sub(r"[^a-z0-9]", "", str(texto or "").lower())


class AghuxJsonProvider(AghuxProviderInterface):
    """Le o JSON versionado do AGHUX e indexa prontuário e código da solicitação."""

    def __init__(self, caminho: Optional[str] = None):
        self.caminho = caminho or settings.AGHUX_FIXTURE_PATH
        with open(self.caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        self.referencia_em = dados.get("referenciaEm")
        self.solicitacoes = dados.get("solicitacoes", [])
        self._por_prontuario: Dict[str, Dict[str, Any]] = {}
        self._por_codigo: Dict[str, Dict[str, Any]] = {}
        for item in self.solicitacoes:
            if item.get("prontuario"):
                self._por_prontuario.setdefault(_chave(item["prontuario"]), item)
            if item.get("codigoSolicitacao"):
                self._por_codigo.setdefault(_chave(item["codigoSolicitacao"]), item)

    async def buscar_por_prontuario(self, prontuario: str) -> Optional[Dict[str, Any]]:
        """Busca um registro pelo prontuário informado no formulário."""
        return self._por_prontuario.get(_chave(prontuario))

    async def buscar_por_codigo_solicitacao(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Busca um registro pelo código de solicitação do AGHUX."""
        return self._por_codigo.get(_chave(codigo))


class AghuProvider(AghuxProviderInterface):
    """Reservado para o provider real do AGHU (PostgreSQL) em entrega futura."""

    async def buscar_por_prontuario(self, prontuario: str) -> Optional[Dict[str, Any]]:
        """Avisa que a conexão real com o AGHU ainda não foi habilitada."""
        raise NotImplementedError(
            "AGHU ainda não implementado: configure AGHUX_PROVIDER_TYPE=JSON."
        )

    async def buscar_por_codigo_solicitacao(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Avisa que a conexão real com o AGHU ainda não foi habilitada."""
        raise NotImplementedError(
            "AGHU ainda não implementado: configure AGHUX_PROVIDER_TYPE=JSON."
        )


def carregar_provider_aghux(caminho: Optional[str] = None) -> AghuxProviderInterface:
    """Fábrica simples usada pelos testes e pelo controller."""
    tipo = os.getenv("AGHUX_PROVIDER_TYPE", settings.AGHUX_PROVIDER_TYPE).upper()
    if tipo == "JSON":
        return AghuxJsonProvider(caminho)
    return AghuProvider()
