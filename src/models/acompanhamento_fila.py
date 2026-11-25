"""
Modelo SQLAlchemy de Acompanhamento da Fila de Exames
=====================================================
Armazena o estado operacional de cada solicitação higienizada (cruzamento
Forms x AGHU), dados complementares do paciente (município, região geográfica,
TFD, data de retorno, telefone), flags clínicas, controle do prazo de 24h para
confirmação e exclusão lógica (soft delete via ``deleted_at``).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional, Tuple

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..resources.database import Base

if TYPE_CHECKING:
    from .importacao_forms import ImportacaoForms


REGIOES_GEOGRAFICAS_VALIDAS: Tuple[str, ...] = (
    "CAPITAL",
    "RMR",
    "INTERIOR",
    "NAO_INFORMADO",
)

STATUS_HIGIENIZACAO_VALIDOS: Tuple[str, ...] = (
    "VALIDA",
    "DUPLICADA",
    "DIVERGENCIA_EXAME",
    "NAO_ENCONTRADA",
    "JA_REALIZADA",
)

STATUS_OPERACIONAL_VALIDOS: Tuple[str, ...] = (
    "NA_FILA",
    "AGUARDANDO_CONFIRMACAO_24H",
    "CONFIRMADO_AGENDADO_AGHU",
    "SEM_RESPOSTA_24H",
    "CANCELADO",
)


def _utc_now() -> datetime:
    """Retorna a data e hora atual em UTC."""
    return datetime.now(timezone.utc)


class AcompanhamentoFila(Base):
    """Representa um item de solicitação de exame acompanhado na fila da Central."""

    __tablename__ = "acompanhamento_fila"
    __table_args__ = (
        CheckConstraint(
            "regiao_geografica IN ('CAPITAL', 'RMR', 'INTERIOR', 'NAO_INFORMADO')",
            name="ck_acompanhamento_fila_regiao_geografica",
        ),
        CheckConstraint(
            "status_higienizacao IN "
            "('VALIDA', 'DUPLICADA', 'DIVERGENCIA_EXAME', 'NAO_ENCONTRADA', 'JA_REALIZADA')",
            name="ck_acompanhamento_fila_status_higienizacao",
        ),
        CheckConstraint(
            "status_operacional IN "
            "('NA_FILA', 'AGUARDANDO_CONFIRMACAO_24H', 'CONFIRMADO_AGENDADO_AGHU', "
            "'SEM_RESPOSTA_24H', 'CANCELADO')",
            name="ck_acompanhamento_fila_status_operacional",
        ),
        Index(
            "ix_acompanhamento_fila_prontuario_exame",
            "prontuario",
            "codigo_exame",
        ),
        Index(
            "ix_acompanhamento_fila_solicitacao_exame",
            "codigo_solicitacao",
            "codigo_exame",
        ),
        Index(
            "ix_acompanhamento_fila_status_ativos",
            "status_operacional",
            "status_higienizacao",
            "deleted_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    importacao_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("importacoes_forms.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    codigo_solicitacao: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    codigo_exame: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    prontuario: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    nome_paciente: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    telefone_contato: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    municipio: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    regiao_geografica: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="NAO_INFORMADO",
        server_default="NAO_INFORMADO",
        index=True,
    )
    utiliza_tfd: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
        index=True,
    )
    data_retorno_medico: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    exame_informado_forms: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    unidade_solicitante: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    especialidade_solicitante: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    flag_hemodialise: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    flag_diabetico_jejum: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    grupo_prioritario_manual: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True,
    )
    status_higienizacao: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="VALIDA",
        server_default="VALIDA",
        index=True,
    )
    status_operacional: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="NA_FILA",
        server_default="NA_FILA",
        index=True,
    )
    contato_iniciado_em: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    prazo_confirmacao_em: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    data_agendada_aghu: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    preparo_orientado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    observacoes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utc_now,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        index=True,
    )

    importacao: Mapped[Optional["ImportacaoForms"]] = relationship(
        "ImportacaoForms",
        back_populates="acompanhamentos",
    )

    @property
    def is_deleted(self) -> bool:
        """Indica se o item da fila foi excluído logicamente."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Marca o item como excluído logicamente sem remoção física."""
        self.deleted_at = _utc_now()

    def __repr__(self) -> str:
        """Retorna representação textual resumida do item da fila."""
        return (
            f"<AcompanhamentoFila id={self.id} "
            f"codigo_solicitacao={self.codigo_solicitacao!r} "
            f"codigo_exame={self.codigo_exame!r} "
            f"status_higienizacao={self.status_higienizacao!r} "
            f"status_operacional={self.status_operacional!r}>"
        )
