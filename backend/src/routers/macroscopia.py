from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.perfis import Perfil, require_perfil
from ..controllers import macroscopia_controller
from ..resources.database import get_app_db_session
from ..schemas.frasco import FrascoDetalhe
from ..schemas.macroscopia import MacroscopiaCreate
from ..schemas.resultados import MacroscopiaResult

router = APIRouter(prefix="/api/macroscopia", tags=["Macroscopia"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/pendencias", response_model=List[FrascoDetalhe])
async def listar_pendencias(
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.MACROSCOPISTA)),
):
    """Fila da estação: frascos aguardando macroscopia."""
    return await macroscopia_controller.listar_pendencias(session)


@router.post("", response_model=MacroscopiaResult, status_code=201)
async def registrar_macroscopia(
    dados: MacroscopiaCreate,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.MACROSCOPISTA)),
):
    """Registra a macroscopia do frasco e gera os cassetes (A, B, C, ...)."""
    return await macroscopia_controller.registrar_macroscopia(
        session, dados, current_user.get("username"), _ip(request)
    )
