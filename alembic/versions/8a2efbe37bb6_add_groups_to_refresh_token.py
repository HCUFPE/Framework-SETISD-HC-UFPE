"""add groups to refresh token

Revision ID: 8a2efbe37bb6
Revises: df72b10ec0f3
Create Date: 2025-11-05 18:13:21.216513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a2efbe37bb6'
down_revision: Union[str, Sequence[str], None] = 'df72b10ec0f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('refresh_tokens'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('refresh_tokens')}
        for index_name in (
            op.f('ix_refresh_tokens_id'),
            op.f('ix_refresh_tokens_token'),
            op.f('ix_refresh_tokens_user_id'),
        ):
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name='refresh_tokens')
        op.drop_table('refresh_tokens')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('refresh_tokens'):
        op.create_table(
            'refresh_tokens',
            sa.Column('id', sa.INTEGER(), nullable=False),
            sa.Column('user_id', sa.VARCHAR(), nullable=True),
            sa.Column('token', sa.VARCHAR(), nullable=True),
            sa.Column('expires_at', sa.DATETIME(), nullable=False),
            sa.Column(
                'created_at',
                sa.DATETIME(),
                server_default=sa.text('(CURRENT_TIMESTAMP)'),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
        op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=1)
        op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
