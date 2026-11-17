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


class ItensConferenciaInput(PayloadRecepcao):
    identificacao_confere: bool
    material_confere: bool
    quantidade_confere: bool
    recipiente_adequado: bool


class ConfirmarEntradaInput(PayloadRecepcao):
    solicitacao_codigo: str = Field(min_length=1)
    conferencia: ItensConferenciaInput
    tipo_exame: Literal["HP", "CG", "CCV", "CO"]
    quantidade: int = Field(ge=1)
    urgente: bool
    motivo_urgencia: str | None = None
    procedimento: str = Field(min_length=1)
    observacoes: str | None = None


class CancelarCasoInput(PayloadRecepcao):
    numero_interno: str = Field(min_length=1)
    motivo: str


class AcionarPlantaoInput(PayloadRecepcao):
    numero_interno: str = Field(min_length=1)


class ContextoSemEtiqueta(PayloadRecepcao):
    tipo: Literal["SEM_ETIQUETA"]


class ContextoSolicitacao(PayloadRecepcao):
    tipo: Literal["SOLICITACAO"]
    solicitacao_codigo: str = Field(min_length=1)
    conferencia: ItensConferenciaInput


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
        "SEM_ETIQUETA_AGHU",
        "IDENTIFICACAO_DIVERGENTE",
        "QUANTIDADE_DIVERGENTE",
        "MATERIAL_INADEQUADO",
        "RECIPIENTE_DANIFICADO",
        "FIXACAO_INADEQUADA",
        "REQUISICAO_INCOMPLETA",
        "OUTRO",
    ]
    descricao: str
    unidade_origem: str | None = None
    nova_amostra_solicitada: bool


class AtualizarSituacaoDevolucaoInput(PayloadRecepcao):
    situacao: Literal["AGUARDANDO_NOVA_AMOSTRA", "NOVA_AMOSTRA_RECEBIDA", "ENCERRADA"]

