"""
Contratos Pydantic da Fila de Exames (``/api/exames``)
=====================================================
Serializa em camelCase os contratos ``IItemFila`` e ``IAlertaExame`` de
``docs/especificacao/05-interfaces.md``. Os requests aceitam tanto camelCase
quanto snake_case.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

RegiaoGeografica = Literal["CAPITAL", "RMR", "INTERIOR", "NAO_INFORMADO"]
StatusHigienizacao = Literal["VALIDA", "DUPLICADA", "DIVERGENCIA_EXAME", "NAO_ENCONTRADA", "JA_REALIZADA"]
StatusOperacional = Literal[
    "NA_FILA",
    "AGUARDANDO_CONFIRMACAO_24H",
    "CONFIRMADO_AGENDADO_AGHU",
    "SEM_RESPOSTA_24H",
    "CANCELADO",
]
TipoAlerta = Literal[
    "INCOMPATIBILIDADE",
    "JANELA_RETORNO",
    "ANTECEDENCIA_PREPARO",
    "JEJUM_CLINICO",
    "IDADE_MAMOGRAFIA",
    "PRAZO_24H_VENCIDO",
    "DUPLICIDADE",
]


class _CamelModel(BaseModel):
    """Base com aliases camelCase e população também pelo nome do campo."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AlertaExame(_CamelModel):
    """Alerta de conflito, preparo, retorno, prazo ou duplicidade (``IAlertaExame``)."""

    tipo: TipoAlerta
    severidade: Literal["ALTA", "MEDIA", "INFO"]
    mensagem: str


class ItemFila(_CamelModel):
    """Item da fila priorizada (``IItemFila``)."""

    id: int
    codigo_solicitacao: str
    codigo_exame: Optional[str] = None
    nome_exame: Optional[str] = None
    prontuario: Optional[str] = None
    nome_paciente: str
    telefone_contato: Optional[str] = None
    municipio: Optional[str] = None
    regiao_geografica: RegiaoGeografica
    utiliza_tfd: bool
    unidade_solicitante: Optional[str] = None
    data_solicitacao: Optional[datetime] = None
    data_retorno_medico: Optional[date] = None
    status_higienizacao: StatusHigienizacao
    status_operacional: StatusOperacional
    score_prioridade: int
    motivos_prioridade: list[str]
    alertas: list[AlertaExame]
    contato_iniciado_em: Optional[datetime] = None
    prazo_confirmacao_em: Optional[datetime] = None
    data_agendada_aghu: Optional[datetime] = None
    preparo_orientado: bool


class OutroExame(_CamelModel):
    """Outro exame do mesmo prontuário (fila local ou AGHU)."""

    codigo_solicitacao: Optional[str] = None
    codigo_exame: Optional[str] = None
    nome_exame: Optional[str] = None
    origem: Literal["FILA", "AGHU"]
    data_agendada: Optional[datetime] = None
    status_operacional: Optional[StatusOperacional] = None


class ItemFilaDetalhe(ItemFila):
    """Detalhe do item com exames relacionados e orientações de preparo."""

    outros_exames: list[OutroExame]
    orientacoes_preparo: Optional[str] = None


class AtualizarStatusRequest(_CamelModel):
    """Corpo de ``PATCH /api/exames/fila/{id}/status``."""

    status_operacional: StatusOperacional
    data_agendada_aghu: Optional[datetime] = None
    preparo_orientado: Optional[bool] = None
    observacoes: Optional[str] = Field(default=None, max_length=2000)


class VincularSolicitacaoRequest(_CamelModel):
    """Corpo de ``PATCH /api/exames/fila/{id}/vincular-solicitacao``."""

    codigo_solicitacao: str = Field(min_length=1, max_length=64)
    codigo_exame: str = Field(min_length=1, max_length=64)
