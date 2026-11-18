"""Cadastro local de usuários e perfis usados na autorização do Sistema AP."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..resources.database import Base


class Usuario(Base):
    """Identidade institucional pré-cadastrada e habilitada para acessar a aplicação."""

    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login_institucional: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    lotacao: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Perfil(Base):
    """Catálogo de perfis locais; permissões do catálogo ficam em authorization.py."""

    __tablename__ = "perfil"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UsuarioPerfil(Base):
    """Atribuição persistente de um perfil local a uma identidade institucional."""

    __tablename__ = "usuario_perfil"
    __table_args__ = (UniqueConstraint("usuario_id", "perfil_id", name="uq_usuario_perfil"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False, index=True)
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfil.id"), nullable=False, index=True)
