"""
Provedor SQLAlchemy da Fila de Exames no SQLite local (``data/app.db``)
======================================================================
Implementa ``FilaProviderInterface`` sobre os models da Fase 1. Retorna
dicionários (sem expor objetos ORM às camadas superiores). As escritas são
feitas na sessão corrente sem commit: o commit acontece junto com o registro
de auditoria, garantindo que alteração e log sejam gravados juntos.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import AcompanhamentoFila, IncompatibilidadeExame, RegraExame, RegraPrioridade
from ..interfaces.fila_provider_interface import FilaProviderInterface


def _para_dict(obj: Any) -> Dict[str, Any]:
    """Converte um objeto ORM em dicionário com suas colunas mapeadas."""
    return {attr.key: getattr(obj, attr.key) for attr in inspect(obj).mapper.column_attrs}


class FilaSqliteProvider(FilaProviderInterface):
    """Acesso à fila e às regras configuráveis no banco local da aplicação."""

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessão assíncrona do SQLite local por injeção de dependência."""
        self.session = session

    async def _obter_orm(self, item_id: int) -> Optional[AcompanhamentoFila]:
        """Busca o objeto ORM de um item não excluído."""
        stmt = select(AcompanhamentoFila).where(
            AcompanhamentoFila.id == item_id, AcompanhamentoFila.deleted_at.is_(None)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def listar_itens_ativos(self) -> List[Dict[str, Any]]:
        """Retorna todos os itens da fila não excluídos logicamente."""
        stmt = (
            select(AcompanhamentoFila)
            .where(AcompanhamentoFila.deleted_at.is_(None))
            .order_by(AcompanhamentoFila.id)
        )
        return [_para_dict(i) for i in (await self.session.execute(stmt)).scalars()]

    async def obter_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um item não excluído pelo id, ou ``None``."""
        item = await self._obter_orm(item_id)
        return _para_dict(item) if item else None

    async def listar_por_prontuario(self, prontuario: str) -> List[Dict[str, Any]]:
        """Retorna os itens não excluídos de um prontuário."""
        stmt = (
            select(AcompanhamentoFila)
            .where(
                AcompanhamentoFila.prontuario == prontuario,
                AcompanhamentoFila.deleted_at.is_(None),
            )
            .order_by(AcompanhamentoFila.id)
        )
        return [_para_dict(i) for i in (await self.session.execute(stmt)).scalars()]

    async def existe_item_ativo(
        self, prontuario: str, codigo_exame: str, excluir_id: Optional[int] = None
    ) -> bool:
        """Indica se há outro item válido, não cancelado e não excluído, do mesmo prontuário e exame."""
        stmt = select(AcompanhamentoFila.id).where(
            AcompanhamentoFila.prontuario == prontuario,
            AcompanhamentoFila.codigo_exame == codigo_exame,
            AcompanhamentoFila.status_higienizacao == "VALIDA",
            AcompanhamentoFila.status_operacional != "CANCELADO",
            AcompanhamentoFila.deleted_at.is_(None),
        )
        if excluir_id is not None:
            stmt = stmt.where(AcompanhamentoFila.id != excluir_id)
        return (await self.session.execute(stmt.limit(1))).first() is not None

    async def atualizar_item(self, item_id: int, campos: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica os campos ao item na sessão corrente (sem commit) e retorna o item atualizado."""
        item = await self._obter_orm(item_id)
        if item is None:
            raise LookupError(f"Item {item_id} não encontrado na fila.")
        for campo, valor in campos.items():
            setattr(item, campo, valor)
        await self.session.flush()
        return _para_dict(item)

    async def listar_regras_prioridade(self) -> List[Dict[str, Any]]:
        """Retorna as regras de prioridade ativas e não excluídas."""
        stmt = (
            select(RegraPrioridade)
            .where(RegraPrioridade.ativo.is_(True), RegraPrioridade.deleted_at.is_(None))
            .order_by(RegraPrioridade.id)
        )
        return [_para_dict(r) for r in (await self.session.execute(stmt)).scalars()]

    async def listar_regras_exames(self) -> List[Dict[str, Any]]:
        """Retorna as regras de exame ativas e não excluídas."""
        stmt = (
            select(RegraExame)
            .where(RegraExame.ativo.is_(True), RegraExame.deleted_at.is_(None))
            .order_by(RegraExame.id)
        )
        return [_para_dict(r) for r in (await self.session.execute(stmt)).scalars()]

    async def listar_incompatibilidades(self) -> List[Dict[str, Any]]:
        """Retorna as incompatibilidades ativas e não excluídas."""
        stmt = (
            select(IncompatibilidadeExame)
            .where(
                IncompatibilidadeExame.ativo.is_(True),
                IncompatibilidadeExame.deleted_at.is_(None),
            )
            .order_by(IncompatibilidadeExame.id)
        )
        return [_para_dict(r) for r in (await self.session.execute(stmt)).scalars()]
