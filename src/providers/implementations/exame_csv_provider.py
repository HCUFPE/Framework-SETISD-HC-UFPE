import csv
from typing import Any, Dict, List, Optional

from ..interfaces.exame_provider_interface import ExameProviderInterface


class ExameCsvProvider(ExameProviderInterface):
    """Provedor de solicitações de exames do AGHU baseado em arquivo CSV oficial."""

    def __init__(self, csv_path: str = "data/exames_aghu_mock.csv") -> None:
        """Inicializa o provedor CSV validando a existência do arquivo."""
        self.csv_path = csv_path
        self._check_file_exists()

    def _check_file_exists(self) -> None:
        """Verifica se o arquivo CSV configurado existe e pode ser aberto."""
        try:
            with open(self.csv_path, mode="r", encoding="utf-8-sig"):
                pass
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Arquivo CSV de exames não encontrado em: {self.csv_path}"
            ) from exc

    @staticmethod
    def _normalize_row(row: Dict[Optional[str], Optional[str]]) -> Dict[str, Any]:
        """Normaliza campos do CSV oficial do AGHU (aspas, prontuário anulável e alias de data)."""
        normalized: Dict[str, Any] = {}
        for key, value in row.items():
            if key is None:
                continue
            clean_key = key.strip()
            if isinstance(value, str):
                clean_value: Optional[str] = value.strip()
                if len(clean_value) >= 2 and clean_value[0] == '"' and clean_value[-1] == '"':
                    clean_value = clean_value[1:-1].replace('""', '"').strip()
            else:
                clean_value = value
            normalized[clean_key] = clean_value

        prontuario = normalized.get("prontuario")
        if prontuario is None or (isinstance(prontuario, str) and prontuario.strip() == ""):
            normalized["prontuario"] = None

        if "data_solicitao" in normalized and "data_solicitacao" not in normalized:
            normalized["data_solicitacao"] = normalized["data_solicitao"]
        elif "data_solicitacao" in normalized and "data_solicitao" not in normalized:
            normalized["data_solicitao"] = normalized["data_solicitacao"]

        id_func = normalized.get("id_funcionario")
        if isinstance(id_func, str) and id_func != "":
            try:
                normalized["id_funcionario"] = int(id_func)
            except ValueError:
                pass
        elif id_func == "":
            normalized["id_funcionario"] = None

        return normalized

    def _read_all_rows(self) -> List[Dict[str, Any]]:
        """Lê e normaliza todas as linhas do arquivo CSV."""
        exames: List[Dict[str, Any]] = []
        with open(self.csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exames.append(self._normalize_row(row))
        return exames

    async def listar_exames(self) -> List[Dict[str, Any]]:
        """Retorna todas as solicitações de exames presentes no CSV."""
        return self._read_all_rows()

    async def buscar_por_solicitacao(
        self, codigo_solicitacao: str
    ) -> List[Dict[str, Any]]:
        """Retorna os itens de exame associados a um código de solicitação."""
        alvo = str(codigo_solicitacao).strip()
        if not alvo:
            return []
        return [
            row
            for row in self._read_all_rows()
            if row.get("codigo_solicitacao") == alvo
        ]

    async def buscar_por_prontuario(self, prontuario: str) -> List[Dict[str, Any]]:
        """Retorna as solicitações de exames associadas a um prontuário."""
        alvo = str(prontuario).strip() if prontuario is not None else ""
        if not alvo:
            return []
        return [
            row
            for row in self._read_all_rows()
            if row.get("prontuario") == alvo
        ]
