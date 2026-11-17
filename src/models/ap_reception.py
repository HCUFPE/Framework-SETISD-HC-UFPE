"""Modelos persistentes das operações existentes de Recepção do Sistema AP."""

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..resources.database import Base


class ApSolicitacao(Base):
    """Representação local de solicitação AGHU usada pelo provider configurado."""

    __tablename__ = "ap_solicitacoes"

    codigo_solicitacao: Mapped[str] = mapped_column(String(60), primary_key=True)
    situacao_recepcao: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    data_solicitacao: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    caso_numero: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ihq_codigo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ihq_caso_numero: Mapped[str | None] = mapped_column(String(40), nullable=True)
    devolucao_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApCaso(Base):
    """Agregado de caso AP; relações da Recepção ficam em tabelas próprias."""

    __tablename__ = "ap_casos"
    __table_args__ = (UniqueConstraint("solicitacao_codigo", name="uq_ap_caso_solicitacao"),)

    numero_interno: Mapped[str] = mapped_column(String(40), primary_key=True)
    solicitacao_codigo: Mapped[str] = mapped_column(
        ForeignKey("ap_solicitacoes.codigo_solicitacao"), nullable=False, index=True
    )
    tipo_exame: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    data_entrada: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApConferenciaRecebimento(Base):
    """Conferência física registrada no recebimento ou rejeição."""

    __tablename__ = "ap_conferencias_recebimento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solicitacao_codigo: Mapped[str] = mapped_column(
        ForeignKey("ap_solicitacoes.codigo_solicitacao"), nullable=False, index=True
    )
    caso_numero: Mapped[str | None] = mapped_column(
        ForeignKey("ap_casos.numero_interno"), nullable=True, index=True
    )
    resultado: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    conferido_em: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApItemMaterial(Base):
    """Material gerado no recebimento, sem operações técnicas posteriores."""

    __tablename__ = "ap_itens_material"

    codigo: Mapped[str] = mapped_column(String(80), primary_key=True)
    caso_numero: Mapped[str] = mapped_column(
        ForeignKey("ap_casos.numero_interno"), nullable=False, index=True
    )
    codigo_pai: Mapped[str | None] = mapped_column(
        ForeignKey("ap_itens_material.codigo"), nullable=True
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApExameIhq(Base):
    """Vínculo de IHQ recebido a caso existente, sem execução técnica de IHQ."""

    __tablename__ = "ap_exames_ihq"

    codigo_interno: Mapped[str] = mapped_column(String(40), primary_key=True)
    caso_numero: Mapped[str] = mapped_column(
        ForeignKey("ap_casos.numero_interno"), nullable=False, index=True
    )
    solicitacao_codigo: Mapped[str] = mapped_column(
        ForeignKey("ap_solicitacoes.codigo_solicitacao"), nullable=False, unique=True
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApNaoConformidade(Base):
    """Ocorrência de não conformidade nos contextos já suportados."""

    __tablename__ = "ap_nao_conformidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    caso_numero: Mapped[str | None] = mapped_column(
        ForeignKey("ap_casos.numero_interno"), nullable=True, index=True
    )
    solicitacao_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("ap_solicitacoes.codigo_solicitacao"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApDevolucao(Base):
    """Devolução associada à não conformidade que a originou."""

    __tablename__ = "ap_devolucoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nao_conformidade_id: Mapped[int] = mapped_column(
        ForeignKey("ap_nao_conformidades.id"), nullable=False, index=True
    )
    caso_numero: Mapped[str | None] = mapped_column(
        ForeignKey("ap_casos.numero_interno"), nullable=True, index=True
    )
    solicitacao_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("ap_solicitacoes.codigo_solicitacao"), nullable=True, index=True
    )
    situacao: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    devolvida_em: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ApHistoricoCaso(Base):
    """Evento imutável da linha do tempo da Recepção."""

    __tablename__ = "ap_historico_caso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    caso_numero: Mapped[str] = mapped_column(
        ForeignKey("ap_casos.numero_interno"), nullable=False, index=True
    )
    ocorrido_em: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
