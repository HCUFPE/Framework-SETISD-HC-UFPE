import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from ..resources.database import Base


class LoteProcessamento(Base):
    """
    Ciclo de processamento técnico de tecidos (tambor/estufa).

    Um lote agrupa N cassetes que entram juntos no processador automático.
    Criado pelo técnico ao iniciar o ciclo; concluído no dia seguinte ao
    retirar os blocos de parafina.
    """

    __tablename__ = "lotes_processamento"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    responsavel = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Em Andamento")
    data_inicio = Column(DateTime, nullable=False, server_default=func.now())
    data_fim = Column(DateTime, nullable=True)
    observacoes = Column(Text, nullable=True)
    data_criacao = Column(DateTime, server_default=func.now())
