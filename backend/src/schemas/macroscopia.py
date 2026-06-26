from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MacroscopiaCreate(BaseModel):
    """Registro da macroscopia de um frasco + quantidade de cassetes a gerar."""

    id_frasco: str
    descricao: str
    numero_cassetes: int = Field(gt=0, le=200)


class MacroscopiaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    id_frasco: str
    descricao: str
    data_realizacao: Optional[datetime] = None
    responsavel: Optional[str] = None
    numero_cassetes: int
