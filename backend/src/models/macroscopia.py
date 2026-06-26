import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..resources.database import Base


class Macroscopia(Base):
    """Registro da etapa de macroscopia de um frasco."""

    __tablename__ = "macroscopias"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_frasco = Column(String, ForeignKey("frascos.id"), nullable=False, index=True)
    descricao = Column(Text, nullable=False)
    data_realizacao = Column(DateTime, server_default=func.now())
    responsavel = Column(String, nullable=True)  # username do JWT (Fase 1)
    numero_cassetes = Column(Integer, nullable=False, default=0)
