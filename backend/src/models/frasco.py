import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..resources.database import Base


class Frasco(Base):
    """
    Peça matriz recebida na triagem (1 frasco : 1 exame nesta fase).

    `qr_code` é a string de identificação gerada já agora
    (formato TIPO|UUID|PATH-AAAA-XXXXXX|timestamp). Ela é independente de
    hardware: quando a impressora chegar, será apenas renderizada como imagem;
    quando o leitor chegar, será apenas digitada no campo de busca.
    """

    __tablename__ = "frascos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_exame = Column(String, ForeignKey("exames.id"), nullable=False, index=True)
    codigo_interno = Column(String, unique=True, index=True, nullable=False)
    qr_code = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False, default="Na Recepção")
    descricao_macroscopia = Column(Text, nullable=True)
    numero_cassetes_gerados = Column(Integer, nullable=False, default=0)
    data_criacao = Column(DateTime, server_default=func.now())
    criado_por = Column(String, nullable=True)
    data_atualizacao = Column(DateTime, onupdate=func.now(), nullable=True)
