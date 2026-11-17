"""Add persistent data for existing AP Reception operations.

Revision ID: c31f7a92e4b1
Revises: 8a2efbe37bb6
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c31f7a92e4b1"
down_revision: Union[str, Sequence[str], None] = "8a2efbe37bb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tabelas do domínio AP e garante a tabela de auditoria compartilhada."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("usuario", sa.String(), nullable=False),
            sa.Column("categoria", sa.String(), nullable=False),
            sa.Column("acao", sa.String(), nullable=False),
            sa.Column("recurso", sa.String(), nullable=False),
            sa.Column("dados_anteriores", sa.Text(), nullable=True),
            sa.Column("dados_novos", sa.Text(), nullable=True),
            sa.Column("ip_origem", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
        op.create_index("ix_audit_logs_usuario", "audit_logs", ["usuario"])
        op.create_index("ix_audit_logs_categoria", "audit_logs", ["categoria"])
        op.create_index("ix_audit_logs_acao", "audit_logs", ["acao"])
        op.create_index("ix_audit_logs_recurso", "audit_logs", ["recurso"])

    op.create_table(
        "ap_solicitacoes",
        sa.Column("codigo_solicitacao", sa.String(length=60), nullable=False),
        sa.Column("situacao_recepcao", sa.String(length=40), nullable=False),
        sa.Column("data_solicitacao", sa.String(length=40), nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=True),
        sa.Column("ihq_codigo", sa.String(length=40), nullable=True),
        sa.Column("ihq_caso_numero", sa.String(length=40), nullable=True),
        sa.Column("devolucao_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("codigo_solicitacao"),
    )
    op.create_index("ix_ap_solicitacoes_situacao_recepcao", "ap_solicitacoes", ["situacao_recepcao"])
    op.create_index("ix_ap_solicitacoes_data_solicitacao", "ap_solicitacoes", ["data_solicitacao"])

    op.create_table(
        "ap_casos",
        sa.Column("numero_interno", sa.String(length=40), nullable=False),
        sa.Column("solicitacao_codigo", sa.String(length=60), nullable=False),
        sa.Column("tipo_exame", sa.String(length=12), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("data_entrada", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["solicitacao_codigo"], ["ap_solicitacoes.codigo_solicitacao"]),
        sa.PrimaryKeyConstraint("numero_interno"),
        sa.UniqueConstraint("solicitacao_codigo", name="uq_ap_caso_solicitacao"),
    )
    op.create_index("ix_ap_casos_solicitacao_codigo", "ap_casos", ["solicitacao_codigo"])
    op.create_index("ix_ap_casos_tipo_exame", "ap_casos", ["tipo_exame"])
    op.create_index("ix_ap_casos_status", "ap_casos", ["status"])
    op.create_index("ix_ap_casos_data_entrada", "ap_casos", ["data_entrada"])

    op.create_table(
        "ap_conferencias_recebimento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("solicitacao_codigo", sa.String(length=60), nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=True),
        sa.Column("resultado", sa.String(length=20), nullable=False),
        sa.Column("conferido_em", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["solicitacao_codigo"], ["ap_solicitacoes.codigo_solicitacao"]),
        sa.ForeignKeyConstraint(["caso_numero"], ["ap_casos.numero_interno"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ap_conferencias_recebimento_solicitacao_codigo", "ap_conferencias_recebimento", ["solicitacao_codigo"])
    op.create_index("ix_ap_conferencias_recebimento_caso_numero", "ap_conferencias_recebimento", ["caso_numero"])
    op.create_index("ix_ap_conferencias_recebimento_resultado", "ap_conferencias_recebimento", ["resultado"])

    op.create_table(
        "ap_itens_material",
        sa.Column("codigo", sa.String(length=80), nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=False),
        sa.Column("codigo_pai", sa.String(length=80), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["caso_numero"], ["ap_casos.numero_interno"]),
        sa.ForeignKeyConstraint(["codigo_pai"], ["ap_itens_material.codigo"]),
        sa.PrimaryKeyConstraint("codigo"),
    )
    op.create_index("ix_ap_itens_material_caso_numero", "ap_itens_material", ["caso_numero"])

    op.create_table(
        "ap_exames_ihq",
        sa.Column("codigo_interno", sa.String(length=40), nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=False),
        sa.Column("solicitacao_codigo", sa.String(length=60), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["caso_numero"], ["ap_casos.numero_interno"]),
        sa.ForeignKeyConstraint(["solicitacao_codigo"], ["ap_solicitacoes.codigo_solicitacao"]),
        sa.PrimaryKeyConstraint("codigo_interno"),
        sa.UniqueConstraint("solicitacao_codigo"),
    )
    op.create_index("ix_ap_exames_ihq_caso_numero", "ap_exames_ihq", ["caso_numero"])

    op.create_table(
        "ap_nao_conformidades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=True),
        sa.Column("solicitacao_codigo", sa.String(length=60), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["caso_numero"], ["ap_casos.numero_interno"]),
        sa.ForeignKeyConstraint(["solicitacao_codigo"], ["ap_solicitacoes.codigo_solicitacao"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ap_nao_conformidades_caso_numero", "ap_nao_conformidades", ["caso_numero"])
    op.create_index("ix_ap_nao_conformidades_solicitacao_codigo", "ap_nao_conformidades", ["solicitacao_codigo"])
    op.create_index("ix_ap_nao_conformidades_status", "ap_nao_conformidades", ["status"])

    op.create_table(
        "ap_devolucoes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nao_conformidade_id", sa.Integer(), nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=True),
        sa.Column("solicitacao_codigo", sa.String(length=60), nullable=True),
        sa.Column("situacao", sa.String(length=40), nullable=False),
        sa.Column("devolvida_em", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["nao_conformidade_id"], ["ap_nao_conformidades.id"]),
        sa.ForeignKeyConstraint(["caso_numero"], ["ap_casos.numero_interno"]),
        sa.ForeignKeyConstraint(["solicitacao_codigo"], ["ap_solicitacoes.codigo_solicitacao"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ap_devolucoes_nao_conformidade_id", "ap_devolucoes", ["nao_conformidade_id"])
    op.create_index("ix_ap_devolucoes_caso_numero", "ap_devolucoes", ["caso_numero"])
    op.create_index("ix_ap_devolucoes_solicitacao_codigo", "ap_devolucoes", ["solicitacao_codigo"])
    op.create_index("ix_ap_devolucoes_situacao", "ap_devolucoes", ["situacao"])
    op.create_index("ix_ap_devolucoes_devolvida_em", "ap_devolucoes", ["devolvida_em"])

    op.create_table(
        "ap_historico_caso",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("caso_numero", sa.String(length=40), nullable=False),
        sa.Column("ocorrido_em", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["caso_numero"], ["ap_casos.numero_interno"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ap_historico_caso_caso_numero", "ap_historico_caso", ["caso_numero"])
    op.create_index("ix_ap_historico_caso_ocorrido_em", "ap_historico_caso", ["ocorrido_em"])


def downgrade() -> None:
    """Remove tabelas de Recepção, preservando a trilha unificada de auditoria."""
    op.drop_index("ix_ap_historico_caso_ocorrido_em", table_name="ap_historico_caso")
    op.drop_index("ix_ap_historico_caso_caso_numero", table_name="ap_historico_caso")
    op.drop_table("ap_historico_caso")
    op.drop_index("ix_ap_devolucoes_devolvida_em", table_name="ap_devolucoes")
    op.drop_index("ix_ap_devolucoes_situacao", table_name="ap_devolucoes")
    op.drop_index("ix_ap_devolucoes_solicitacao_codigo", table_name="ap_devolucoes")
    op.drop_index("ix_ap_devolucoes_caso_numero", table_name="ap_devolucoes")
    op.drop_index("ix_ap_devolucoes_nao_conformidade_id", table_name="ap_devolucoes")
    op.drop_table("ap_devolucoes")
    op.drop_index("ix_ap_nao_conformidades_status", table_name="ap_nao_conformidades")
    op.drop_index("ix_ap_nao_conformidades_solicitacao_codigo", table_name="ap_nao_conformidades")
    op.drop_index("ix_ap_nao_conformidades_caso_numero", table_name="ap_nao_conformidades")
    op.drop_table("ap_nao_conformidades")
    op.drop_index("ix_ap_exames_ihq_caso_numero", table_name="ap_exames_ihq")
    op.drop_table("ap_exames_ihq")
    op.drop_index("ix_ap_itens_material_caso_numero", table_name="ap_itens_material")
    op.drop_table("ap_itens_material")
    op.drop_index("ix_ap_conferencias_recebimento_resultado", table_name="ap_conferencias_recebimento")
    op.drop_index("ix_ap_conferencias_recebimento_caso_numero", table_name="ap_conferencias_recebimento")
    op.drop_index("ix_ap_conferencias_recebimento_solicitacao_codigo", table_name="ap_conferencias_recebimento")
    op.drop_table("ap_conferencias_recebimento")
    op.drop_index("ix_ap_casos_data_entrada", table_name="ap_casos")
    op.drop_index("ix_ap_casos_status", table_name="ap_casos")
    op.drop_index("ix_ap_casos_tipo_exame", table_name="ap_casos")
    op.drop_index("ix_ap_casos_solicitacao_codigo", table_name="ap_casos")
    op.drop_table("ap_casos")
    op.drop_index("ix_ap_solicitacoes_data_solicitacao", table_name="ap_solicitacoes")
    op.drop_index("ix_ap_solicitacoes_situacao_recepcao", table_name="ap_solicitacoes")
    op.drop_table("ap_solicitacoes")
