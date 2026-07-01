from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FrascoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    id_exame: str
    codigo_interno: str
    qr_code: str
    status: str
    descricao_macroscopia: Optional[str] = None
    numero_cassetes_gerados: int
    data_criacao: Optional[datetime] = None


class FrascoDetalhe(BaseModel):
    """
    Frasco enriquecido com dados do exame e do paciente — usado na fila de
    pendências da estação e na busca manual (permite conferência visual).
    """

    id_frasco: str
    id_exame: str
    codigo_interno: str
    status: str
    numero_solicitacao: str
    numero_exame_aghu: Optional[str] = None
    tipo_peca: Optional[str] = None
    paciente_nome: str
    data_criacao: Optional[datetime] = None
