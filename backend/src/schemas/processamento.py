from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class IniciarLoteRequest(BaseModel):
    cassete_ids: List[str] = Field(..., min_length=1, description="IDs dos cassetes a incluir no lote")
    responsavel: Optional[str] = None
    observacoes: Optional[str] = None


class ConcluirLoteRequest(BaseModel):
    observacoes: Optional[str] = None


class LoteOut(BaseModel):
    id: str
    responsavel: Optional[str]
    status: str
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    observacoes: Optional[str]
    data_criacao: Optional[datetime]

    model_config = {"from_attributes": True}


class CasseteFilaOut(BaseModel):
    id: str
    letra_fragmento: str
    qr_code: str
    status: str
    codigo_interno_frasco: Optional[str] = None
    numero_solicitacao: Optional[str] = None
    paciente_nome: Optional[str] = None
    data_criacao: Optional[datetime] = None

    model_config = {"from_attributes": True}
