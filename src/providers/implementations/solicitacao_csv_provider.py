import os
from typing import List, Dict, Any

import pandas as pd

from ..interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface


class SolicitacaoCsvProvider(SolicitacaoProviderInterface):
    """Provedor de solicitações AGHU a partir de um CSV exportado.

    O arquivo é lido UMA única vez na construção e mantido em memória.
    Campos entre aspas com quebra de linha são suportados pelo parser do pandas.
    """

    def __init__(self, csv_path: str) -> None:
        """Carrega o CSV em memória.

        Raises:
            RuntimeError: se o arquivo não existir.
        """
        self.csv_path = csv_path
        if not os.path.isfile(csv_path):
            raise RuntimeError(f"Arquivo CSV de solicitações não encontrado em: {csv_path}")

        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding="utf-8")
        df.columns = [str(c).strip() for c in df.columns]
        self._registros: List[Dict[str, Any]] = [
            {
                chave: (
                    valor.replace("\r\n", "\n").replace("\r", "\n").strip()
                    if isinstance(valor, str)
                    else valor
                )
                for chave, valor in linha.items()
            }
            for linha in df.to_dict(orient="records")
        ]

    async def listar_solicitacoes(self) -> List[Dict[str, Any]]:
        """Retorna cópias de todos os itens de exame carregados."""
        return [dict(r) for r in self._registros]

    async def obter_itens_por_codigo(self, codigo: str) -> List[Dict[str, Any]]:
        """Retorna cópias dos itens cujo `codigo_solicitacao` é igual ao informado."""
        codigo = str(codigo).strip()
        return [dict(r) for r in self._registros if r.get("codigo_solicitacao") == codigo]
