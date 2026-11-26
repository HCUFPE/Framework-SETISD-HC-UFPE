"""Schemas HTTP compatíveis com os tipos camelCase do frontend AP."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


def _camel_case(nome: str) -> str:
    """Converte nomes Python snake_case para aliases TypeScript camelCase."""
    primeiro, *restante = nome.split("_")
    return primeiro + "".join(parte.capitalize() for parte in restante)


class PayloadRecepcao(BaseModel):
    """Configuração comum de aliases e compatibilidade com nomes Python."""

    model_config = ConfigDict(alias_generator=_camel_case, populate_by_name=True, extra="ignore")


class ConfirmarEntradaInput(PayloadRecepcao):
    solicitacao_id: str = Field(min_length=1)
    tipo_exame: Literal["HP", "CG", "CCV", "CO"]
    urgente: bool
    procedimento: str = Field(min_length=1)
    observacoes: str | None = None


class VincularIhqInput(PayloadRecepcao):
    solicitacao_id: str = Field(min_length=1)
    caso_origem_numero: str = Field(min_length=1)
    divergencia_confirmada: bool = False
    observacoes: str | None = None


class CancelarCasoInput(PayloadRecepcao):
    numero_interno: str = Field(min_length=1)
    motivo: str


class CancelarExameSolicitacaoInput(PayloadRecepcao):
    solicitacao_id: str = Field(min_length=1)
    motivo: str


class AcionarPlantaoInput(PayloadRecepcao):
    numero_interno: str = Field(min_length=1)


class ContextoSemEtiqueta(PayloadRecepcao):
    tipo: Literal["SEM_ETIQUETA"]


class ContextoSolicitacao(PayloadRecepcao):
    tipo: Literal["SOLICITACAO"]
    solicitacao_ids: list[str] = Field(min_length=1)


class ContextoCaso(PayloadRecepcao):
    tipo: Literal["CASO"]
    caso_numero: str = Field(min_length=1)


ContextoNaoConformidade = Annotated[
    ContextoSemEtiqueta | ContextoSolicitacao | ContextoCaso,
    Field(discriminator="tipo"),
]


class RegistrarNaoConformidadeInput(PayloadRecepcao):
    contexto: ContextoNaoConformidade
    tipo: Literal[
        "SEM_SOLICITACAO_OU_ETIQUETA",
        "EXAME_NAO_CORRESPONDE_MATERIAL",
        "FALTA_DESCRICAO_FRASCO",
        "IDENTIFICACAO_ILEGIVEL",
        "NUMERACAO_FRASCOS_DIVERGENTE",
        "QUANTIDADE_FRASCOS_DIVERGENTE",
        "LATERALIDADE_DIVERGENTE",
        "FALTA_CARIMBO_ASSINATURA",
        "ACONDICIONAMENTO_INADEQUADO",
        "SOLICITACOES_DUPLICADAS",
        "PECAS_NAO_DESCRITAS",
        "SISCAN_INCORRETO",
        "SEM_AGENDAMENTO_CMCE",
        "OUTROS",
    ]
    descricao: str | None = None
    observacao: str | None = None
    unidade_origem: str | None = None
    nova_amostra_solicitada: bool


class AtualizarSituacaoDevolucaoInput(PayloadRecepcao):
    situacao: Literal["AGUARDANDO_NOVA_AMOSTRA", "NOVA_AMOSTRA_RECEBIDA", "ENCERRADA"]
