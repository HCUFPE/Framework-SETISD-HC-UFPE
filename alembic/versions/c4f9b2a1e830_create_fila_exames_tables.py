"""create fila exames tables

Revision ID: c4f9b2a1e830
Revises: 8a2efbe37bb6
Create Date: 2026-11-25 19:52:30.000000

Cria as 5 tabelas locais do Sistema de Gestão de Fila de Exames (HC-UFPE):
- importacoes_forms
- regras_prioridade
- regras_exames
- acompanhamento_fila (FK -> importacoes_forms.id)
- incompatibilidades_exames (FK -> regras_exames.codigo_exame)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4f9b2a1e830"
down_revision: Union[str, Sequence[str], None] = "8a2efbe37bb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica a criação das 5 tabelas de gestão da fila de exames."""
    # 1. importacoes_forms (tabela pai de acompanhamento_fila)
    op.create_table(
        "importacoes_forms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("importado_em", sa.DateTime(), nullable=False),
        sa.Column("usuario_importador", sa.String(length=120), nullable=False),
        sa.Column("total_linhas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_validas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_duplicadas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_erros", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "total_linhas >= 0",
            name="ck_importacoes_forms_total_linhas_non_negative",
        ),
        sa.CheckConstraint(
            "total_validas >= 0",
            name="ck_importacoes_forms_total_validas_non_negative",
        ),
        sa.CheckConstraint(
            "total_duplicadas >= 0",
            name="ck_importacoes_forms_total_duplicadas_non_negative",
        ),
        sa.CheckConstraint(
            "total_erros >= 0",
            name="ck_importacoes_forms_total_erros_non_negative",
        ),
    )
    op.create_index(
        op.f("ix_importacoes_forms_id"),
        "importacoes_forms",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_importacoes_forms_importado_em"),
        "importacoes_forms",
        ["importado_em"],
        unique=False,
    )
    op.create_index(
        op.f("ix_importacoes_forms_usuario_importador"),
        "importacoes_forms",
        ["usuario_importador"],
        unique=False,
    )
    op.create_index(
        op.f("ix_importacoes_forms_deleted_at"),
        "importacoes_forms",
        ["deleted_at"],
        unique=False,
    )

    # 2. regras_prioridade
    op.create_table(
        "regras_prioridade",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo", sa.String(length=100), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo_criterio", sa.String(length=50), nullable=False),
        sa.Column("valor_match", sa.String(length=255), nullable=True),
        sa.Column("peso", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "tipo_criterio IN ('CLINICA', 'GRUPO_CLINICO', 'VULNERAVEL', "
            "'AFINIDADE_EXAME', 'RETORNO_PROXIMO')",
            name="ck_regras_prioridade_tipo_criterio",
        ),
        sa.CheckConstraint(
            "peso >= 0 AND peso <= 1000",
            name="ck_regras_prioridade_peso_range",
        ),
    )
    op.create_index(
        op.f("ix_regras_prioridade_id"),
        "regras_prioridade",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_regras_prioridade_codigo"),
        "regras_prioridade",
        ["codigo"],
        unique=True,
    )
    op.create_index(
        op.f("ix_regras_prioridade_tipo_criterio"),
        "regras_prioridade",
        ["tipo_criterio"],
        unique=False,
    )
    op.create_index(
        op.f("ix_regras_prioridade_ativo"),
        "regras_prioridade",
        ["ativo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_regras_prioridade_deleted_at"),
        "regras_prioridade",
        ["deleted_at"],
        unique=False,
    )

    # 3. regras_exames (tabela pai de incompatibilidades_exames)
    op.create_table(
        "regras_exames",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo_exame", sa.String(length=50), nullable=False),
        sa.Column("nome_exame", sa.String(length=255), nullable=False),
        sa.Column("unidade_executora", sa.String(length=255), nullable=True),
        sa.Column("antecedencia_minima_dias", sa.Integer(), nullable=False),
        sa.Column("janela_retorno_max_horas", sa.Integer(), nullable=True),
        sa.Column("exige_jejum", sa.Boolean(), nullable=False),
        sa.Column("priorizar_manha_diabetico", sa.Boolean(), nullable=False),
        sa.Column("idade_minima_alerta", sa.Integer(), nullable=True),
        sa.Column("orientacoes_preparo", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "antecedencia_minima_dias >= 0",
            name="ck_regras_exames_antecedencia_minima_dias",
        ),
        sa.CheckConstraint(
            "janela_retorno_max_horas IS NULL OR janela_retorno_max_horas >= 0",
            name="ck_regras_exames_janela_retorno_max_horas",
        ),
        sa.CheckConstraint(
            "idade_minima_alerta IS NULL OR idade_minima_alerta >= 0",
            name="ck_regras_exames_idade_minima_alerta",
        ),
    )
    op.create_index(
        op.f("ix_regras_exames_id"),
        "regras_exames",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_regras_exames_codigo_exame"),
        "regras_exames",
        ["codigo_exame"],
        unique=True,
    )
    op.create_index(
        op.f("ix_regras_exames_unidade_executora"),
        "regras_exames",
        ["unidade_executora"],
        unique=False,
    )
    op.create_index(
        op.f("ix_regras_exames_ativo"),
        "regras_exames",
        ["ativo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_regras_exames_deleted_at"),
        "regras_exames",
        ["deleted_at"],
        unique=False,
    )

    # 4. acompanhamento_fila (filha de importacoes_forms)
    op.create_table(
        "acompanhamento_fila",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("importacao_id", sa.Integer(), nullable=True),
        sa.Column("codigo_solicitacao", sa.String(length=64), nullable=False),
        sa.Column("codigo_exame", sa.String(length=64), nullable=True),
        sa.Column("prontuario", sa.String(length=64), nullable=True),
        sa.Column("nome_paciente", sa.String(length=255), nullable=False),
        sa.Column("telefone_contato", sa.String(length=64), nullable=True),
        sa.Column("municipio", sa.String(length=120), nullable=True),
        sa.Column(
            "regiao_geografica",
            sa.String(length=32),
            server_default="NAO_INFORMADO",
            nullable=False,
        ),
        sa.Column(
            "utiliza_tfd",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("data_retorno_medico", sa.Date(), nullable=True),
        sa.Column("exame_informado_forms", sa.String(length=255), nullable=True),
        sa.Column("unidade_solicitante", sa.String(length=255), nullable=True),
        sa.Column("especialidade_solicitante", sa.String(length=255), nullable=True),
        sa.Column(
            "flag_hemodialise",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "flag_diabetico_jejum",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("grupo_prioritario_manual", sa.String(length=120), nullable=True),
        sa.Column(
            "status_higienizacao",
            sa.String(length=32),
            server_default="VALIDA",
            nullable=False,
        ),
        sa.Column(
            "status_operacional",
            sa.String(length=32),
            server_default="NA_FILA",
            nullable=False,
        ),
        sa.Column("contato_iniciado_em", sa.DateTime(), nullable=True),
        sa.Column("prazo_confirmacao_em", sa.DateTime(), nullable=True),
        sa.Column("data_agendada_aghu", sa.DateTime(), nullable=True),
        sa.Column(
            "preparo_orientado",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["importacao_id"],
            ["importacoes_forms.id"],
            name="fk_acompanhamento_fila_importacao_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "regiao_geografica IN ('CAPITAL', 'RMR', 'INTERIOR', 'NAO_INFORMADO')",
            name="ck_acompanhamento_fila_regiao_geografica",
        ),
        sa.CheckConstraint(
            "status_higienizacao IN "
            "('VALIDA', 'DUPLICADA', 'DIVERGENCIA_EXAME', 'NAO_ENCONTRADA', 'JA_REALIZADA')",
            name="ck_acompanhamento_fila_status_higienizacao",
        ),
        sa.CheckConstraint(
            "status_operacional IN "
            "('NA_FILA', 'AGUARDANDO_CONFIRMACAO_24H', 'CONFIRMADO_AGENDADO_AGHU', "
            "'SEM_RESPOSTA_24H', 'CANCELADO')",
            name="ck_acompanhamento_fila_status_operacional",
        ),
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_id"),
        "acompanhamento_fila",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_importacao_id"),
        "acompanhamento_fila",
        ["importacao_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_codigo_solicitacao"),
        "acompanhamento_fila",
        ["codigo_solicitacao"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_codigo_exame"),
        "acompanhamento_fila",
        ["codigo_exame"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_prontuario"),
        "acompanhamento_fila",
        ["prontuario"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_nome_paciente"),
        "acompanhamento_fila",
        ["nome_paciente"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_municipio"),
        "acompanhamento_fila",
        ["municipio"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_regiao_geografica"),
        "acompanhamento_fila",
        ["regiao_geografica"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_utiliza_tfd"),
        "acompanhamento_fila",
        ["utiliza_tfd"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_data_retorno_medico"),
        "acompanhamento_fila",
        ["data_retorno_medico"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_unidade_solicitante"),
        "acompanhamento_fila",
        ["unidade_solicitante"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_especialidade_solicitante"),
        "acompanhamento_fila",
        ["especialidade_solicitante"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_status_higienizacao"),
        "acompanhamento_fila",
        ["status_higienizacao"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_status_operacional"),
        "acompanhamento_fila",
        ["status_operacional"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_prazo_confirmacao_em"),
        "acompanhamento_fila",
        ["prazo_confirmacao_em"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_data_agendada_aghu"),
        "acompanhamento_fila",
        ["data_agendada_aghu"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_created_at"),
        "acompanhamento_fila",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acompanhamento_fila_deleted_at"),
        "acompanhamento_fila",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_acompanhamento_fila_prontuario_exame",
        "acompanhamento_fila",
        ["prontuario", "codigo_exame"],
        unique=False,
    )
    op.create_index(
        "ix_acompanhamento_fila_solicitacao_exame",
        "acompanhamento_fila",
        ["codigo_solicitacao", "codigo_exame"],
        unique=False,
    )
    op.create_index(
        "ix_acompanhamento_fila_status_ativos",
        "acompanhamento_fila",
        ["status_operacional", "status_higienizacao", "deleted_at"],
        unique=False,
    )

    # 5. incompatibilidades_exames (filha de regras_exames)
    op.create_table(
        "incompatibilidades_exames",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo_exame_origem", sa.String(length=50), nullable=False),
        sa.Column("codigo_exame_conflitante", sa.String(length=50), nullable=False),
        sa.Column("tipo_conflito", sa.String(length=50), nullable=False),
        sa.Column("intervalo_minimo_dias", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["codigo_exame_origem"],
            ["regras_exames.codigo_exame"],
            name="fk_incompatibilidades_exames_codigo_exame_origem",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "tipo_conflito IN ('MESMO_DIA', 'PREPARO', 'INTERVALO_MINIMO')",
            name="ck_incompatibilidades_exames_tipo_conflito",
        ),
        sa.CheckConstraint(
            "intervalo_minimo_dias >= 0",
            name="ck_incompatibilidades_exames_intervalo_minimo_dias",
        ),
    )
    op.create_index(
        op.f("ix_incompatibilidades_exames_id"),
        "incompatibilidades_exames",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incompatibilidades_exames_codigo_exame_origem"),
        "incompatibilidades_exames",
        ["codigo_exame_origem"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incompatibilidades_exames_codigo_exame_conflitante"),
        "incompatibilidades_exames",
        ["codigo_exame_conflitante"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incompatibilidades_exames_tipo_conflito"),
        "incompatibilidades_exames",
        ["tipo_conflito"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incompatibilidades_exames_ativo"),
        "incompatibilidades_exames",
        ["ativo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incompatibilidades_exames_deleted_at"),
        "incompatibilidades_exames",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_incompatibilidades_exames_par",
        "incompatibilidades_exames",
        ["codigo_exame_origem", "codigo_exame_conflitante"],
        unique=False,
    )


def downgrade() -> None:
    """Reverte a criação das 5 tabelas em ordem inversa de chaves estrangeiras."""
    # 1. incompatibilidades_exames (filha de regras_exames)
    op.drop_index("ix_incompatibilidades_exames_par", table_name="incompatibilidades_exames")
    op.drop_index(op.f("ix_incompatibilidades_exames_deleted_at"), table_name="incompatibilidades_exames")
    op.drop_index(op.f("ix_incompatibilidades_exames_ativo"), table_name="incompatibilidades_exames")
    op.drop_index(op.f("ix_incompatibilidades_exames_tipo_conflito"), table_name="incompatibilidades_exames")
    op.drop_index(op.f("ix_incompatibilidades_exames_codigo_exame_conflitante"), table_name="incompatibilidades_exames")
    op.drop_index(op.f("ix_incompatibilidades_exames_codigo_exame_origem"), table_name="incompatibilidades_exames")
    op.drop_index(op.f("ix_incompatibilidades_exames_id"), table_name="incompatibilidades_exames")
    op.drop_table("incompatibilidades_exames")

    # 2. acompanhamento_fila (filha de importacoes_forms)
    op.drop_index("ix_acompanhamento_fila_status_ativos", table_name="acompanhamento_fila")
    op.drop_index("ix_acompanhamento_fila_solicitacao_exame", table_name="acompanhamento_fila")
    op.drop_index("ix_acompanhamento_fila_prontuario_exame", table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_deleted_at"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_created_at"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_data_agendada_aghu"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_prazo_confirmacao_em"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_status_operacional"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_status_higienizacao"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_especialidade_solicitante"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_unidade_solicitante"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_data_retorno_medico"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_utiliza_tfd"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_regiao_geografica"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_municipio"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_nome_paciente"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_prontuario"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_codigo_exame"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_codigo_solicitacao"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_importacao_id"), table_name="acompanhamento_fila")
    op.drop_index(op.f("ix_acompanhamento_fila_id"), table_name="acompanhamento_fila")
    op.drop_table("acompanhamento_fila")

    # 3. regras_exames
    op.drop_index(op.f("ix_regras_exames_deleted_at"), table_name="regras_exames")
    op.drop_index(op.f("ix_regras_exames_ativo"), table_name="regras_exames")
    op.drop_index(op.f("ix_regras_exames_unidade_executora"), table_name="regras_exames")
    op.drop_index(op.f("ix_regras_exames_codigo_exame"), table_name="regras_exames")
    op.drop_index(op.f("ix_regras_exames_id"), table_name="regras_exames")
    op.drop_table("regras_exames")

    # 4. regras_prioridade
    op.drop_index(op.f("ix_regras_prioridade_deleted_at"), table_name="regras_prioridade")
    op.drop_index(op.f("ix_regras_prioridade_ativo"), table_name="regras_prioridade")
    op.drop_index(op.f("ix_regras_prioridade_tipo_criterio"), table_name="regras_prioridade")
    op.drop_index(op.f("ix_regras_prioridade_codigo"), table_name="regras_prioridade")
    op.drop_index(op.f("ix_regras_prioridade_id"), table_name="regras_prioridade")
    op.drop_table("regras_prioridade")

    # 5. importacoes_forms
    op.drop_index(op.f("ix_importacoes_forms_deleted_at"), table_name="importacoes_forms")
    op.drop_index(op.f("ix_importacoes_forms_usuario_importador"), table_name="importacoes_forms")
    op.drop_index(op.f("ix_importacoes_forms_importado_em"), table_name="importacoes_forms")
    op.drop_index(op.f("ix_importacoes_forms_id"), table_name="importacoes_forms")
    op.drop_table("importacoes_forms")
