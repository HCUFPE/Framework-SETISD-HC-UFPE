import os
from typing import Any, Dict, List, Mapping, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...helpers.sql_helper import create_query, read_sql_file
from ..interfaces.exame_provider_interface import ExameProviderInterface


def get_sql_query(file_path: str) -> str:
    """Carrega o conteúdo de um template SQL localizado em ``src/providers/sql/``."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.normpath(os.path.join(base_dir, "..", "sql", file_path))
    try:
        return read_sql_file(sql_file_path)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Arquivo SQL de exames não encontrado em: {sql_file_path}"
        ) from exc


class ExamePostgresProvider(ExameProviderInterface):
    """Provedor somente leitura de solicitações de exames no banco PostgreSQL do AGHU."""

    def __init__(self, session: AsyncSession) -> None:
        """Inicializa o provedor PostgreSQL com uma sessão assíncrona do AGHU."""
        self.session: AsyncSession = session

    @staticmethod
    def _parse_numeric_identifier(value: Optional[str]) -> Optional[int]:
        """Valida e converte um identificador numérico (solicitação ou prontuário) para inteiro."""
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned or not (cleaned.isascii() and cleaned.isdigit()):
            return None
        return int(cleaned)

    @staticmethod
    def _prepare_parameterized_query(file_path: str, param_name: str) -> str:
        """Carrega o template SQL e converte o placeholder ``#param`` em bind seguro ``:param``."""
        sql_template = get_sql_query(file_path)
        return create_query(sql_template, {param_name: f":{param_name}"})

    @staticmethod
    def _normalize_row(row: Mapping[str, Any]) -> Dict[str, Any]:
        """Normaliza registro retornado pelo AGHU (prontuário anulável, tipos e alias de data)."""
        normalized: Dict[str, Any] = {}
        for key, value in dict(row).items():
            clean_key = key.strip() if isinstance(key, str) else str(key)
            if isinstance(value, str):
                normalized[clean_key] = value.strip()
            else:
                normalized[clean_key] = value

        prontuario = normalized.get("prontuario")
        if prontuario is None:
            normalized["prontuario"] = None
        else:
            prontuario_str = str(prontuario).strip()
            normalized["prontuario"] = prontuario_str if prontuario_str else None

        codigo_solicitacao = normalized.get("codigo_solicitacao")
        if codigo_solicitacao is not None:
            normalized["codigo_solicitacao"] = str(codigo_solicitacao).strip()

        if "data_solicitao" in normalized and (
            "data_solicitacao" not in normalized
            or normalized.get("data_solicitacao") is None
        ):
            normalized["data_solicitacao"] = normalized["data_solicitao"]
        elif "data_solicitacao" in normalized and (
            "data_solicitao" not in normalized
            or normalized.get("data_solicitao") is None
        ):
            normalized["data_solicitao"] = normalized["data_solicitacao"]

        id_func = normalized.get("id_funcionario")
        if isinstance(id_func, str):
            if id_func == "":
                normalized["id_funcionario"] = None
            else:
                try:
                    normalized["id_funcionario"] = int(id_func)
                except ValueError:
                    pass

        return normalized

    async def listar_exames(self) -> List[Dict[str, Any]]:
        """Retorna a listagem de solicitações de exames diretamente do AGHU."""
        query_string = get_sql_query("exames/consulta_aghu_exames.sql")
        query = text(query_string)

        result = await self.session.execute(query)
        rows = result.mappings().all()
        return [self._normalize_row(row) for row in rows]

    async def buscar_por_solicitacao(
        self, codigo_solicitacao: str
    ) -> List[Dict[str, Any]]:
        """Retorna os itens de exame associados a um código de solicitação no AGHU."""
        codigo_int = self._parse_numeric_identifier(codigo_solicitacao)
        if codigo_int is None:
            return []

        query_string = self._prepare_parameterized_query(
            "exames/buscar_por_solicitacao.sql", "codigo_solicitacao"
        )
        query = text(query_string)

        result = await self.session.execute(
            query, {"codigo_solicitacao": codigo_int}
        )
        rows = result.mappings().all()
        return [self._normalize_row(row) for row in rows]

    async def buscar_por_prontuario(self, prontuario: str) -> List[Dict[str, Any]]:
        """Retorna as solicitações de exames associadas a um prontuário no AGHU."""
        prontuario_int = self._parse_numeric_identifier(prontuario)
        if prontuario_int is None:
            return []

        query_string = self._prepare_parameterized_query(
            "exames/buscar_por_prontuario.sql", "prontuario"
        )
        query = text(query_string)

        result = await self.session.execute(query, {"prontuario": prontuario_int})
        rows = result.mappings().all()
        return [self._normalize_row(row) for row in rows]

    async def buscar_por_nome(self, nome: str) -> List[Dict[str, Any]]:
        """Retorna solicitações do AGHU cujo nome do paciente contém o trecho (ILIKE, mín. 3 caracteres)."""
        trecho = " ".join((nome or "").split())
        if len(trecho) < 3:
            return []
        trecho_escapado = (
            trecho.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

        query_string = self._prepare_parameterized_query(
            "exames/buscar_por_nome.sql", "nome"
        )
        query = text(query_string)

        result = await self.session.execute(query, {"nome": f"%{trecho_escapado}%"})
        rows = result.mappings().all()
        return [self._normalize_row(row) for row in rows]
