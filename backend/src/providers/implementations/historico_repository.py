from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.cassete import Cassete
from ...models.historico_movimentacao import HistoricoMovimentacao


class HistoricoRepository:
    """Acesso ORM ao histórico de movimentação (App DB)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar(
        self,
        id_exame: Optional[str] = None,
        id_frasco: Optional[str] = None,
        id_cassete: Optional[str] = None,
    ) -> List[HistoricoMovimentacao]:
        condicoes = []
        if id_exame:
            condicoes.append(HistoricoMovimentacao.id_exame == id_exame)
        if id_frasco:
            condicoes.append(HistoricoMovimentacao.id_frasco == id_frasco)
            # Inclui histórico dos cassetes filhos do frasco (ex.: registros de processamento)
            cassete_ids_stmt = select(Cassete.id).where(Cassete.id_frasco == id_frasco)
            condicoes.append(HistoricoMovimentacao.id_cassete.in_(cassete_ids_stmt))
        if id_cassete:
            condicoes.append(HistoricoMovimentacao.id_cassete == id_cassete)

        stmt = select(HistoricoMovimentacao)
        if condicoes:
            stmt = stmt.where(or_(*condicoes))
        stmt = stmt.order_by(HistoricoMovimentacao.timestamp_transicao.asc())
        return list((await self.session.execute(stmt)).scalars().all())
