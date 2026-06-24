from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.exame import Exame


class ExameRepository:
    """Acesso ORM aos exames (App DB)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, exame: Exame) -> None:
        self.session.add(exame)

    async def obter(self, id_exame: str) -> Optional[Exame]:
        return await self.session.get(Exame, id_exame)

    async def listar(self) -> List[Exame]:
        stmt = select(Exame).order_by(Exame.data_recebimento.desc())
        return list((await self.session.execute(stmt)).scalars().all())
