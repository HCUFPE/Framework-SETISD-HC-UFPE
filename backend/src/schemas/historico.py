from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HistoricoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    id_exame: Optional[str] = None
    id_frasco: Optional[str] = None
    id_cassete: Optional[str] = None
    etapa: str
    status_anterior: Optional[str] = None
    status_novo: str
    usuario_responsavel: Optional[str] = None
    timestamp_transicao: Optional[datetime] = None
    ip_origem: Optional[str] = None
    observacoes: Optional[str] = None
