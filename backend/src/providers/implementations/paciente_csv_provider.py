import csv
from typing import List, Dict, Any
from fastapi import HTTPException, status

from ..interfaces.paciente_provider_interface import PacienteProviderInterface

class PacienteCsvProvider(PacienteProviderInterface):
    def __init__(self, csv_path: str = 'data/pacientes.csv'):
        self.csv_path = csv_path
        self._check_file_exists()

    def _check_file_exists(self):
        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            raise RuntimeError(f"Arquivo CSV de pacientes não encontrado em: {self.csv_path}")

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        pacientes = []
        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Tenta converter o código para int
                    if 'codigo' in row:
                        try:
                            row['codigo'] = int(row['codigo'])
                        except ValueError:
                            pass
                    pacientes.append(row)
        except Exception as e:
            print(f"Erro ao ler CSV: {e}")
        return pacientes

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        current_codigo = int(row.get('codigo', -1))
                        if current_codigo == codigo:
                            # Converte o código no dicionário retornado também
                            row['codigo'] = current_codigo
                            return row
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Erro ao ler CSV: {e}")

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado no CSV")

