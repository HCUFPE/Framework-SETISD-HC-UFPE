from typing import List

from fastapi import APIRouter, Depends, Request
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
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Dashboard: lista exames com nome do paciente e flag de SLA."""
    return await exame_controller.listar_dashboard(session)


@router.get("", response_model=List[ExameOut])
async def listar_exames(
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    return await exame_controller.listar_exames(session)


@router.get("/{id_exame}", response_model=ExameOut)
async def obter_exame(
    id_exame: str,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    return await exame_controller.obter_exame(session, id_exame)
