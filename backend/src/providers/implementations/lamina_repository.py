from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.lamina import Lamina


class LaminaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, lamina: Lamina) -> None:
        self.session.add(lamina)

    async def listar_por_bloco(self, id_bloco: str) -> List[Lamina]:
        stmt = (
            select(Lamina)
            .where(Lamina.id_bloco == id_bloco)
            .order_by(Lamina.numero_lamina.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def contar_por_bloco(self, id_bloco: str) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).where(Lamina.id_bloco == id_bloco)
        )
        return result.scalar_one()
