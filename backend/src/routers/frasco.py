from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.perfis import Perfil, require_perfil
from ..controllers import macroscopia_controller, triagem_controller
from ..resources.database import get_app_db_session
from ..schemas.etiqueta import EtiquetaOut
from ..schemas.frasco import FrascoDetalhe, FrascoOut

router = APIRouter(prefix="/api/frascos", tags=["Frascos"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/buscar", response_model=List[FrascoDetalhe])
async def buscar_frasco(
    numero_solicitacao: Optional[str] = Query(default=None),
    codigo_interno: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Identificação manual de frasco (substitui a leitura por QR enquanto o
    hardware não chega)."""
    return await macroscopia_controller.buscar_frasco(
        session, numero_solicitacao, codigo_interno
    )


@router.get("/{id_frasco}/etiqueta", response_model=EtiquetaOut)
async def obter_etiqueta(
    id_frasco: str,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    return await triagem_controller.obter_etiqueta_frasco(session, id_frasco)


@router.post("/{id_frasco}/encaminhar-macroscopia", response_model=FrascoOut)
async def encaminhar_macroscopia(
    id_frasco: str,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.RECEPCIONISTA)),
):
    return await triagem_controller.encaminhar_para_macroscopia(
        session, id_frasco, current_user.get("username"), _ip(request)
    )


@router.post("/{id_frasco}/iniciar-macroscopia", response_model=FrascoOut)
async def iniciar_macroscopia(
    id_frasco: str,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.MACROSCOPISTA)),
):
    return await macroscopia_controller.iniciar_macroscopia(
        session, id_frasco, current_user.get("username"), _ip(request)
    )
