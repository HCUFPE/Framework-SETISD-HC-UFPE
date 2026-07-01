from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.perfis import Perfil, require_perfil
from ..controllers import microscopia_controller
from ..resources.database import get_app_db_session

router = APIRouter(prefix="/api/microscopia", tags=["Microscopia"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


class LaudoRequest(BaseModel):
    acao: Literal["liberar", "revisao", "complemento"]
    responsavel: Optional[str] = None
    laudo: Optional[str] = None
    observacoes: Optional[str] = None


@router.get("/pendencias", response_model=List[dict])
async def listar_pendencias(
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.PATOLOGISTA, Perfil.RESIDENTE)),
):
    """Fila da microscopia: exames Em Microscopia ou em Revisão Pendente."""
    return await microscopia_controller.listar_pendencias(session)


@router.post("/{id_exame}/laudo", response_model=dict)
async def registrar_laudo(
    id_exame: str,
    dados: LaudoRequest,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.PATOLOGISTA, Perfil.RESIDENTE)),
):
    """Registra a decisão da microscopia (liberar / revisão / complemento) e
    transiciona o status do exame — persistido e visível no dashboard."""
    return await microscopia_controller.registrar_laudo(
        session,
        id_exame,
        dados.acao,
        dados.responsavel,
        dados.laudo,
        dados.observacoes,
        current_user.get("username"),
        _ip(request),
    )
