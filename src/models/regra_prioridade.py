"""
Modelo SQLAlchemy de Regras de Prioridade Clínica (`regras_prioridade`).
========================================================================
Armazena critérios e pesos configuráveis utilizados pelo motor determinístico
de priorização da fila de exames do HC-UFPE, com suporte a exclusão lógica
(`deleted_at`).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..resources.database import Base

TIPOS_CRITERIO_VALIDOS: tuple[str, ...] = (
    "CLINICA",
    "GRUPO_CLINICO",
    "VULNERAVEL",
    "AFINIDADE_EXAME",
    "RETORNO_PROXIMO",
)


def _utc_now() -> datetime:
    """Retorna o timestamp atual em UTC."""
    return datetime.now(timezone.utc)


class RegraPrioridade(Base):
    """
    Representa uma regra configurável de peso para cálculo do score de
    prioridade clínica na fila de marcação de exames.
    """

    __tablename__ = "regras_prioridade"
    __table_args__ = (
        CheckConstraint(
            "tipo_criterio IN ('CLINICA', 'GRUPO_CLINICO', 'VULNERAVEL', "
            "'AFINIDADE_EXAME', 'RETORNO_PROXIMO')",
            name="ck_regras_prioridade_tipo_criterio",
        ),
        CheckConstraint(
            "peso >= 0 AND peso <= 1000",
            name="ck_regras_prioridade_peso_range",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    codigo: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_criterio: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    valor_match: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=""
    )
    peso: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, onupdate=_utc_now, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True
    )

    @property
    def is_deleted(self) -> bool:
        """Indica se o registro foi excluído logicamente (`deleted_at` preenchido)."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca o registro como excluído logicamente sem remoção física."""
        self.deleted_at = _utc_now()

    def __repr__(self) -> str:
        """Retorna representação textual resumida da regra de prioridade."""
        return (
            f"<RegraPrioridade id={self.id} codigo={self.codigo!r} "
            f"tipo_criterio={self.tipo_criterio!r} peso={self.peso} ativo={self.ativo}>"
        )
