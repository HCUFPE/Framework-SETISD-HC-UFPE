"""gestao agendamentos

Revision ID: e7c1a9d4b3f2
Revises: c4f1a7d9e2b3
Create Date: 2026-11-25 16:00:00.000000

Vagas locais, agendamentos, contatos e endereços cifrados (v0.3.0).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7c1a9d4b3f2"
down_revision: Union[str, Sequence[str], None] = "c4f1a7d9e2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria as tabelas de agendamentos e adiciona a chave do paciente."""
    op.add_column("solicitacoes", sa.Column("paciente_chave", sa.String(64), nullable=True))
    op.create_index("ix_solicitacoes_paciente_chave", "solicitacoes", ["paciente_chave"])

    op.create_table(
        "agenda_slots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("unidade", sa.String(300), nullable=False),
        sa.Column("codigo_exame", sa.String(100), nullable=False, server_default=""),
        sa.Column("nome_exame", sa.String(300), nullable=False, server_default=""),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacidade", sa.Integer(), nullable=False),
        sa.Column("situacao", sa.String(20), nullable=False, server_default="DISPONIVEL"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agenda_slots_inicio_unidade_codigo",
        "agenda_slots",
        ["inicio", "unidade", "codigo_exame"],
    )

    op.create_table(
        "agendamentos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("solicitacao_id", sa.String(36), sa.ForeignKey("solicitacoes.id"), nullable=False),
        sa.Column("slot_id", sa.String(36), sa.ForeignKey("agenda_slots.id"), nullable=False),
        sa.Column("paciente_chave", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ATIVO"),
        sa.Column("autor", sa.String(255), nullable=False, server_default=""),
        sa.Column("justificativa", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    for nome, colunas in (
        ("solicitacao_id", ["solicitacao_id"]),
        ("slot_id", ["slot_id"]),
        ("paciente_chave", ["paciente_chave"]),
        ("status", ["status"]),
        ("slot_paciente_status", ["slot_id", "paciente_chave", "status"]),
    ):
        op.create_index(f"ix_agendamentos_{nome}", "agendamentos", colunas)

    op.create_table(
        "contatos_paciente",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("solicitacao_id", sa.String(36), sa.ForeignKey("solicitacoes.id"), nullable=False),
        sa.Column("canal", sa.String(50), nullable=False),
        sa.Column("resultado", sa.String(30), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("operador", sa.String(255), nullable=False, server_default=""),
        sa.Column("realizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_contatos_paciente_solicitacao_id", "contatos_paciente", ["solicitacao_id"])
    op.create_index("ix_contatos_paciente_resultado", "contatos_paciente", ["resultado"])

    op.create_table(
        "paciente_enderecos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("paciente_chave", sa.String(64), nullable=False),
        sa.Column("cep_cripto", sa.Text(), nullable=True),
        sa.Column("logradouro_cripto", sa.Text(), nullable=True),
        sa.Column("numero_cripto", sa.Text(), nullable=True),
        sa.Column("complemento_cripto", sa.Text(), nullable=True),
        sa.Column("bairro_cripto", sa.Text(), nullable=True),
        sa.Column("cidade", sa.String(150), nullable=True),
        sa.Column("estado", sa.String(150), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("distancia_km", sa.Float(), nullable=True),
        sa.Column("distancia_fonte", sa.String(20), nullable=True, server_default="INDISPONIVEL"),
        sa.Column("calculado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_paciente_enderecos_paciente_chave", "paciente_enderecos", ["paciente_chave"])


def downgrade() -> None:
    """Remove as tabelas desta entrega preservando a integração anterior."""
    op.drop_index("ix_paciente_enderecos_paciente_chave", table_name="paciente_enderecos")
    op.drop_table("paciente_enderecos")
    op.drop_index("ix_contatos_paciente_resultado", table_name="contatos_paciente")
    op.drop_index("ix_contatos_paciente_solicitacao_id", table_name="contatos_paciente")
    op.drop_table("contatos_paciente")
    for nome in (
        "slot_paciente_status",
        "status",
        "paciente_chave",
        "slot_id",
        "solicitacao_id",
    ):
        op.drop_index(f"ix_agendamentos_{nome}", table_name="agendamentos")
    op.drop_table("agendamentos")
    op.drop_index("ix_agenda_slots_inicio_unidade_codigo", table_name="agenda_slots")
    op.drop_table("agenda_slots")
    op.drop_index("ix_solicitacoes_paciente_chave", table_name="solicitacoes")
    op.drop_column("solicitacoes", "paciente_chave")
