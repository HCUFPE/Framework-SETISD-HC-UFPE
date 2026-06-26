from sqlalchemy.ext.asyncio import AsyncSession

from ...models.macroscopia import Macroscopia


class MacroscopiaRepository:
    """Acesso ORM aos registros de macroscopia (App DB)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, macroscopia: Macroscopia) -> None:
        self.session.add(macroscopia)
