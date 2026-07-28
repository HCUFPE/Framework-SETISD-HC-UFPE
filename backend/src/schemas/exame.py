from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .paciente import PacienteInput


class ExameCreate(BaseModel):
    """Registro de recebimento de peça na triagem."""

    paciente: PacienteInput
    tipo_exame: str = "HP"          # HP | IHQ | HPDerm | CCV | CG | RevInt | Congela
    tipo_peca: Optional[str] = None
    topografia: Optional[str] = None
    numero_exame_aghu: Optional[str] = None


class ExameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    numero_solicitacao: str
    tipo_exame: str
    id_paciente: str
    numero_exame_aghu: Optional[str] = None
    tipo_peca: Optional[str] = None
    topografia: Optional[str] = None
    status: str
    data_recebimento: Optional[datetime] = None


class DashboardExameOut(BaseModel):
    """Estrutura usada pelo dashboard do frontend."""

    id: str
    solicitacao: str        # numero_solicitacao formatado (ex: HP-0001/26.1)
    paciente: str           # nome do paciente (join com pacientes_local)
    etapa: str              # status do exame (bate com ExamStatus do frontend)
    data_entrada: datetime  # data_recebimento — frontend calcula SLA e tempoNaEtapa a partir daqui
    atrasado: bool          # SLA >= 20 dias (calculado pelo backend para facilitar)
    codigo_aghu: Optional[str] = None

