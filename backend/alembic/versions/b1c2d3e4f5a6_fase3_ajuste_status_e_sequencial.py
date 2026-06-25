"""fase3: align frontend — tipo_exame, sequencial, ano, semestre em exames; status padronizados

Revision ID: b1c2d3e4f5a6
Revises: a466fca0bf59
Create Date: 2026-06-23

Alinha o modelo Exame ao frontend:
- Adiciona tipo_exame, sequencial, ano, semestre (derivam numero_solicitacao)
- O campo status não precisa de migração de dados em dev (banco é resetado),
  mas em produção os valores antigos precisariam ser mapeados manualmente.
"""

from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f5a6'
down_revision = 'a466fca0bf59'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('exames') as batch_op:
        batch_op.add_column(sa.Column('tipo_exame', sa.String(), nullable=True, server_default='HP'))
        batch_op.add_column(sa.Column('sequencial', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ano', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('semestre', sa.Integer(), nullable=True))

    # Popula tipo_exame para registros existentes
    op.execute("UPDATE exames SET tipo_exame = 'HP' WHERE tipo_exame IS NULL")

    # Converte status antigos para os novos valores (alinhamento com frontend)
    op.execute("UPDATE exames SET status = 'Na Recepção' WHERE status IN ('Na Triagem', 'Aguardando Macroscopia')")
    op.execute("UPDATE exames SET status = 'Em Processamento' WHERE status = 'Aguardando Processamento'")
    op.execute("UPDATE exames SET status = 'Em Microscopia' WHERE status = 'Aguardando Microscopia'")

    # Converte status antigos nos frascos
    op.execute("UPDATE frascos SET status = 'Na Recepção' WHERE status = 'Na Triagem'")


def downgrade() -> None:
    with op.batch_alter_table('exames') as batch_op:
        batch_op.drop_column('semestre')
        batch_op.drop_column('ano')
        batch_op.drop_column('sequencial')
        batch_op.drop_column('tipo_exame')

    # Reverter status (aproximação — perde a distinção entre Na Triagem e Aguardando Macroscopia)
    op.execute("UPDATE exames SET status = 'Na Triagem' WHERE status = 'Na Recepção'")
    op.execute("UPDATE exames SET status = 'Aguardando Processamento' WHERE status = 'Em Processamento'")
    op.execute("UPDATE exames SET status = 'Aguardando Microscopia' WHERE status = 'Em Microscopia'")
    op.execute("UPDATE frascos SET status = 'Na Triagem' WHERE status = 'Na Recepção'")
