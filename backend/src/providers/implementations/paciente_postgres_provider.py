import os
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..interfaces.paciente_provider_interface import PacienteProviderInterface

def get_sql_query(file_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Ajuste no caminho para voltar dois níveis (implementations -> providers -> src) e depois entrar em providers/sql
    sql_file_path = os.path.join(base_dir, '..', 'sql', file_path)
    try:
        with open(sql_file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Arquivo SQL não encontrado em: {sql_file_path}")

class PacientePostgresProvider(PacienteProviderInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        query_string = get_sql_query("paciente/listar_pacientes.sql")
        query = text(query_string)
        
        result = await self.session.execute(query)
        pacientes = result.mappings().all()
        return [dict(paciente) for paciente in pacientes]

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        query_string = get_sql_query("paciente/obter_paciente.sql")
        query = text(query_string)
        
        result = await self.session.execute(query, {"codigo": codigo})
        paciente = result.mappings().first()
        
        if not paciente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado")
            
        return dict(paciente)
