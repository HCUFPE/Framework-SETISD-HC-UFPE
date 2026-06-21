from sqlalchemy import Column, Integer, String, DateTime
from ..resources.database import Base


class Exame(Base):
    __tablename__ = "exames"

    codigo = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
