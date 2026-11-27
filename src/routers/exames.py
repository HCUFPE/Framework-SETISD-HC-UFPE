"""
Endpoints da Fila de Exames (``/api/exames``) — TASK-010
=======================================================
Rotas protegidas (Default-Private) para a Central de Marcação operar a fila
priorizada: listagem com filtros, detalhe com alertas, confirmação em 24h,
vinculação por busca ativa e consulta somente-leitura ao AGHU.
"""

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..config import settings
from ..controllers import fila_controller
from ..dependencies import get_exame_provider, get_fila_provider
from ..providers.interfaces.exame_provider_interface import ExameProviderInterface
from ..providers.interfaces.fila_provider_interface import FilaProviderInterface
from ..resources.database import get_app_db_session
from ..schemas.fila import (
    AtualizarStatusRequest,
    ItemFila,
    ItemFilaDetalhe,
    RegiaoGeografica,
    StatusHigienizacao,
    StatusOperacional,
    VincularSolicitacaoRequest,
)

# Dependência do provedor AGHU definida pela configuração (EXAME_PROVIDER_TYPE).
provider_aghu = get_exame_provider(settings.EXAME_PROVIDER_TYPE)

router = APIRouter(
    prefix="/api/exames",
    tags=["Fila de Exames"],
    dependencies=[Depends(auth_handler.decode_token)],
)

AghuDep = Annotated[ExameProviderInterface, Depends(provider_aghu)]
FilaDep = Annotated[FilaProviderInterface, Depends(get_fila_provider)]
UsuarioDep = Annotated[dict, Depends(auth_handler.decode_token)]
DbDep = Annotated[AsyncSession, Depends(get_app_db_session)]


def _usuario(payload: dict) -> str:
    """Extrai o login do usuário autenticado do token."""
    return str(payload.get("sub") or payload.get("username") or "desconhecido")


def _ip(request: Request) -> Optional[str]:
    """IP de origem da requisição."""
    return request.client.host if request.client else None


@router.get("/fila", response_model=list[ItemFila])
async def listar_fila(
    response: Response,
    fila: FilaDep,
    aghu: AghuDep,
    codigo_exame: Optional[str] = None,
    unidade: Optional[str] = None,
    status_operacional: Optional[StatusOperacional] = None,
    status_higienizacao: Optional[StatusHigienizacao] = None,
    municipio: Optional[str] = None,
    regiao: Optional[RegiaoGeografica] = None,
    apenas_tfd: bool = False,
    apenas_24h_vencidos: bool = False,
    busca: Optional[str] = None,
    limit: Annotated[Optional[int], Query(ge=1, le=500)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict[str, Any]]:
    """Lista a fila priorizada (score, motivos e alertas) com filtros que não alteram o score."""
    filtros = fila_controller.montar_filtros(
        codigo_exame=codigo_exame,
        unidade=unidade,
        status_operacional=status_operacional,
        status_higienizacao=status_higienizacao,
        municipio=municipio,
        regiao=regiao,
        apenas_tfd=apenas_tfd,
        busca=busca,
    )
    itens, total = await fila_controller.montar_fila(
        fila, aghu, filtros, apenas_24h_vencidos=apenas_24h_vencidos, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return itens


@router.get("/fila/{item_id}", response_model=ItemFilaDetalhe)
async def obter_item_fila(item_id: int, fila: FilaDep, aghu: AghuDep) -> dict[str, Any]:
    """Detalhe do item com outros exames do prontuário (fila + AGHU), alertas e preparo."""
    return await fila_controller.obter_detalhe(item_id, fila, aghu)


@router.patch("/fila/{item_id}/status", response_model=ItemFilaDetalhe)
async def atualizar_status_item(
    item_id: int,
    corpo: AtualizarStatusRequest,
    request: Request,
    db: DbDep,
    fila: FilaDep,
    aghu: AghuDep,
    usuario: UsuarioDep,
) -> dict[str, Any]:
    """Transita o status operacional (confirmação 24h) com auditoria NEGOCIO_CLINICO."""
    return await fila_controller.atualizar_status(
        item_id,
        corpo.status_operacional,
        db=db,
        fila=fila,
        aghu=aghu,
        usuario=_usuario(usuario),
        ip_origem=_ip(request),
        data_agendada_aghu=corpo.data_agendada_aghu,
        preparo_orientado=corpo.preparo_orientado,
        observacoes=corpo.observacoes,
    )


@router.patch("/fila/{item_id}/vincular-solicitacao", response_model=ItemFilaDetalhe)
async def vincular_solicitacao_item(
    item_id: int,
    corpo: VincularSolicitacaoRequest,
    request: Request,
    db: DbDep,
    fila: FilaDep,
    aghu: AghuDep,
    usuario: UsuarioDep,
) -> dict[str, Any]:
    """Vincula a solicitação correta encontrada no AGHU (busca ativa) com auditoria."""
    return await fila_controller.vincular_solicitacao(
        item_id,
        corpo.codigo_solicitacao,
        corpo.codigo_exame,
        db=db,
        fila=fila,
        aghu=aghu,
        usuario=_usuario(usuario),
        ip_origem=_ip(request),
    )


@router.get("/aghu/buscar", response_model=list[dict])
async def buscar_no_aghu(
    aghu: AghuDep,
    prontuario: Optional[str] = None,
    codigo_solicitacao: Optional[str] = None,
    nome: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Busca ativa somente-leitura no AGHU por prontuário, solicitação ou parte do nome."""
    return await fila_controller.buscar_aghu(aghu, prontuario, codigo_solicitacao, nome)
