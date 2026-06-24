from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.perfis import require_perfil
from ..controllers import historico_controller
from ..resources.database import get_app_db_session
from ..schemas.historico import HistoricoOut

router = APIRouter(prefix="/api/historico", tags=["Rastreabilidade"])


@router.get("", response_model=List[HistoricoOut])
async def listar_historico(
    id_exame: Optional[str] = Query(default=None),
    id_frasco: Optional[str] = Query(default=None),
    id_cassete: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Histórico completo de movimentação de um exame/frasco/cassete (RF040)."""
    return await historico_controller.listar_historico(
        session, id_exame=id_exame, id_frasco=id_frasco, id_cassete=id_cassete
    )
