from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class PacienteInput(BaseModel):
    """Dados de paciente informados na triagem (SUS) ou importados (HC)."""

    nome: str
    cpf: Optional[str] = None
    cns: Optional[str] = None
    data_nascimento: Optional[date] = None
    origem: Literal["SUS", "HC"] = "SUS"


class PacienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    cpf: Optional[str] = None
    cns: Optional[str] = None
    data_nascimento: Optional[date] = None
    origem: str
