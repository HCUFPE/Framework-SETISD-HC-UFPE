from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.paciente_local import PacienteLocal


class PacienteLocalRepository:
    """Acesso ORM ao cache local de pacientes (App DB)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, paciente: PacienteLocal) -> None:
        self.session.add(paciente)

    async def obter(self, id_paciente: str) -> Optional[PacienteLocal]:
        return await self.session.get(PacienteLocal, id_paciente)

    async def buscar_por_documento(
        self, cpf: Optional[str], cns: Optional[str]
    ) -> Optional[PacienteLocal]:
        if not cpf and not cns:
            return None
        condicoes = []
        if cpf:
            condicoes.append(PacienteLocal.cpf == cpf)
        if cns:
            condicoes.append(PacienteLocal.cns == cns)
        stmt = (
            select(PacienteLocal)
            .where(or_(*condicoes), PacienteLocal.ativo.is_(True))
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()
