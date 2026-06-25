import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..resources.database import Base


class HistoricoMovimentacao(Base):
    """
    Log de auditoria append-only de TODAS as transições de status (RNF010).

    As FKs para os subprodutos são nullable: cada registro referencia o nível
    em que a transição ocorreu (exame, frasco ou cassete). NUNCA deve ser
    deletado ou alterado.
    """

    __tablename__ = "historico_movimentacao"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_exame = Column(String, ForeignKey("exames.id"), nullable=True, index=True)
    id_frasco = Column(String, ForeignKey("frascos.id"), nullable=True, index=True)
    id_cassete = Column(String, ForeignKey("cassetes.id"), nullable=True, index=True)
    etapa = Column(String(50), nullable=False)  # Triagem | Macroscopia | ...
    status_anterior = Column(String, nullable=True)
    status_novo = Column(String, nullable=False)
    usuario_responsavel = Column(String, nullable=True)
    timestamp_transicao = Column(DateTime, server_default=func.now())
    ip_origem = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)
