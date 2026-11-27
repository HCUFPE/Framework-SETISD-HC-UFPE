"""
Modelo SQLAlchemy de Regras por Exame (`regras_exames`).
========================================================
Armazena parâmetros configuráveis de preparo, antecedência mínima, janela de
retorno e alertas clínicos por sigla oficial do exame no AGHU, com suporte a
exclusão lógica (`deleted_at`).
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..resources.database import Base

if TYPE_CHECKING:
    from .incompatibilidade_exame import IncompatibilidadeExame


def _utc_now() -> datetime:
    """Retorna o timestamp atual em UTC."""
    return datetime.now(timezone.utc)


class RegraExame(Base):
    """
    Representa o cadastro configurável de regras operacionais e clínicas de um
    exame diagnóstico (ex.: preparo, janela de retorno, jejum e idade de alerta).
    """

    __tablename__ = "regras_exames"
    __table_args__ = (
        CheckConstraint(
            "antecedencia_minima_dias >= 0",
            name="ck_regras_exames_antecedencia_minima_dias",
        ),
        CheckConstraint(
            "janela_retorno_max_horas IS NULL OR janela_retorno_max_horas >= 0",
            name="ck_regras_exames_janela_retorno_max_horas",
        ),
        CheckConstraint(
            "idade_minima_alerta IS NULL OR idade_minima_alerta >= 0",
            name="ck_regras_exames_idade_minima_alerta",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    codigo_exame: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    nome_exame: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_executora: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    antecedencia_minima_dias: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    janela_retorno_max_horas: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    exige_jejum: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    priorizar_manha_diabetico: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    idade_minima_alerta: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    orientacoes_preparo: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, onupdate=_utc_now, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True
    )

    incompatibilidades: Mapped[list["IncompatibilidadeExame"]] = relationship(
        "IncompatibilidadeExame",
        back_populates="regra_exame_origem",
        foreign_keys="IncompatibilidadeExame.codigo_exame_origem",
    )

    @property
    def is_deleted(self) -> bool:
        """Indica se o registro foi excluído logicamente (`deleted_at` preenchido)."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca o registro como excluído logicamente sem remoção física."""
        self.deleted_at = _utc_now()

    def __repr__(self) -> str:
        """Retorna representação textual resumida da regra de exame."""
        return (
            f"<RegraExame id={self.id} codigo_exame={self.codigo_exame!r} "
            f"nome_exame={self.nome_exame!r} ativo={self.ativo}>"
        )
