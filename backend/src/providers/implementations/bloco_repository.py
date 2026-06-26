from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...models.bloco_parafina import BlocoParafina
from ...models.cassete import Cassete
from ...models.exame import Exame
from ...models.frasco import Frasco
from ...models.paciente_local import PacienteLocal


class BlocoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, bloco: BlocoParafina) -> None:
        self.session.add(bloco)

    async def obter(self, id_bloco: str) -> Optional[BlocoParafina]:
        return (
            await self.session.execute(
                select(BlocoParafina).where(BlocoParafina.id == id_bloco)
            )
        ).scalar_one_or_none()

    async def obter_por_codigo(self, codigo_bloco: str) -> Optional[BlocoParafina]:
        return (
            await self.session.execute(
                select(BlocoParafina).where(BlocoParafina.codigo_bloco == codigo_bloco)
            )
        ).scalar_one_or_none()

    async def obter_por_cassete(self, id_cassete: str) -> Optional[BlocoParafina]:
        return (
            await self.session.execute(
                select(BlocoParafina).where(BlocoParafina.id_cassete == id_cassete)
            )
        ).scalar_one_or_none()

    async def listar_por_lote(self, id_lote: str) -> List[BlocoParafina]:
        stmt = (
            select(BlocoParafina)
            .where(BlocoParafina.id_lote == id_lote)
            .order_by(BlocoParafina.codigo_bloco.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def listar_pendencias_corte(self) -> List[dict]:
        """Blocos aguardando corte microtômico — fila da estação."""
        stmt = (
            select(
                BlocoParafina.id,
                BlocoParafina.codigo_bloco,
                BlocoParafina.status,
                BlocoParafina.data_criacao,
                Cassete.letra_fragmento,
                Frasco.codigo_interno.label("codigo_interno_frasco"),
                Exame.numero_solicitacao,
                Exame.tipo_peca,
                PacienteLocal.nome.label("paciente_nome"),
            )
            .join(Cassete, BlocoParafina.id_cassete == Cassete.id)
            .join(Frasco, Cassete.id_frasco == Frasco.id)
            .join(Exame, Frasco.id_exame == Exame.id)
            .outerjoin(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
            .where(BlocoParafina.status == "Aguardando Corte")
            .order_by(BlocoParafina.data_criacao.asc())
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def buscar_detalhe(self, codigo_bloco: Optional[str]) -> List[dict]:
        """Busca manual por código de bloco."""
        conditions = []
        if codigo_bloco:
            conditions.append(BlocoParafina.codigo_bloco.ilike(f"%{codigo_bloco}%"))

        stmt = (
            select(
                BlocoParafina.id,
                BlocoParafina.codigo_bloco,
                BlocoParafina.status,
                BlocoParafina.data_criacao,
                Cassete.letra_fragmento,
                Exame.numero_solicitacao,
                PacienteLocal.nome.label("paciente_nome"),
            )
            .join(Cassete, BlocoParafina.id_cassete == Cassete.id)
            .join(Frasco, Cassete.id_frasco == Frasco.id)
            .join(Exame, Frasco.id_exame == Exame.id)
            .outerjoin(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
            .where(*conditions)
            .order_by(BlocoParafina.codigo_bloco.asc())
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]
