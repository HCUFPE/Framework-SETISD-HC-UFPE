import uuid

from sqlalchemy import Column, String, Date, Boolean, DateTime
from sqlalchemy.sql import func

from ..resources.database import Base


class PacienteLocal(Base):
    """
    Cache local de pacientes (ADR 004).

    - Pacientes do HC são importados do AGHU (somente leitura) e cacheados aqui.
    - Pacientes SUS são cadastrados diretamente na triagem.

    `cpf` e `cns` são únicos quando preenchidos; ao menos um deve existir
    (validado na camada de controller).
    """

    __tablename__ = "pacientes_local"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cpf = Column(String(11), unique=True, index=True, nullable=True)
    cns = Column(String(15), unique=True, index=True, nullable=True)
    nome = Column(String, nullable=False)
    data_nascimento = Column(Date, nullable=True)
    origem = Column(String, nullable=False, default="SUS")  # "SUS" | "HC"
    ativo = Column(Boolean, nullable=False, default=True)  # soft delete
    data_criacao = Column(DateTime, server_default=func.now())
    criado_por = Column(String, nullable=True)
