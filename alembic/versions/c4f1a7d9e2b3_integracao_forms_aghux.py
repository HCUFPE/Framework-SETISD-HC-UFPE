"""integracao forms aghux

Revision ID: c4f1a7d9e2b3
Revises: 8a2efbe37bb6
Create Date: 2026-11-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4f1a7d9e2b3"
down_revision: Union[str, Sequence[str], None] = "8a2efbe37bb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria as tabelas da integração Forms → AGHUX."""
    op.create_table(
        "forms_responses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("response_id", sa.String(255), nullable=False),
        sa.Column("form_id", sa.String(255), nullable=False),
        sa.Column("payload_cripto", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDENTE"),
        sa.Column("tentativas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ultimo_erro", sa.Text(), nullable=True),
        sa.Column("ip_origem", sa.String(64), nullable=True),
        sa.Column("recebido_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("solicitacao_id", sa.String(36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_forms_responses_response_id", "forms_responses", ["response_id"], unique=True)
    op.create_index("ix_forms_responses_form_id", "forms_responses", ["form_id"])
    op.create_index("ix_forms_responses_status", "forms_responses", ["status"])
    op.create_index("ix_forms_responses_solicitacao_id", "forms_responses", ["solicitacao_id"])

    op.create_table(
        "webhook_nonces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nonce", sa.String(255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_webhook_nonces_nonce", "webhook_nonces", ["nonce"], unique=True)

    op.create_table(
        "solicitacoes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("protocolo", sa.String(100), nullable=False),
        sa.Column("forms_response_id", sa.String(255), nullable=True),
        sa.Column("codigo_solicitacao_aghux", sa.String(100), nullable=True),
        sa.Column("prontuario", sa.String(100), nullable=True),
        sa.Column("paciente_nome", sa.String(300), nullable=False),
        sa.Column("telefone", sa.String(50), nullable=True),
        sa.Column("cidade", sa.String(150), nullable=True),
        sa.Column("estado", sa.String(150), nullable=True),
        sa.Column("cpf_cripto", sa.Text(), nullable=True),
        sa.Column("cns_cripto", sa.Text(), nullable=True),
        sa.Column("cpf_hash", sa.String(64), nullable=True),
        sa.Column("cns_hash", sa.String(64), nullable=True),
        sa.Column("exame", sa.String(300), nullable=False),
        sa.Column("itens_exame", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("tipo_exame", sa.String(150), nullable=True),
        sa.Column("setor_solicitante", sa.String(300), nullable=True),
        sa.Column("solicitante_codigo", sa.String(100), nullable=True),
        sa.Column("solicitante_nome", sa.String(300), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="RECEBIDA"),
        sa.Column("pontuacao", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prioridade", sa.String(10), nullable=False, server_default="BAIXA"),
        sa.Column("recebida_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    for nome in ("protocolo", "forms_response_id", "codigo_solicitacao_aghux", "prontuario",
                 "cpf_hash", "cns_hash", "status", "recebida_em"):
        op.create_index(f"ix_solicitacoes_{nome}", "solicitacoes", [nome], unique=(nome == "forms_response_id"))
    op.create_index("ix_solicitacoes_ativas_prontuario", "solicitacoes", ["prontuario", "deleted_at"])

    op.create_table(
        "solicitacao_itens_exame",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("solicitacao_id", sa.String(36), sa.ForeignKey("solicitacoes.id"), nullable=False),
        sa.Column("codigo_exame", sa.String(100), nullable=False),
        sa.Column("nome_exame", sa.String(300), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_solicitacao_itens_exame_solicitacao_id", "solicitacao_itens_exame", ["solicitacao_id"])

    op.create_table(
        "divergencias",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("solicitacao_id", sa.String(36), sa.ForeignKey("solicitacoes.id"), nullable=False),
        sa.Column("campo", sa.String(150), nullable=False),
        sa.Column("valor_formulario", sa.Text(), nullable=True),
        sa.Column("valor_aghux", sa.Text(), nullable=True),
        sa.Column("tratada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("justificativa", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_divergencias_solicitacao_id", "divergencias", ["solicitacao_id"])

    op.create_table(
        "alertas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("solicitacao_id", sa.String(36), sa.ForeignKey("solicitacoes.id"), nullable=False),
        sa.Column("campo", sa.String(150), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("severidade", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alertas_solicitacao_id", "alertas", ["solicitacao_id"])


def downgrade() -> None:
    """Remove as tabelas da integração preservando as demais."""
    op.drop_index("ix_alertas_solicitacao_id", table_name="alertas")
    op.drop_table("alertas")
    op.drop_index("ix_divergencias_solicitacao_id", table_name="divergencias")
    op.drop_table("divergencias")
    op.drop_index("ix_solicitacao_itens_exame_solicitacao_id", table_name="solicitacao_itens_exame")
    op.drop_table("solicitacao_itens_exame")
    for nome in ("protocolo", "forms_response_id", "codigo_solicitacao_aghux", "prontuario",
                 "cpf_hash", "cns_hash", "status", "recebida_em"):
        op.drop_index(f"ix_solicitacoes_{nome}", table_name="solicitacoes")
    op.drop_index("ix_solicitacoes_ativas_prontuario", table_name="solicitacoes")
    op.drop_table("solicitacoes")
    op.drop_index("ix_webhook_nonces_nonce", table_name="webhook_nonces")
    op.drop_table("webhook_nonces")
    for nome in ("response_id", "form_id", "status", "solicitacao_id"):
        op.drop_index(f"ix_forms_responses_{nome}", table_name="forms_responses")
    op.drop_table("forms_responses")
