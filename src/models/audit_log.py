"""
Modelo SQLAlchemy de Auditoria e Trilha de Mudanças (Audit Log)
================================================================
Registra de forma estruturada e imutável as ações de mutação (criação, alteração, exclusão,
troca de privilégios) realizadas por usuários no sistema.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from ..resources.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    usuario = Column(String, nullable=False, index=True)
    categoria = Column(String, nullable=False, index=True)  # SEGURANCA, NEGOCIO_CLINICO, CONFIGURACAO
    acao = Column(String, nullable=False, index=True)       # ex: ALTERAR_PERFIL, CRIAR_PACIENTE
    recurso = Column(String, nullable=False, index=True)    # ex: usuario:joao.silva, paciente:123
    dados_anteriores = Column(Text, nullable=True)          # JSON serializado do estado BEFORE
    dados_novos = Column(Text, nullable=True)               # JSON serializado do estado AFTER
    ip_origem = Column(String, nullable=True)

    def __repr__(self):
        return f"<AuditLog id={self.id} usuario={self.usuario} acao={self.acao} recurso={self.recurso}>"
