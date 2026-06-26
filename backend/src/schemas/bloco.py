from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class GerarLaminasRequest(BaseModel):
    quantidade: int = Field(default=1, ge=1, le=20, description="Número de lâminas a gerar")
    coloracao: str = Field(default="HE", description="Coloração padrão (HE, PAS, Giemsa...)")


class BlocoOut(BaseModel):
    id: str
    id_cassete: str
    id_lote: str
    codigo_bloco: str
    qr_code: str
    status: str
    data_criacao: Optional[datetime]
    criado_por: Optional[str]

    model_config = {"from_attributes": True}


class BlocoDetalhe(BaseModel):
    id: str
    codigo_bloco: str
    status: str
    letra_fragmento: Optional[str] = None
    numero_solicitacao: Optional[str] = None
    paciente_nome: Optional[str] = None
    data_criacao: Optional[datetime] = None

    model_config = {"from_attributes": True}
