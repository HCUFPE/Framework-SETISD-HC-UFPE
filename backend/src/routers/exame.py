from typing import List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.perfis import Perfil, require_perfil
from ..controllers import exame_controller, triagem_controller
from ..resources.database import get_app_db_session
from ..schemas.exame import DashboardExameOut, ExameCreate, ExameOut
from ..schemas.resultados import TriagemResult

router = APIRouter(prefix="/api/exames", tags=["Exames / Triagem"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=TriagemResult, status_code=201)
async def registrar_recebimento(
    dados: ExameCreate,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.RECEPCIONISTA)),
):
    """Triagem: registra o recebimento da peça, gera número de solicitação,
    cria o frasco com seu código de identificação e devolve a etiqueta."""
    return await triagem_controller.registrar_recebimento(
        session, dados, current_user.get("username"), _ip(request)
    )


@router.get("/dashboard", response_model=List[DashboardExameOut])

async def listar_dashboard(
    etapa: str | None = Query(None, description="Filtra por etapa do processo"),
    codigo_aghu: str | None = Query(None, description="Filtra por código do AGHU"),
    codigo_interno: str | None = Query(None, description="Filtra por código interno/solicitação"),
    nome_paciente: str | None = Query(None, description="Filtra por nome do paciente"),
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Dashboard: lista exames com nome do paciente e flag de SLA com opção de filtros."""
    return await exame_controller.listar_dashboard(
        session,
        etapa=etapa,
        codigo_aghu=codigo_aghu,
        codigo_interno=codigo_interno,
        nome_paciente=nome_paciente,
    )



@router.get("", response_model=List[ExameOut])
async def listar_exames(
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    return await exame_controller.listar_exames(session)


@router.get("/{id_exame}/detalhe")
async def obter_detalhe(
    id_exame: str,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Visão unificada do caso (exame + paciente + frasco + macroscopia +
    cassetes + blocos + lâminas) para o modal 'Ver detalhes' do dashboard."""
    return await exame_controller.obter_detalhe(session, id_exame)


@router.get("/{id_exame}", response_model=ExameOut)
async def obter_exame(
    id_exame: str,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    return await exame_controller.obter_exame(session, id_exame)
