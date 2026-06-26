from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.lote_processamento import LoteProcessamento


class LoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, lote: LoteProcessamento) -> None:
        self.session.add(lote)

    async def obter(self, id_lote: str) -> Optional[LoteProcessamento]:
        return (
            await self.session.execute(
                select(LoteProcessamento).where(LoteProcessamento.id == id_lote)
            )
        ).scalar_one_or_none()

    async def listar(self) -> List[LoteProcessamento]:
        stmt = select(LoteProcessamento).order_by(LoteProcessamento.data_criacao.desc())
        return list((await self.session.execute(stmt)).scalars().all())
