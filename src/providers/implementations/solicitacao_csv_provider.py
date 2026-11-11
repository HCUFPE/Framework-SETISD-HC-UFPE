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

# Coluna da lista -> coluna do CSV, para as que são um único campo da view.
_CAMPO_DA_COLUNA = {
    "codigo": "codigo_solicitacao",
    "paciente": "nome_paciente",
    "prontuario": "prontuario",
    "origem": "origem",
}

def _texto_da_coluna(coluna: str, linha: Dict[str, str]) -> str:
    """Texto da coluna para comparar: sem caracteres invisíveis e sem diferenciar maiúsculas."""
    if coluna == "clinica":
        texto = f"{limpar_texto(linha['especialidade'])} {limpar_texto(linha['unidade'])}"
    else:
        texto = limpar_texto(linha[_CAMPO_DA_COLUNA[coluna]])
    return texto.casefold()

def _passa_na_consulta(
    linhas: List[Dict[str, str]],
    filtros: Dict[str, str],
    codigos_lab_filtro: Optional[Sequence[str]],
) -> bool:
    """Aplica os filtros por coluna e o filtro de bancada a uma solicitação (todas as colunas combinadas)."""
    primeira = linhas[0]
    for coluna, procurado in filtros.items():
        if coluna == "data":
            if converter_data(primeira["data_solicitacao"]) != procurado:
                return False
        elif procurado.casefold() not in _texto_da_coluna(coluna, primeira):
            return False
    if codigos_lab_filtro is not None:
        return any(limpar_texto(linha["codigo_lab"]) in codigos_lab_filtro for linha in linhas)
    return True

def _chave_de_ordenacao(coluna: str, codigo: str, linhas: List[Dict[str, str]]) -> Any:
    """Chave de ordenação da solicitação para a coluna pedida; valor ausente vem primeiro."""
    if coluna == "codigo":
        return int(codigo)
    if coluna == "data":
        return converter_data(linhas[0]["data_solicitacao"]) or ""
    return _texto_da_coluna(coluna, linhas[0])

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
        codigos_lab_urgentes: Sequence[str] = (),
        codigos_excluidas_da_prioridade: Sequence[str] = (),
        consulta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Filtra, ordena (prioritárias primeiro) e monta só as solicitações da página pedida."""
        consulta = consulta or {}
        filtros = consulta.get("filtros") or {}
        codigos_lab_filtro = consulta.get("codigos_lab_filtro")
        ordenar_por = consulta.get("ordenar_por")
        laboratorios = set(codigos_lab)
        urgentes = set(codigos_lab_urgentes)
        excluidas = set(codigos_excluidas_da_prioridade)
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
            and _passa_na_consulta(linhas, filtros, codigos_lab_filtro)
        ]
        selecionadas.sort(
            key=lambda grupo: (
                grupo[0] not in excluidas
                and any(
                    limpar_texto(linha["codigo_lab"]) in urgentes
                    and (permitidos is None or limpar_texto(linha["cod_status_item"]) in permitidos)
                    for linha in grupo[1]
                ),
                converter_data(grupo[1][0]["data_solicitacao"]) or "",
                int(grupo[0]),
            ),
            reverse=True,
        )
        if ordenar_por:
            # A ordenação escolhida vale no lugar da padrão. O sort é estável, então os empates
            # continuam da mais recente para a mais antiga, como acima.
            selecionadas.sort(
                key=lambda grupo: _chave_de_ordenacao(ordenar_por, grupo[0], grupo[1]),
                reverse=consulta.get("direcao") == "desc",
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
        codigos_lab_urgentes: Sequence[str] = (),
        codigos_excluidas_da_prioridade: Sequence[str] = (),
        consulta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Retorna uma página de solicitações, as prioritárias primeiro e depois por data."""
        return await self._executar(
            self._listar,
            pagina,
            por_pagina,
            codigos_status,
            codigos_lab,
            codigos_lab_urgentes,
            codigos_excluidas_da_prioridade,
            consulta,
        )
    