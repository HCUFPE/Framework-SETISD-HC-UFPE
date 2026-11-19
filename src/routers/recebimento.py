from datetime import date
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field, StrictBool, StrictInt
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..controllers import recebimento_controller
from ..dependencies import get_recebimento_provider, get_solicitacao_provider
from ..providers.interfaces.recebimento_provider_interface import RecebimentoProviderInterface
from ..providers.interfaces.solicitacao_provider_interface import (COLUNAS_ORDENAVEIS,SolicitacaoProviderInterface,)
from ..resources.database import get_app_db_session

# --- PONTO ÚNICO DE CONFIGURAÇÃO PARA ESTE ROTEADOR ---
# Para ler direto do AGHU, altere esta linha para "postgres".
STRATEGY = "csv"
# ----------------------------------------------------

router = APIRouter(
    prefix="/api/recebimento",
    tags=["Recebimento de Amostras"],
    dependencies=[Depends(auth_handler.decode_token)],
)

CodigoSolicitacao = Annotated[str, Path(min_length=1, max_length=60, pattern=r"^[\w\-. ]+$")]


class AmostraRecebimento(BaseModel):
    """Marcação de uma amostra enviada pela tela."""

    numero_amostra: StrictInt = Field(ge=1)
    receber: StrictBool
    descricao_informada: Optional[str] = Field(default=None, max_length=200)


class DadosHp(BaseModel):
    """Dados que a recepção acrescenta ao receber um HP, com valores controlados (RNF009)."""

    quantidade_pecas: StrictInt = Field(ge=1)
    urgente: StrictBool
    procedimento_id: StrictInt


class RecebimentoEntrada(BaseModel):
    """Corpo do recebimento de uma solicitação, com um único checklist para o recebimento."""

    amostras: List[AmostraRecebimento] = Field(min_length=1)
    sigla_confere: StrictBool = False
    descricao_confere: StrictBool = False
    recipientes_confere: StrictBool = False
    dados_hp: Optional[DadosHp] = None
    referencia_hp: Optional[str] = Field(default=None, max_length=30)


class NaoConformidadeEntrada(BaseModel):
    """Corpo do registro de não conformidade."""

    motivo_id: int
    observacao: str = Field(min_length=1, max_length=2000)
    numero_cmce: Optional[str] = Field(default=None, max_length=30)
    medico_solicitante: Optional[str] = Field(default=None, max_length=200)


def _usuario_do_token(payload: Dict[str, Any]) -> str:
    """Retorna o login do usuário a partir do token; responde 401 se ele não vier no token."""
    usuario = payload.get("sub")
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificação do usuário.",
        )
    return usuario


def _ip_de_origem(request: Request) -> Optional[str]:
    """Retorna o IP de origem da requisição."""
    return request.client.host if request.client else None


@router.get("/motivos-nao-conformidade", response_model=List[dict])
async def listar_motivos(
    recebimento_provider: RecebimentoProviderInterface = Depends(get_recebimento_provider),
) -> List[Dict[str, Any]]:
    """Lista os motivos de não conformidade ativos."""
    return await recebimento_controller.listar_motivos(recebimento_provider)


@router.get("/procedimentos-hp", response_model=List[dict])
async def listar_procedimentos_hp(
    recebimento_provider: RecebimentoProviderInterface = Depends(get_recebimento_provider),
) -> List[Dict[str, Any]]:
    """Lista os procedimentos de HP ativos."""
    return await recebimento_controller.listar_procedimentos_hp(recebimento_provider)


@router.get("/solicitacoes", response_model=dict)
async def listar_solicitacoes(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    somente_recebiveis: bool = Query(default=True),
    ordenar_por: Optional[str] = Query(default=None, pattern=f"^({'|'.join(COLUNAS_ORDENAVEIS)})$"),
    direcao: str = Query(default="asc", pattern="^(asc|desc)$"),
    filtro_codigo: Optional[str] = Query(default=None, max_length=30),
    filtro_data: Optional[date] = Query(default=None),
    filtro_paciente: Optional[str] = Query(default=None, max_length=80),
    filtro_prontuario: Optional[str] = Query(default=None, max_length=30),
    filtro_origem: Optional[str] = Query(default=None, max_length=80),
    filtro_clinica: Optional[str] = Query(default=None, max_length=80),
    filtro_bancada: Optional[str] = Query(default=None, max_length=10),
    solicitacao_provider: SolicitacaoProviderInterface = Depends(get_solicitacao_provider(STRATEGY)),
    recebimento_provider: RecebimentoProviderInterface = Depends(get_recebimento_provider),
) -> Dict[str, Any]:
    """
    Lista as solicitações do AGHU com paginação: urgências primeiro e, depois, das mais recentes
    para as mais antigas. Os filtros por coluna se combinam e `ordenar_por` troca a ordem padrão.
    """
    return await recebimento_controller.listar_solicitacoes(
        pagina,
        por_pagina,
        somente_recebiveis,
        solicitacao_provider,
        recebimento_provider,
        filtros={
            "codigo": filtro_codigo,
            "data": filtro_data.isoformat() if filtro_data else None,
            "paciente": filtro_paciente,
            "prontuario": filtro_prontuario,
            "origem": filtro_origem,
            "clinica": filtro_clinica,
            "bancada": filtro_bancada,
        },
        ordenar_por=ordenar_por,
        direcao=direcao,
    )

@router.get("/solicitacoes/{codigo}", response_model=dict)
async def obter_solicitacao(
    codigo: CodigoSolicitacao,
    solicitacao_provider: SolicitacaoProviderInterface = Depends(get_solicitacao_provider(STRATEGY)),
    recebimento_provider: RecebimentoProviderInterface = Depends(get_recebimento_provider),
) -> Dict[str, Any]:
    """Busca a solicitação pelo código lido ou digitado e retorna os dados para a conferência."""
    return await recebimento_controller.obter_solicitacao(
        codigo, solicitacao_provider, recebimento_provider
    )


@router.post(
    "/solicitacoes/{codigo}/recebimentos",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def receber_amostras(
    codigo: CodigoSolicitacao,
    entrada: RecebimentoEntrada,
    request: Request,
    token: Dict[str, Any] = Depends(auth_handler.decode_token),
    solicitacao_provider: SolicitacaoProviderInterface = Depends(get_solicitacao_provider(STRATEGY)),
    recebimento_provider: RecebimentoProviderInterface = Depends(get_recebimento_provider),
    db: AsyncSession = Depends(get_app_db_session),
) -> Dict[str, Any]:
    """Conclui o recebimento das amostras marcadas e gera o nº interno de cada exame."""
    return await recebimento_controller.receber_amostras(
        codigo=codigo,
        marcacoes=[amostra.model_dump() for amostra in entrada.amostras],
        checklist={
            "sigla_confere": entrada.sigla_confere,
            "descricao_confere": entrada.descricao_confere,
            "recipientes_confere": entrada.recipientes_confere,
        },
        dados_hp=entrada.dados_hp.model_dump() if entrada.dados_hp else None,
        referencia_hp=entrada.referencia_hp,
        usuario=_usuario_do_token(token),
        ip_origem=_ip_de_origem(request),
        solicitacao_provider=solicitacao_provider,
        recebimento_provider=recebimento_provider,
        db=db,
    )


@router.post(
    "/solicitacoes/{codigo}/nao-conformidades",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_nao_conformidade(
    codigo: CodigoSolicitacao,
    entrada: NaoConformidadeEntrada,
    request: Request,
    token: Dict[str, Any] = Depends(auth_handler.decode_token),
    solicitacao_provider: SolicitacaoProviderInterface = Depends(get_solicitacao_provider(STRATEGY)),
    recebimento_provider: RecebimentoProviderInterface = Depends(get_recebimento_provider),
    db: AsyncSession = Depends(get_app_db_session),
) -> Dict[str, Any]:
    """Registra a não conformidade e marca a solicitação como devolvida à origem."""
    return await recebimento_controller.registrar_nao_conformidade(
        codigo=codigo,
        motivo_id=entrada.motivo_id,
        observacao=entrada.observacao,
        numero_cmce=entrada.numero_cmce,
        medico_solicitante=entrada.medico_solicitante,
        usuario=_usuario_do_token(token),
        ip_origem=_ip_de_origem(request),
        solicitacao_provider=solicitacao_provider,
        recebimento_provider=recebimento_provider,
        db=db,
    )
