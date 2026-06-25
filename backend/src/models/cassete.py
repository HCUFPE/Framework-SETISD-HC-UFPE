import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.sql import func

from ..resources.database import Base


class Cassete(Base):
    """
    Fragmento clivado da peça, gerado na macroscopia (N cassetes : 1 frasco).

    Identificado pela letra do fragmento (A, B, C, ...) única dentro do frasco,
    e por um `qr_code` único global gerado na criação.
    """

    __tablename__ = "cassetes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_frasco = Column(String, ForeignKey("frascos.id"), nullable=False, index=True)
    letra_fragmento = Column(String, nullable=False)
    qr_code = Column(String, unique=True, index=True, nullable=False)
    coloracao_padrao = Column(String, nullable=False, default="HE")
    status = Column(String, nullable=False, default="Aguardando Processamento")
    id_lote_processamento = Column(
        String, ForeignKey("lotes_processamento.id"), nullable=True, index=True
    )
    data_criacao = Column(DateTime, server_default=func.now())
    criado_por = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("id_frasco", "letra_fragmento", name="uq_cassete_frasco_letra"),
    )
