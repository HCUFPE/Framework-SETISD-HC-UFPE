from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.exame import Exame
from ...models.frasco import Frasco
from ...models.paciente_local import PacienteLocal
from ...services.maquina_estados import StatusFrasco


class FrascoRepository:
    """Acesso ORM aos frascos (App DB)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, frasco: Frasco) -> None:
        self.session.add(frasco)

    async def obter(self, id_frasco: str) -> Optional[Frasco]:
        return await self.session.get(Frasco, id_frasco)

    def _select_detalhe(self):
        """Frasco + exame + paciente, para fila de pendências e busca manual."""
        return (
            select(
                Frasco.id.label("id_frasco"),
                Exame.id.label("id_exame"),
                Frasco.codigo_interno,
                Frasco.status,
                Frasco.data_criacao,
                Exame.numero_solicitacao,
                Exame.numero_exame_aghu,
                Exame.tipo_peca,
                PacienteLocal.nome.label("paciente_nome"),
            )
            .join(Exame, Frasco.id_exame == Exame.id)
            .join(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
        )

    async def listar_pendencias_recepcao(self) -> List[Dict]:
        """Frascos recebidos que ainda não foram encaminhados à macroscopia."""
        stmt = (
            self._select_detalhe()
            .where(Frasco.status == StatusFrasco.NA_RECEPCAO)
            .order_by(Frasco.data_criacao.asc())
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def listar_pendencias_macroscopia(self) -> List[Dict]:
        stmt = (
            self._select_detalhe()
            .where(Frasco.status.in_([
                StatusFrasco.AGUARDANDO_MACROSCOPIA,
                StatusFrasco.EM_MACROSCOPIA,
            ]))
            .order_by(Frasco.data_criacao.asc())
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]

    async def buscar_detalhe(
        self, numero_solicitacao: Optional[str], codigo_interno: Optional[str]
    ) -> List[Dict]:
        stmt = self._select_detalhe()
        if numero_solicitacao:
            stmt = stmt.where(Exame.numero_solicitacao == numero_solicitacao)
        if codigo_interno:
            stmt = stmt.where(Frasco.codigo_interno == codigo_interno)
        stmt = stmt.order_by(Frasco.data_criacao.asc())
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(r) for r in rows]
