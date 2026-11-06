import asyncio
import csv
from typing import Any, Callable, Dict, List, Optional, Sequence

from fastapi import HTTPException, status

from ..interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface
from .solicitacao_mapeamento import (
    COLUNAS_VIEW,
    converter_data,
    limpar_texto,
    montar_solicitacao,
)

# Layout do CSV exportado da vw_solicitacao: ver docs/especificacao/05-interfaces.md.
CSV_DELIMITADOR = ","
CSV_ENCODING = "utf-8-sig"  # Também aceita o BOM de arquivos exportados por planilhas.


class SolicitacaoCsvProvider(SolicitacaoProviderInterface):
    """Lê as solicitações de um CSV exportado do AGHU. Nunca grava no arquivo."""

    def __init__(self, csv_path: str = "data/solicitacoes_aghu_exemplo.csv") -> None:
        """Guarda o caminho do arquivo e confirma que ele existe."""
        self.csv_path = csv_path
        self._verificar_arquivo()

    def _verificar_arquivo(self) -> None:
        """Levanta RuntimeError se o CSV não existir, como no provider de pacientes."""
        try:
            with open(self.csv_path, mode="r", encoding=CSV_ENCODING):
                pass
        except FileNotFoundError:
            raise RuntimeError(f"Arquivo CSV de solicitações não encontrado em: {self.csv_path}")

    def _ler_todas(self) -> List[Dict[str, str]]:
        """Retorna todas as linhas do arquivo. Levanta ValueError se faltar coluna."""
        with open(self.csv_path, mode="r", encoding=CSV_ENCODING, newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=CSV_DELIMITADOR)
            faltantes = set(COLUNAS_VIEW) - set(leitor.fieldnames or [])
            if faltantes:
                raise ValueError("Colunas ausentes no arquivo.")
            return list(leitor)

    def _obter(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Monta a solicitação com as linhas do código informado."""
        return montar_solicitacao(
            [
                linha
                for linha in self._ler_todas()
                if limpar_texto(linha["codigo_solicitacao"]) == codigo
            ]
        )

    def _listar(
        self,
        pagina: int,
        por_pagina: int,
        codigos_status: Optional[Sequence[str]],
        codigos_lab: Sequence[str],
    ) -> Dict[str, Any]:
        """Filtra, ordena e monta só as solicitações da página pedida."""
        laboratorios = set(codigos_lab)
        permitidos = None if codigos_status is None else set(codigos_status)

        grupos: Dict[str, List[Dict[str, str]]] = {}
        for linha in self._ler_todas():
            grupos.setdefault(limpar_texto(linha["codigo_solicitacao"]), []).append(linha)

        selecionadas = [
            (codigo, linhas)
            for codigo, linhas in grupos.items()
            if any(
                limpar_texto(linha["codigo_lab"]) in laboratorios
                and (permitidos is None or limpar_texto(linha["cod_status_item"]) in permitidos)
                for linha in linhas
            )
        ]
        selecionadas.sort(
            key=lambda grupo: (converter_data(grupo[1][0]["data_solicitacao"]) or "", int(grupo[0])),
            reverse=True,
        )

        inicio = (pagina - 1) * por_pagina
        return {
            "total": len(selecionadas),
            "solicitacoes": [
                montar_solicitacao(linhas)
                for _, linhas in selecionadas[inicio : inicio + por_pagina]
            ],
        }

    async def _executar(self, leitura: Callable[..., Any], *argumentos: Any) -> Any:
        """Lê em thread, para não travar outras requisições, e traduz as falhas de leitura."""
        try:
            return await asyncio.to_thread(leitura, *argumentos)
        except ValueError as erro:
            # Registra só o tipo do erro: a mensagem de uma conversão falha traria o valor lido.
            print(f"Layout inválido no CSV de solicitações: {type(erro).__name__}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="O arquivo de solicitações do AGHU não está no layout esperado.",
            )
        except (OSError, csv.Error) as erro:
            print(f"Erro ao ler CSV de solicitações: {type(erro).__name__}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível ler os dados de solicitações do AGHU.",
            )

    async def obter_solicitacao_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Retorna a solicitação e suas amostras, ou None se o código não existir."""
        return await self._executar(self._obter, codigo)

    async def listar_solicitacoes(
        self,
        pagina: int,
        por_pagina: int,
        codigos_status: Optional[Sequence[str]],
        codigos_lab: Sequence[str],
    ) -> Dict[str, Any]:
        """Retorna uma página de solicitações, da mais recente para a mais antiga."""
        return await self._executar(self._listar, pagina, por_pagina, codigos_status, codigos_lab)
