from sqlalchemy import Column, Integer, String, Date, DateTime
from ..resources.database import Base


class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    codigo = Column(String, primary_key=True, index=True)
    data_retorno = Column(Date)
    unidade_solicitante = Column(String)
    deleted_at = Column(DateTime, nullable=True)
