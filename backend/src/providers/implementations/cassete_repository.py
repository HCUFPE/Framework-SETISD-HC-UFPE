from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.cassete import Cassete
from ...models.exame import Exame
from ...models.frasco import Frasco
from ...models.paciente_local import PacienteLocal


class CasseteRepository:
    """Acesso ORM aos cassetes (App DB)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, cassete: Cassete) -> None:
        self.session.add(cassete)

    async def obter(self, id_cassete: str) -> Optional[Cassete]:
        return (
            await self.session.execute(
                select(Cassete).where(Cassete.id == id_cassete)
            )
        ).scalar_one_or_none()

    async def listar_por_frasco(self, id_frasco: str) -> List[Cassete]:
        stmt = (
            select(Cassete)
            .where(Cassete.id_frasco == id_frasco)
            .order_by(Cassete.letra_fragmento.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def listar_por_lote(self, id_lote: str) -> List[Cassete]:
        stmt = (
            select(Cassete)
            .where(Cassete.id_lote_processamento == id_lote)
            .order_by(Cassete.letra_fragmento.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def listar_pendencias_processamento(self) -> List[dict]:
        """Cassetes aguardando entrada em lote de processamento."""
        stmt = (
            select(
                Cassete.id,
                Cassete.letra_fragmento,
                Cassete.qr_code,
                Cassete.status,
                Cassete.data_criacao,
                Frasco.codigo_interno.label("codigo_interno_frasco"),
                Exame.numero_solicitacao,
                PacienteLocal.nome.label("paciente_nome"),
            )
            .join(Frasco, Cassete.id_frasco == Frasco.id)
            .join(Exame, Frasco.id_exame == Exame.id)
            .outerjoin(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
            .where(Cassete.status == "Aguardando Processamento")
            .order_by(Cassete.data_criacao.asc())
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]
