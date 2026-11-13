import os
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ...helpers.sql_helper import read_sql_file
from ..interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface
from .solicitacao_mapeamento import limpar_texto, montar_solicitacao

_PASTA_SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql", "solicitacao")


def _sql(nome_arquivo: str) -> Any:
    """Carrega um template da pasta de SQL das solicitações."""
    return text(read_sql_file(os.path.join(_PASTA_SQL, nome_arquivo)))


class SolicitacaoPostgresProvider(SolicitacaoProviderInterface):
    """
    Leitura de solicitações na vw_solicitacao do AGHU (RN-01: somente SELECT).

    Ainda não foi executado contra o banco real: o schema e os tipos da view estão como TODO
    nos arquivos de src/providers/sql/solicitacao/. Depois de confirmá-los, troque STRATEGY em
    src/routers/recebimento.py para "postgres".
    """

    def __init__(self, session: AsyncSession) -> None:
        """Guarda a sessão de leitura do banco do AGHU."""
        self.session = session

    def _erro_de_leitura(self, erro: Exception) -> HTTPException:
        """Registra só o tipo do erro e monta a resposta 503."""
        print(f"Erro ao consultar a vw_solicitacao: {type(erro).__name__}")
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível ler os dados de solicitações do AGHU.",
        )

    async def obter_solicitacao_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Retorna a solicitação e suas amostras, ou None se o código não existir."""
        try:
            resultado = await self.session.execute(_sql("obter_solicitacao.sql"), {"codigo": codigo})
            linhas = resultado.mappings().all()
        except (SQLAlchemyError, OSError) as erro:
            raise self._erro_de_leitura(erro)
        return montar_solicitacao(list(linhas))

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
        consulta = consulta or {}
        por_coluna = consulta.get("filtros") or {}
        codigos_lab_filtro = consulta.get("codigos_lab_filtro")
        dia = por_coluna.get("data")
        # Todos os valores vão como parâmetros do SQL; nada do usuário entra no texto da consulta.
        filtros = {
            "codigos_lab": list(codigos_lab),
            "filtrar_status": codigos_status is not None,
            "codigos_status": list(codigos_status or []),
            "filtro_codigo": por_coluna.get("codigo"),
            "filtro_data": date.fromisoformat(dia) if dia else None,
            "filtro_paciente": por_coluna.get("paciente"),
            "filtro_prontuario": por_coluna.get("prontuario"),
            "filtro_origem": por_coluna.get("origem"),
            "filtro_clinica": por_coluna.get("clinica"),
            "filtrar_bancada": codigos_lab_filtro is not None,
            "codigos_lab_filtro": list(codigos_lab_filtro or []),
        }
        prioridade = {
            "codigos_lab_urgentes": list(codigos_lab_urgentes),
            "codigos_excluidas": list(codigos_excluidas_da_prioridade),
            "ordenar_por": consulta.get("ordenar_por"),
            "direcao": consulta.get("direcao") or "asc",
        }
        try:
            total = await self.session.execute(_sql("contar_solicitacoes.sql"), filtros)
            quantidade = total.scalar_one()
            resultado = await self.session.execute(
                _sql("listar_solicitacoes.sql"),
                                {
                    **filtros,
                    **prioridade,
                    "limite": por_pagina,
                    "deslocamento": (pagina - 1) * por_pagina,
                },
            )
            linhas = resultado.mappings().all()
        except (SQLAlchemyError, OSError) as erro:
            raise self._erro_de_leitura(erro)

        # O SQL já ordena as solicitações; o dicionário preserva essa ordem.
        grupos: Dict[str, List[Any]] = {}
        for linha in linhas:
            grupos.setdefault(limpar_texto(linha["codigo_solicitacao"]), []).append(linha)
        return {
            "total": quantidade,
            "solicitacoes": [montar_solicitacao(grupo) for grupo in grupos.values()],
        }
