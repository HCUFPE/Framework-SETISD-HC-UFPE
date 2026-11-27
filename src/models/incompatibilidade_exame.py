"""
Modelo SQLAlchemy de Matriz de Incompatibilidades entre Exames
(`incompatibilidades_exames`).
==============================================================
Armazena pares de exames que não podem ser agendados no mesmo dia, possuem
conflito de preparo ou exigem intervalo mínimo em dias, com suporte a exclusão
lógica (`deleted_at`).
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..resources.database import Base

if TYPE_CHECKING:
    from .regra_exame import RegraExame

TIPOS_CONFLITO_VALIDOS: tuple[str, ...] = (
    "MESMO_DIA",
    "PREPARO",
    "INTERVALO_MINIMO",
)


def _utc_now() -> datetime:
    """Retorna o timestamp atual em UTC."""
    return datetime.now(timezone.utc)


class IncompatibilidadeExame(Base):
    """
    Representa uma restrição de incompatibilidade entre um exame de origem
    cadastrado em `regras_exames` e um exame conflitante.
    """

    __tablename__ = "incompatibilidades_exames"
    __table_args__ = (
        CheckConstraint(
            "tipo_conflito IN ('MESMO_DIA', 'PREPARO', 'INTERVALO_MINIMO')",
            name="ck_incompatibilidades_exames_tipo_conflito",
        ),
        CheckConstraint(
            "intervalo_minimo_dias >= 0",
            name="ck_incompatibilidades_exames_intervalo_minimo_dias",
        ),
        Index(
            "ix_incompatibilidades_exames_par",
            "codigo_exame_origem",
            "codigo_exame_conflitante",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    codigo_exame_origem: Mapped[str] = mapped_column(
        String(50),
        ForeignKey(
            "regras_exames.codigo_exame",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    codigo_exame_conflitante: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    tipo_conflito: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    intervalo_minimo_dias: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True
    )

    regra_exame_origem: Mapped["RegraExame"] = relationship(
        "RegraExame",
        back_populates="incompatibilidades",
        foreign_keys=[codigo_exame_origem],
    )

    @property
    def is_deleted(self) -> bool:
        """Indica se o registro foi excluído logicamente (`deleted_at` preenchido)."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca o registro como excluído logicamente sem remoção física."""
        self.deleted_at = _utc_now()

    def __repr__(self) -> str:
        """Retorna representação textual resumida da incompatibilidade."""
        return (
            f"<IncompatibilidadeExame id={self.id} "
            f"origem={self.codigo_exame_origem!r} "
            f"conflitante={self.codigo_exame_conflitante!r} "
            f"tipo_conflito={self.tipo_conflito!r} ativo={self.ativo}>"
        )
