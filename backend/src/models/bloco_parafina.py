import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..resources.database import Base


class BlocoParafina(Base):
    """
    Bloco de parafina gerado após o processamento de um cassete.

    Relação 1:1 com o cassete de origem. O código do bloco é derivado
    do número de solicitação + letra do fragmento, tornando-o legível sem
    depender de scanner (ex.: PATH-2026-000001-A).
    """

    __tablename__ = "blocos_parafina"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_cassete = Column(
        String, ForeignKey("cassetes.id"), unique=True, nullable=False, index=True
    )
    id_lote = Column(
        String, ForeignKey("lotes_processamento.id"), nullable=False, index=True
    )
    codigo_bloco = Column(String, unique=True, nullable=False, index=True)
    qr_code = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="Aguardando Corte")
    data_criacao = Column(DateTime, server_default=func.now())
    criado_por = Column(String, nullable=True)
