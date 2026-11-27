"""
Modelo SQLAlchemy de Histórico de Importações do Google Forms
=============================================================
Registra cada lote de planilha (CSV/XLSX) importado pela Central de Marcação
do HC-UFPE, incluindo totalizadores de higienização e suporte a exclusão lógica
(soft delete via ``deleted_at``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..resources.database import Base

if TYPE_CHECKING:
    from .acompanhamento_fila import AcompanhamentoFila


def _utc_now() -> datetime:
    """Retorna a data e hora atual em UTC."""
    return datetime.now(timezone.utc)


class ImportacaoForms(Base):
    """Representa o registro de uma importação de planilha do Google Forms."""

    __tablename__ = "importacoes_forms"
    __table_args__ = (
        CheckConstraint(
            "total_linhas >= 0",
            name="ck_importacoes_forms_total_linhas_non_negative",
        ),
        CheckConstraint(
            "total_validas >= 0",
            name="ck_importacoes_forms_total_validas_non_negative",
        ),
        CheckConstraint(
            "total_duplicadas >= 0",
            name="ck_importacoes_forms_total_duplicadas_non_negative",
        ),
        CheckConstraint(
            "total_erros >= 0",
            name="ck_importacoes_forms_total_erros_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    nome_arquivo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    importado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utc_now,
        nullable=False,
        index=True,
    )
    usuario_importador: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )
    total_linhas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_validas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_duplicadas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_erros: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        index=True,
    )

    acompanhamentos: Mapped[List["AcompanhamentoFila"]] = relationship(
        "AcompanhamentoFila",
        back_populates="importacao",
        passive_deletes=True,
    )

    @property
    def is_deleted(self) -> bool:
        """Indica se o registro de importação foi excluído logicamente."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca o registro como excluído logicamente sem remoção física."""
        self.deleted_at = _utc_now()

    def __repr__(self) -> str:
        """Retorna representação textual resumida da importação."""
        return (
            f"<ImportacaoForms id={self.id} nome_arquivo={self.nome_arquivo!r} "
            f"usuario_importador={self.usuario_importador!r} "
            f"total_linhas={self.total_linhas}>"
        )
