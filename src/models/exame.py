"""
Modelos do recebimento e da conferência de amostras na Recepção.
================================================================
Dados próprios do sistema, gravados no banco local. Os dados do paciente continuam
no AGHU: aqui fica só o prontuário, e o nome e as informações clínicas nunca são gravados.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    text,
)

from ..resources.database import Base

STATUS_RECEBIDO = "RECEBIDO"
STATUS_DEVOLVIDO = "DEVOLVIDO"

# Cargas iniciais. Depois de criadas, as listas passam a valer pelo banco, sem regra no código.
MOTIVOS_INICIAIS = [
    "Amostra sem solicitação ou sem etiqueta do AGHU",
    "Solicitação do exame não corresponde ao tipo de material enviado",
    "Falta descrição do material no frasco",
    "Etiqueta, identificação do paciente na peça ou requisição ilegível(is)",
    "Numeração dos frascos não corresponde à numeração do AGHU",
    "Quantidade de material não confere com a solicitação do AGHU",
    "Informações do material divergentes no frasco e no AGHU",
    "Falta carimbo e/ou assinatura do médico responsável",
    "Acondicionamento inadequado ou sem fixador",
    "Várias solicitações do mesmo exame em códigos diferentes",
    "Peças não descritas no campo de informações clínicas",
    "Formulário do SISCAN incompleto ou ausente",
    "Sem agendamento no sistema CMCE (SES-PE)",
    "Outra",
]

BANCADAS_INICIAIS: List[Dict[str, Any]] = [
    {"codigo_lab": "207", "bancada": "HP", "prefixo": "HP"},
    {"codigo_lab": "203", "bancada": "CG", "prefixo": "CG"},
    {"codigo_lab": "139", "bancada": "CCV", "prefixo": "CCV"},
    {"codigo_lab": "205", "bancada": "CO", "prefixo": "CO"},
    {"codigo_lab": "209", "bancada": "IHQ", "prefixo": "IH"},
]

STATUS_ITEM_INICIAIS: List[Dict[str, Any]] = [
    {"codigo": "AC", "descricao": "A COLETAR", "permite_recebimento": True},
    {"codigo": "EC", "descricao": "EM COLETA", "permite_recebimento": True},
    {"codigo": "CO", "descricao": "COLETADO", "permite_recebimento": True},
    {"codigo": "AE", "descricao": "AREA EXECUTORA", "permite_recebimento": True},
    {"codigo": "PE", "descricao": "PENDENTE", "permite_recebimento": True},
    {"codigo": "EX", "descricao": "EXECUTANDO", "permite_recebimento": False},
    {"codigo": "LI", "descricao": "LIBERADO", "permite_recebimento": False},
    {"codigo": "CA", "descricao": "CANCELADO", "permite_recebimento": False},
]

PROCEDIMENTOS_HP_INICIAIS = [
    "Peça de mama",
    "Biópsia de mama",
    "Peça de colo uterino",
    "Biópsia de colo uterino",
    "Anatomopatológico geral",
]


def _agora_utc() -> datetime:
    """Retorna a data e a hora atuais em UTC."""
    return datetime.now(timezone.utc)


class BancadaLaboratorio(Base):
    """Bancada e prefixo do nº interno de cada laboratório do AGHU (`codigo_lab`)."""

    __tablename__ = "bancadas_laboratorio"

    codigo_lab = Column(String, primary_key=True)
    bancada = Column(String, nullable=False, unique=True)  # HP, CO, IHQ, CG, CCV
    prefixo = Column(String, nullable=False)  # HP, CO, IH, CG, CCV
    ativo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_agora_utc, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class StatusItemAghu(Base):
    """Status de item do AGHU e se ele permite o recebimento da amostra."""

    __tablename__ = "status_item_aghu"

    codigo = Column(String, primary_key=True)
    descricao = Column(String, nullable=False)  # Nome usado no AGHU (RNF003).
    permite_recebimento = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=_agora_utc, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class ProcedimentoHp(Base):
    """Procedimento informado no recebimento de HP (lista configurável)."""

    __tablename__ = "procedimentos_hp"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String, nullable=False, unique=True)
    ativo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_agora_utc, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class Exame(Base):
    """Exame de uma bancada de uma solicitação do AGHU."""

    __tablename__ = "exames"
    __table_args__ = (
        UniqueConstraint("tipo", "ano", "sequencial", name="uq_exame_tipo_ano_sequencial"),
        CheckConstraint("status IN ('RECEBIDO', 'DEVOLVIDO')", name="ck_exame_status"),
        CheckConstraint(
            "(status = 'RECEBIDO' AND sequencial IS NOT NULL AND numero_interno IS NOT NULL) "
            "OR (status = 'DEVOLVIDO' AND sequencial IS NULL AND numero_interno IS NULL)",
            name="ck_exame_numero_por_status",
        ),
        CheckConstraint(
            "quantidade_pecas IS NULL OR quantidade_pecas >= 1",
            name="ck_exame_quantidade_pecas",
        ),
        # Impede dois recebimentos do mesmo tipo, mesmo com leituras simultâneas.
        Index(
            "uq_exame_solicitacao_tipo_recebido",
            "codigo_solicitacao",
            "tipo",
            unique=True,
            sqlite_where=text("status = 'RECEBIDO' AND deleted_at IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_interno = Column(String, nullable=True, index=True)  # Ex.: "HP 4757"; nulo se devolvido.
    tipo = Column(String, nullable=False)  # HP, CO, IHQ, CG, CCV
    ano = Column(Integer, nullable=False)
    sequencial = Column(Integer, nullable=True)
    codigo_solicitacao = Column(String, nullable=False, index=True)
    prontuario = Column(String, nullable=True, index=True)  # Paciente Externo pode vir sem.
    origem = Column(String, nullable=False)
    especialidade = Column(String, nullable=True)  # Clínica; Paciente Externo vem sem.
    unidade = Column(String, nullable=True)  # Andar ou ambulatório.
    status = Column(String, nullable=False)
    quantidade_pecas = Column(Integer, nullable=True)  # Obrigatório ao receber HP.
    urgente = Column(Boolean, nullable=True)  # HP informado na recepção; CO sempre urgente.
    procedimento_id = Column(Integer, ForeignKey("procedimentos_hp.id"), nullable=True)
    referencia_hp = Column(String, nullable=True)  # IHQ: HP de origem, ex.: "HP-2025/24".
    recebido_por = Column(String, nullable=False)
    recebido_em = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_agora_utc, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class Amostra(Base):
    """Amostra de um exame, com os dados copiados do AGHU no momento do registro."""

    __tablename__ = "amostras"
    __table_args__ = (
        UniqueConstraint("exame_id", "numero_amostra", name="uq_amostra_exame_numero"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=False, index=True)
    numero_amostra = Column(Integer, nullable=False)  # Pode ter lacunas na solicitação.
    bancada = Column(String, nullable=False)
    sigla_exame = Column(String, nullable=False)  # Sigla do AGHU, ex.: APECR.
    nome_exame = Column(String, nullable=False)
    descricao_material = Column(Text, nullable=True)  # Vazia no AGHU em algumas siglas.
    descricao_informada = Column(Text, nullable=True)  # Preenchida se o AGHU vier sem descrição.
    cod_status_item = Column(String, nullable=False)  # Status no AGHU no momento do registro.
    recebida = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_agora_utc, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class ConferenciaAmostra(Base):
    """Checklist obrigatório de uma amostra recebida (RF004)."""

    __tablename__ = "conferencias_amostra"
    __table_args__ = (UniqueConstraint("amostra_id", name="uq_conferencia_amostra"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    amostra_id = Column(Integer, ForeignKey("amostras.id"), nullable=False)
    sigla_confere = Column(Boolean, nullable=False)
    descricao_confere = Column(Boolean, nullable=False)
    recipientes_confere = Column(Boolean, nullable=False)
    conferido_por = Column(String, nullable=False)
    conferido_em = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class MotivoNaoConformidade(Base):
    """Motivo padronizado de não conformidade (lista configurável)."""

    __tablename__ = "motivos_nao_conformidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String, nullable=False, unique=True)
    ativo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_agora_utc, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class NaoConformidade(Base):
    """Não conformidade registrada na devolução de um exame à origem (RF005)."""

    __tablename__ = "nao_conformidades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=False, index=True)
    motivo_id = Column(Integer, ForeignKey("motivos_nao_conformidade.id"), nullable=False)
    observacao = Column(Text, nullable=False)
    numero_cmce = Column(String, nullable=True)  # Não vem do AGHU.
    medico_solicitante = Column(String, nullable=True)  # Não vem do AGHU; pode estar ilegível.
    resolvida = Column(Boolean, nullable=False, default=False)  # "Resolveu?" da planilha.
    resolvida_por = Column(String, nullable=True)
    resolvida_em = Column(DateTime, nullable=True)
    registrado_por = Column(String, nullable=False)
    registrado_em = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class SequenciaNumeroInterno(Base):
    """Último nº interno usado, por tipo e por ano (RF006)."""

    __tablename__ = "sequencias_numero_interno"

    tipo = Column(String, primary_key=True)
    ano = Column(Integer, primary_key=True)
    ultimo_numero = Column(Integer, nullable=False)


# As tabelas nascem do create_all no startup, então a carga inicial acompanha a criação.
@event.listens_for(MotivoNaoConformidade.__table__, "after_create")
def _carregar_motivos_iniciais(target: Any, connection: Any, **_: Any) -> None:
    """Grava os motivos iniciais quando a tabela é criada."""
    connection.execute(
        target.insert(),
        [{"descricao": descricao, "ativo": True} for descricao in MOTIVOS_INICIAIS],
    )


@event.listens_for(BancadaLaboratorio.__table__, "after_create")
def _carregar_bancadas_iniciais(target: Any, connection: Any, **_: Any) -> None:
    """Grava o mapeamento inicial de laboratório para bancada quando a tabela é criada."""
    connection.execute(target.insert(), [{**dados, "ativo": True} for dados in BANCADAS_INICIAIS])


@event.listens_for(StatusItemAghu.__table__, "after_create")
def _carregar_status_iniciais(target: Any, connection: Any, **_: Any) -> None:
    """Grava os status de item do AGHU quando a tabela é criada."""
    connection.execute(target.insert(), STATUS_ITEM_INICIAIS)


@event.listens_for(ProcedimentoHp.__table__, "after_create")
def _carregar_procedimentos_iniciais(target: Any, connection: Any, **_: Any) -> None:
    """Grava os procedimentos de HP quando a tabela é criada."""
    connection.execute(
        target.insert(),
        [{"descricao": descricao, "ativo": True} for descricao in PROCEDIMENTOS_HP_INICIAIS],
    )
