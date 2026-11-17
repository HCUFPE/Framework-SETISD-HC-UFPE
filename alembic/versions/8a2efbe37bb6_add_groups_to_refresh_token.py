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
    if not inspector.has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("token", sa.String(), nullable=True),
            sa.Column("groups", sa.JSON(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
        op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
        op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)
        return

    if "groups" not in {column["name"] for column in inspector.get_columns("refresh_tokens")}:
        with op.batch_alter_table("refresh_tokens") as batch_op:
            batch_op.add_column(sa.Column("groups", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("refresh_tokens") and "groups" in {
        column["name"] for column in inspector.get_columns("refresh_tokens")
    }:
        with op.batch_alter_table("refresh_tokens") as batch_op:
            batch_op.drop_column("groups")
