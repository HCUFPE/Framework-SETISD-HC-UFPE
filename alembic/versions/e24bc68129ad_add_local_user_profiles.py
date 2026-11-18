"""Add the local user and profile registry used by RBAC.

Revision ID: e24bc68129ad
Revises: c31f7a92e4b1
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e24bc68129ad"
down_revision: Union[str, Sequence[str], None] = "c31f7a92e4b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria o cadastro local necessário para autorizar identidades autenticadas."""
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("login_institucional", sa.String(length=100), nullable=False),
        sa.Column("nome", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=160), nullable=True),
        sa.Column("lotacao", sa.String(length=160), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login_institucional", name="uq_usuario_login_institucional"),
    )

    op.create_table(
        "perfil",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo", name="uq_perfil_codigo"),
    )

    op.create_table(
        "usuario_perfil",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("perfil_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["perfil_id"], ["perfil.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "perfil_id", name="uq_usuario_perfil"),
    )
    op.create_index("ix_usuario_perfil_usuario_id", "usuario_perfil", ["usuario_id"])
    op.create_index("ix_usuario_perfil_perfil_id", "usuario_perfil", ["perfil_id"])


def downgrade() -> None:
    """Remove as tabelas de cadastro local em ordem segura de dependência."""
    op.drop_index("ix_usuario_perfil_perfil_id", table_name="usuario_perfil")
    op.drop_index("ix_usuario_perfil_usuario_id", table_name="usuario_perfil")
    op.drop_table("usuario_perfil")
    op.drop_table("perfil")
    op.drop_table("usuario")
