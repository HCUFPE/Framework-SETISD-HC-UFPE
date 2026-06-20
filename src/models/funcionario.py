from sqlalchemy import Column, Integer, DateTime
from ..resources.database import Base


class Funcionario(Base):
    __tablename__ = "funcionarios"

    id = Column(Integer, primary_key=True, index=True)
    deleted_at = Column(DateTime, nullable=True)
