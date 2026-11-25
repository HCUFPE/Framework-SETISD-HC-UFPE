"""
Modelos da Integração Microsoft Forms → AGHUX (Fase 4 / v0.2.0)
===============================================================
A entidade `FormsResponse` é o evento idempotente do webhook. `Solicitacao` e
suas entidades filhas são criadas pelo controller após o cruzamento com o
AGHUX. Nenhuma mutação física é usada: registros editáveis têm `deleted_at`.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text

from ..resources.database import Base


def _agora() -> datetime:
    """Retorna a data/hora atual em UTC (compatível com SQLite e Alembic)."""
    return datetime.now(timezone.utc)


class FormsResponse(Base):
    """Evento recebido do Microsoft Forms via webhook do Power Automate."""

    __tablename__ = "forms_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(String(255), nullable=False, unique=True, index=True)
    form_id = Column(String(255), nullable=False, index=True)
    payload_cripto = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDENTE", index=True)
    tentativas = Column(Integer, nullable=False, default=0)
    ultimo_erro = Column(Text, nullable=True)
    ip_origem = Column(String(64), nullable=True)
    recebido_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    processado_em = Column(DateTime(timezone=True), nullable=True)
    solicitacao_id = Column(String(36), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class WebhookNonce(Base):
    """Nonce consumido pelo webhook; impede repetição (replay attack)."""

    __tablename__ = "webhook_nonces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nonce = Column(String(255), nullable=False, unique=True, index=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    expira_em = Column(DateTime(timezone=True), nullable=False)


class Solicitacao(Base):
    """Solicitação de exame originada do formulário externo."""

    __tablename__ = "solicitacoes"

    id = Column(String(36), primary_key=True)
    protocolo = Column(String(100), nullable=False, index=True)
    forms_response_id = Column(String(255), nullable=True, unique=True, index=True)
    codigo_solicitacao_aghux = Column(String(100), nullable=True, index=True)
    prontuario = Column(String(100), nullable=True, index=True)
    paciente_chave = Column(String(64), nullable=True, index=True)
    paciente_nome = Column(String(300), nullable=False)
    telefone = Column(String(50), nullable=True)
    cidade = Column(String(150), nullable=True)
    estado = Column(String(150), nullable=True)
    cpf_cripto = Column(Text, nullable=True)
    cns_cripto = Column(Text, nullable=True)
    cpf_hash = Column(String(64), nullable=True, index=True)
    cns_hash = Column(String(64), nullable=True, index=True)
    exame = Column(String(300), nullable=False)
    itens_exame = Column(Text, nullable=False, default="[]")
    tipo_exame = Column(String(150), nullable=True)
    setor_solicitante = Column(String(300), nullable=True)
    solicitante_codigo = Column(String(100), nullable=True)
    solicitante_nome = Column(String(300), nullable=True)
    status = Column(String(30), nullable=False, default="RECEBIDA", index=True)
    pontuacao = Column(Integer, nullable=False, default=0)
    prioridade = Column(String(10), nullable=False, default="BAIXA")
    recebida_em = Column(DateTime(timezone=True), nullable=False, default=_agora, index=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    atualizado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class SolicitacaoItemExame(Base):
    """Item de exame de uma solicitação (um exame por linha)."""

    __tablename__ = "solicitacao_itens_exame"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitacao_id = Column(String(36), ForeignKey("solicitacoes.id"), nullable=False, index=True)
    codigo_exame = Column(String(100), nullable=False)
    nome_exame = Column(String(300), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class Divergencia(Base):
    """Diferença entre o valor informado no formulário e o cadastro AGHUX."""

    __tablename__ = "divergencias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitacao_id = Column(String(36), ForeignKey("solicitacoes.id"), nullable=False, index=True)
    campo = Column(String(150), nullable=False)
    valor_formulario = Column(Text, nullable=True)
    valor_aghux = Column(Text, nullable=True)
    tratada = Column(Boolean, nullable=False, default=False)
    justificativa = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class Alerta(Base):
    """Inconsistência detectada no recebimento da resposta do formulário."""

    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitacao_id = Column(String(36), ForeignKey("solicitacoes.id"), nullable=False, index=True)
    campo = Column(String(150), nullable=False)
    mensagem = Column(Text, nullable=False)
    severidade = Column(String(10), nullable=False, default="MEDIA")
    criado_em = Column(DateTime(timezone=True), nullable=False, default=_agora)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


Index("ix_solicitacoes_ativas_prontuario", Solicitacao.prontuario, Solicitacao.deleted_at)
