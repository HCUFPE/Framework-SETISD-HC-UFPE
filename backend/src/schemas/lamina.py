from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel


class LaminaOut(BaseModel):
    id: str
    id_bloco: str
    numero_lamina: int
    codigo_lamina: str
    qr_code: str
    coloracao: str
    status: str
    data_criacao: Optional[datetime]
    criado_por: Optional[str]

    model_config = {"from_attributes": True}


class GerarLaminasResult(BaseModel):
    bloco_id: str
    codigo_bloco: str
    laminas: List[LaminaOut]
    etiquetas: List[dict]
