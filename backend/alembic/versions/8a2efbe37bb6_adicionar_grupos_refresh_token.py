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
    """Adiciona a coluna groups (JSON) em refresh_tokens."""
    op.add_column("refresh_tokens", sa.Column("groups", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove a coluna groups."""
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_column("groups")
