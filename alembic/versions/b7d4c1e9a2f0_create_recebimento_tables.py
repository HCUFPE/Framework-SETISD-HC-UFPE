"""Create recebimento tables

Revision ID: b7d4c1e9a2f0
Revises: 8a2efbe37bb6
Create Date: 2026-11-05 12:00:00.000000

Migração escrita à mão: alembic/env.py não importa os modelos, então o autogenerate
não os enxerga e geraria a remoção das tabelas.
"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d4c1e9a2f0'
down_revision: Union[str, Sequence[str], None] = '8a2efbe37bb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MOTIVOS_INICIAIS = [
    "Amostra sem solicitação ou sem etiqueta do AGHU",
    "Solicitação do exame não corresponde ao tipo de material enviado",
    "Falta descrição do material no frasco",
    "Etiqueta, identificação do paciente na peça ou requisição ilegível(is)",
    "Numeração dos frascos não corresponde à numeração do AGHU",
    "Quantidade de material não confere com a solicitação do AGHU",
    "Informações do material divergentes no frasco e no AGHU",
    "Falta carimbo e/ou assinatura do médico responsável",
    "Acondicionamento inadequado ou sem fixador",
    "Várias solicitações do mesmo exame em códigos diferentes",
    "Peças não descritas no campo de informações clínicas",
    "Formulário do SISCAN incompleto ou ausente",
    "Sem agendamento no sistema CMCE (SES-PE)",
    "Outra",
]

BANCADAS_INICIAIS = [
    {"codigo_lab": "207", "bancada": "HP", "prefixo": "HP"},
    {"codigo_lab": "203", "bancada": "CG", "prefixo": "CG"},
    {"codigo_lab": "139", "bancada": "CCV", "prefixo": "CCV"},
    {"codigo_lab": "205", "bancada": "CO", "prefixo": "CO"},
    {"codigo_lab": "209", "bancada": "IHQ", "prefixo": "IH"},
]

STATUS_ITEM_INICIAIS = [
    {"codigo": "AC", "descricao": "A COLETAR", "permite_recebimento": True},
    {"codigo": "EC", "descricao": "EM COLETA", "permite_recebimento": True},
    {"codigo": "CO", "descricao": "COLETADO", "permite_recebimento": True},
    {"codigo": "AE", "descricao": "AREA EXECUTORA", "permite_recebimento": True},
    {"codigo": "PE", "descricao": "PENDENTE", "permite_recebimento": True},
    {"codigo": "EX", "descricao": "EXECUTANDO", "permite_recebimento": False},
    {"codigo": "LI", "descricao": "LIBERADO", "permite_recebimento": False},
    {"codigo": "CA", "descricao": "CANCELADO", "permite_recebimento": False},
]

PROCEDIMENTOS_HP_INICIAIS = [
    "Peça de mama",
    "Biópsia de mama",
    "Peça de colo uterino",
    "Biópsia de colo uterino",
    "Anatomopatológico geral",
]


def upgrade() -> None:
    """Cria as tabelas do recebimento e carrega as listas iniciais."""
    bancadas = op.create_table(
        'bancadas_laboratorio',
        sa.Column('codigo_lab', sa.String(), primary_key=True),
        sa.Column('bancada', sa.String(), nullable=False, unique=True),
        sa.Column('prefixo', sa.String(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    status_item = op.create_table(
        'status_item_aghu',
        sa.Column('codigo', sa.String(), primary_key=True),
        sa.Column('descricao', sa.String(), nullable=False),
        sa.Column('permite_recebimento', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    procedimentos = op.create_table(
        'procedimentos_hp',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('descricao', sa.String(), nullable=False, unique=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'exames',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('numero_interno', sa.String(), nullable=True),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=False),
        sa.Column('sequencial', sa.Integer(), nullable=True),
        sa.Column('codigo_solicitacao', sa.String(), nullable=False),
        sa.Column('prontuario', sa.String(), nullable=True),
        sa.Column('origem', sa.String(), nullable=False),
        sa.Column('especialidade', sa.String(), nullable=True),
        sa.Column('unidade', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('quantidade_pecas', sa.Integer(), nullable=True),
        sa.Column('urgente', sa.Boolean(), nullable=True),
        sa.Column('procedimento_id', sa.Integer(), sa.ForeignKey('procedimentos_hp.id'), nullable=True),
        sa.Column('referencia_hp', sa.String(), nullable=True),
        sa.Column('recebido_por', sa.String(), nullable=False),
        sa.Column('recebido_em', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('tipo', 'ano', 'sequencial', name='uq_exame_tipo_ano_sequencial'),
        sa.CheckConstraint("status IN ('RECEBIDO', 'DEVOLVIDO')", name='ck_exame_status'),
        sa.CheckConstraint(
            "(status = 'RECEBIDO' AND sequencial IS NOT NULL AND numero_interno IS NOT NULL) "
            "OR (status = 'DEVOLVIDO' AND sequencial IS NULL AND numero_interno IS NULL)",
            name='ck_exame_numero_por_status',
        ),
        sa.CheckConstraint(
            "quantidade_pecas IS NULL OR quantidade_pecas >= 1",
            name='ck_exame_quantidade_pecas',
        ),
    )
    op.create_index('ix_exames_numero_interno', 'exames', ['numero_interno'])
    op.create_index('ix_exames_codigo_solicitacao', 'exames', ['codigo_solicitacao'])
    op.create_index('ix_exames_prontuario', 'exames', ['prontuario'])
    op.create_index(
        'uq_exame_solicitacao_tipo_recebido',
        'exames',
        ['codigo_solicitacao', 'tipo'],
        unique=True,
        sqlite_where=sa.text("status = 'RECEBIDO' AND deleted_at IS NULL"),
    )

    op.create_table(
        'amostras',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('exame_id', sa.Integer(), sa.ForeignKey('exames.id'), nullable=False),
        sa.Column('numero_amostra', sa.Integer(), nullable=False),
        sa.Column('bancada', sa.String(), nullable=False),
        sa.Column('sigla_exame', sa.String(), nullable=False),
        sa.Column('nome_exame', sa.String(), nullable=False),
        sa.Column('descricao_material', sa.Text(), nullable=True),
        sa.Column('descricao_informada', sa.Text(), nullable=True),
        sa.Column('cod_status_item', sa.String(), nullable=False),
        sa.Column('recebida', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('exame_id', 'numero_amostra', name='uq_amostra_exame_numero'),
    )
    op.create_index('ix_amostras_exame_id', 'amostras', ['exame_id'])

    op.create_table(
        'conferencias_amostra',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('amostra_id', sa.Integer(), sa.ForeignKey('amostras.id'), nullable=False),
        sa.Column('sigla_confere', sa.Boolean(), nullable=False),
        sa.Column('descricao_confere', sa.Boolean(), nullable=False),
        sa.Column('recipientes_confere', sa.Boolean(), nullable=False),
        sa.Column('conferido_por', sa.String(), nullable=False),
        sa.Column('conferido_em', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('amostra_id', name='uq_conferencia_amostra'),
    )

    motivos = op.create_table(
        'motivos_nao_conformidade',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('descricao', sa.String(), nullable=False, unique=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'nao_conformidades',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('exame_id', sa.Integer(), sa.ForeignKey('exames.id'), nullable=False),
        sa.Column(
            'motivo_id', sa.Integer(), sa.ForeignKey('motivos_nao_conformidade.id'), nullable=False
        ),
        sa.Column('observacao', sa.Text(), nullable=False),
        sa.Column('numero_cmce', sa.String(), nullable=True),
        sa.Column('medico_solicitante', sa.String(), nullable=True),
        sa.Column('resolvida', sa.Boolean(), nullable=False),
        sa.Column('resolvida_por', sa.String(), nullable=True),
        sa.Column('resolvida_em', sa.DateTime(), nullable=True),
        sa.Column('registrado_por', sa.String(), nullable=False),
        sa.Column('registrado_em', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_nao_conformidades_exame_id', 'nao_conformidades', ['exame_id'])

    op.create_table(
        'sequencias_numero_interno',
        sa.Column('tipo', sa.String(), primary_key=True),
        sa.Column('ano', sa.Integer(), primary_key=True),
        sa.Column('ultimo_numero', sa.Integer(), nullable=False),
    )

    agora = datetime.now(timezone.utc)
    op.bulk_insert(
        motivos,
        [{"descricao": descricao, "ativo": True, "created_at": agora} for descricao in MOTIVOS_INICIAIS],
    )
    op.bulk_insert(
        bancadas,
        [{**dados, "ativo": True, "created_at": agora} for dados in BANCADAS_INICIAIS],
    )
    op.bulk_insert(
        status_item,
        [{**dados, "created_at": agora} for dados in STATUS_ITEM_INICIAIS],
    )
    op.bulk_insert(
        procedimentos,
        [
            {"descricao": descricao, "ativo": True, "created_at": agora}
            for descricao in PROCEDIMENTOS_HP_INICIAIS
        ],
    )


def downgrade() -> None:
    """Remove as tabelas do recebimento."""
    op.drop_table('sequencias_numero_interno')
    op.drop_index('ix_nao_conformidades_exame_id', table_name='nao_conformidades')
    op.drop_table('nao_conformidades')
    op.drop_table('motivos_nao_conformidade')
    op.drop_table('conferencias_amostra')
    op.drop_index('ix_amostras_exame_id', table_name='amostras')
    op.drop_table('amostras')
    op.drop_index('uq_exame_solicitacao_tipo_recebido', table_name='exames')
    op.drop_index('ix_exames_prontuario', table_name='exames')
    op.drop_index('ix_exames_codigo_solicitacao', table_name='exames')
    op.drop_index('ix_exames_numero_interno', table_name='exames')
    op.drop_table('exames')
    op.drop_table('procedimentos_hp')
    op.drop_table('status_item_aghu')
    op.drop_table('bancadas_laboratorio')
