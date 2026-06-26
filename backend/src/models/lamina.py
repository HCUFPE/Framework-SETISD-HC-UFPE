import uuid

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from ..resources.database import Base


class Lamina(Base):
    """
    Lâmina histológica gerada a partir do corte microtômico de um bloco.

    Múltiplas lâminas podem ser geradas de um mesmo bloco (colorações
    diferentes, níveis de corte, etc.). O código é composto pelo código
    do bloco + número sequencial (ex.: PATH-2026-000001-A-L1).
    """

    __tablename__ = "laminas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_bloco = Column(
        String, ForeignKey("blocos_parafina.id"), nullable=False, index=True
    )
    numero_lamina = Column(Integer, nullable=False)
    codigo_lamina = Column(String, unique=True, nullable=False, index=True)
    qr_code = Column(String, unique=True, nullable=False, index=True)
    coloracao = Column(String, nullable=False, default="HE")
    status = Column(String, nullable=False, default="Aguardando Leitura")
    data_criacao = Column(DateTime, server_default=func.now())
    criado_por = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("id_bloco", "numero_lamina", name="uq_lamina_bloco_numero"),
    )
