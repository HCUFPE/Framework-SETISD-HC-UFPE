"""fase2 processamento: lote_processamento, bloco_parafina, lamina, cassete_id_lote

Revision ID: a466fca0bf59
Revises: 05efce119b89
Create Date: 2026-06-23 15:20:35.313862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a466fca0bf59'
down_revision: Union[str, Sequence[str], None] = '05efce119b89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tabelas do Processamento Técnico (Fase 2) e adiciona FK em cassetes."""
    op.create_table(
        "lotes_processamento",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("responsavel", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data_inicio", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("data_fim", sa.DateTime(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("data_criacao", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "blocos_parafina",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("id_cassete", sa.String(), nullable=False),
        sa.Column("id_lote", sa.String(), nullable=False),
        sa.Column("codigo_bloco", sa.String(), nullable=False),
        sa.Column("qr_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data_criacao", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("criado_por", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["id_cassete"], ["cassetes.id"]),
        sa.ForeignKeyConstraint(["id_lote"], ["lotes_processamento.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_cassete"),
    )
    op.create_index("ix_blocos_parafina_id_cassete", "blocos_parafina", ["id_cassete"], unique=True)
    op.create_index("ix_blocos_parafina_id_lote", "blocos_parafina", ["id_lote"], unique=False)
    op.create_index("ix_blocos_parafina_codigo_bloco", "blocos_parafina", ["codigo_bloco"], unique=True)
    op.create_index("ix_blocos_parafina_qr_code", "blocos_parafina", ["qr_code"], unique=True)

    op.create_table(
        "laminas",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("id_bloco", sa.String(), nullable=False),
        sa.Column("numero_lamina", sa.Integer(), nullable=False),
        sa.Column("codigo_lamina", sa.String(), nullable=False),
        sa.Column("qr_code", sa.String(), nullable=False),
        sa.Column("coloracao", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data_criacao", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("criado_por", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["id_bloco"], ["blocos_parafina.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_bloco", "numero_lamina", name="uq_lamina_bloco_numero"),
    )
    op.create_index("ix_laminas_id_bloco", "laminas", ["id_bloco"], unique=False)
    op.create_index("ix_laminas_codigo_lamina", "laminas", ["codigo_lamina"], unique=True)
    op.create_index("ix_laminas_qr_code", "laminas", ["qr_code"], unique=True)

    # Adiciona FK do lote no cassete
    op.add_column("cassetes", sa.Column("id_lote_processamento", sa.String(), nullable=True))
    op.create_index("ix_cassetes_id_lote_processamento", "cassetes", ["id_lote_processamento"], unique=False)


def downgrade() -> None:
    """Remove tabelas do Processamento Técnico (Fase 2)."""
    op.drop_index("ix_cassetes_id_lote_processamento", table_name="cassetes")
    op.drop_column("cassetes", "id_lote_processamento")

    op.drop_index("ix_laminas_qr_code", table_name="laminas")
    op.drop_index("ix_laminas_codigo_lamina", table_name="laminas")
    op.drop_index("ix_laminas_id_bloco", table_name="laminas")
    op.drop_table("laminas")

    op.drop_index("ix_blocos_parafina_qr_code", table_name="blocos_parafina")
    op.drop_index("ix_blocos_parafina_codigo_bloco", table_name="blocos_parafina")
    op.drop_index("ix_blocos_parafina_id_lote", table_name="blocos_parafina")
    op.drop_index("ix_blocos_parafina_id_cassete", table_name="blocos_parafina")
    op.drop_table("blocos_parafina")

    op.drop_table("lotes_processamento")
