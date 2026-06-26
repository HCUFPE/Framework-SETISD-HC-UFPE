from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.historico_movimentacao import HistoricoMovimentacao
from ..providers.implementations.historico_repository import HistoricoRepository


async def listar_historico(
    session: AsyncSession,
    id_exame: Optional[str] = None,
    id_frasco: Optional[str] = None,
    id_cassete: Optional[str] = None,
) -> List[HistoricoMovimentacao]:
    if not any([id_exame, id_frasco, id_cassete]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe id_exame, id_frasco ou id_cassete.",
        )
    return await HistoricoRepository(session).listar(
        id_exame=id_exame, id_frasco=id_frasco, id_cassete=id_cassete
    )
