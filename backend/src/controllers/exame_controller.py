from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.exame import Exame
from ..models.paciente_local import PacienteLocal
from ..providers.implementations.exame_repository import ExameRepository

_SLA_DIAS = 20


def _dias_desde(data: datetime) -> int:
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = agora - data.replace(tzinfo=None) if data else None
    return delta.days if delta else 0


async def listar_exames(session: AsyncSession) -> List[Exame]:
    return await ExameRepository(session).listar()


async def obter_exame(session: AsyncSession, id_exame: str) -> Exame:
    exame = await ExameRepository(session).obter(id_exame)
    if exame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exame não encontrado."
        )
    return exame


async def listar_dashboard(session: AsyncSession) -> list[dict]:
    """
    Retorna exames com nome do paciente e flag de SLA para o dashboard do frontend.
    Estrutura alinhada com o mock de dashboard.vue.
    """
    stmt = (
        select(
            Exame.id,
            Exame.numero_solicitacao,
            Exame.status,
            Exame.data_recebimento,
            PacienteLocal.nome.label("nome_paciente"),
        )
        .join(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
        .order_by(Exame.data_recebimento.desc())
    )
    rows = (await session.execute(stmt)).all()

    result = []
    for row in rows:
        dias = _dias_desde(row.data_recebimento) if row.data_recebimento else 0
        result.append(
            {
                "id": row.id,
                "solicitacao": row.numero_solicitacao,
                "paciente": row.nome_paciente or "",
                "etapa": row.status,
                "data_entrada": row.data_recebimento,
                "atrasado": dias >= _SLA_DIAS,
            }
        )
    return result
