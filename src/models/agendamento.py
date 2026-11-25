"""
Modelos da Gestão de Agendamentos (v0.4.0)
=========================================
Vagas são configuração local (SQLite), com soft delete. Agendamentos, contatos
e endereços de pacientes complementam as entidades da integração Forms → AGHUX.
Nenhum dado de endereço é gravado em claro: CEP/logradouro/número/complemento
são cifrados com AES-GCM pelo helper de criptografia.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text

from ..resources.database import Base


def _agora() -> datetime:
    """Retorna a data/hora atual em UTC (compatível com SQLite e Alembic)."""
    return datetime.now(timezone.utc)


class AgendaSlot(Base):
    """Vaga local de exame, gerenciada pela Área Gestora/ADMIN_TI."""

    __tablename__ = "agenda_slots"

    id = Column(String(36), primary_key=True)
    unidade = Column(String(300), nullable=False)
    codigo_exame = Column(String(100), nullable=False, default="")
    nome_exame = Column(String(300), nullable=False, default="")
    inicio = Column(DateTime(timezone=True), nullable=False)
    fim = Column(DateTime(timezone=True), nullable=False)
    capacidade = Column(Integer, nullable=False)
    situacao = Column(String(20), nullable=False, default="DISPONIVEL")
    criado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    atualizado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


Index(
    "ix_agenda_slots_inicio_unidade_codigo",
    AgendaSlot.inicio,
    AgendaSlot.unidade,
    AgendaSlot.codigo_exame,
)


class Agendamento(Base):
    """Marcação efetivada após aceite do paciente e divergências tratadas."""

    __tablename__ = "agendamentos"

    id = Column(String(36), primary_key=True)
    solicitacao_id = Column(String(36), ForeignKey("solicitacoes.id"), nullable=False, index=True)
    slot_id = Column(String(36), ForeignKey("agenda_slots.id"), nullable=False, index=True)
    paciente_chave = Column(String(64), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ATIVO", index=True)
    autor = Column(String(255), nullable=False, default="")
    justificativa = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    cancelado_em = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


# Índice composto lógico: a unicidade de ATIVOs por slot/paciente é validada
# no controller (índice parcial não é suportado de forma portátil no SQLite).
Index(
    "ix_agendamentos_slot_paciente_status",
    Agendamento.slot_id,
    Agendamento.paciente_chave,
    Agendamento.status,
)


class ContatoPaciente(Base):
    """Registro de aceite, recusa ou sem resposta (RN-07)."""

    __tablename__ = "contatos_paciente"

    id = Column(String(36), primary_key=True)
    solicitacao_id = Column(String(36), ForeignKey("solicitacoes.id"), nullable=False, index=True)
    canal = Column(String(50), nullable=False)
    resultado = Column(String(30), nullable=False, index=True)
    observacao = Column(Text, nullable=True)
    operador = Column(String(255), nullable=False, default="")
    realizado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class PacienteEndereco(Base):
    """Endereço cifrado e última distância calculada até o hospital."""

    __tablename__ = "paciente_enderecos"

    id = Column(String(36), primary_key=True)
    paciente_chave = Column(String(64), nullable=False, index=True)
    cep_cripto = Column(Text, nullable=True)
    logradouro_cripto = Column(Text, nullable=True)
    numero_cripto = Column(Text, nullable=True)
    complemento_cripto = Column(Text, nullable=True)
    bairro_cripto = Column(Text, nullable=True)
    cidade = Column(String(150), nullable=True)
    estado = Column(String(150), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    distancia_km = Column(Float, nullable=True)
    distancia_fonte = Column(String(20), nullable=True, default="INDISPONIVEL")
    calculado_em = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
