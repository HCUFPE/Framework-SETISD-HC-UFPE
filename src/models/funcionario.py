from sqlalchemy import Column, String, Integer, DateTime
from ..resources.database import Base


class Funcionario(Base):
    __tablename__ = "funcionarios"

    id = Column(String, primary_key=True, index=True)
    deleted_at = Column(DateTime, nullable=True)
