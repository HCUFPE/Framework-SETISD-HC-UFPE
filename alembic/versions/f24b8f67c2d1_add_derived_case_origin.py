"""Add optional source-case relation for derived cases."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f24b8f67c2d1"
down_revision: Union[str, Sequence[str], None] = "e24bc68129ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona origem de derivação sem alterar os casos existentes."""
    with op.batch_alter_table("ap_casos") as batch_op:
        batch_op.add_column(sa.Column("caso_origem_numero", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("tipo_derivacao", sa.String(length=20), nullable=True))
        batch_op.create_foreign_key(
            "fk_ap_casos_caso_origem_numero",
            "ap_casos",
            ["caso_origem_numero"],
            ["numero_interno"],
        )
        batch_op.create_index("ix_ap_casos_caso_origem_numero", ["caso_origem_numero"])


def downgrade() -> None:
    """Remove a relação aditiva criada para casos derivados."""
    with op.batch_alter_table("ap_casos") as batch_op:
        batch_op.drop_index("ix_ap_casos_caso_origem_numero")
        batch_op.drop_constraint("fk_ap_casos_caso_origem_numero", type_="foreignkey")
        batch_op.drop_column("tipo_derivacao")
        batch_op.drop_column("caso_origem_numero")
