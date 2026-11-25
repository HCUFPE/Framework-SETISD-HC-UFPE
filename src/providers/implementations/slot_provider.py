"""
Provedor local de vagas (agenda_slots)
======================================
Implementação sobre o banco SQLite da aplicação. As ocupações são sempre
derivadas dos agendamentos ATIVOS — nunca armazenamos um contador que possa
divergir da realidade após remarcar ou cancelar.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...helpers.string_helper import parse_datetime
from ...models.agendamento import AgendaSlot, Agendamento
from ..interfaces.slot_provider_interface import SlotProviderInterface

STATUS_SLOT = {"DISPONIVEL", "LOTADO", "ENCERRADO"}


def para_utc_naive(valor: datetime) -> datetime:
    """Converte datetimes com ou sem fuso para UTC naive (padrão do SQLite)."""
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc).replace(tzinfo=None)


def para_utc_aware(valor: datetime) -> datetime:
    """Converte datetimes do SQLite para UTC com fuso explícito."""
    if valor is None:
        return datetime.now(timezone.utc)
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def para_iso(valor: Optional[datetime]) -> Optional[str]:
    """Serializa para ISO-8601 com fuso UTC."""
    if valor is None:
        return None
    return para_utc_aware(valor).isoformat()


def _status_publico(slot: AgendaSlot, livres: int) -> str:
    """Traduz a situação interna para o enum do contrato HTTP."""
    situacao = (slot.situacao or "").strip().upper()
    if situacao in STATUS_SLOT:
        return situacao
    if situacao in {"FECHADO", "CLOSED", "INATIVO", "ENCERRADA"}:
        return "ENCERRADO"
    return "LOTADO" if livres <= 0 else "DISPONIVEL"


def slot_para_dto(slot: AgendaSlot, ocupadas: int) -> Dict[str, Any]:
    """Converte o modelo em `AgendaSlot` (camelCase) sem expor PHI."""
    capacidade = int(slot.capacidade or 0)
    livres = max(0, capacidade - int(ocupadas or 0))
    return {
        "id": slot.id,
        "unidade": slot.unidade,
        "codigoExame": slot.codigo_exame or "",
        "nomeExame": slot.nome_exame or "",
        "inicio": para_iso(slot.inicio),
        "fim": para_iso(slot.fim),
        "capacidade": capacidade,
        "ocupadas": int(ocupadas or 0),
        "livres": livres,
        "status": _status_publico(slot, livres),
    }


class SlotProvider(SlotProviderInterface):
    """Leitura e manutenção das vagas locais na aplicação."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _ocupadas_por_slot(self, ids: List[str]) -> Dict[str, int]:
        """Conta agendamentos ATIVOS e PROPOSTOS agrupados por slot."""
        if not ids:
            return {}
        linhas = (
            await self.db.execute(
                select(Agendamento.slot_id, func.count(Agendamento.id))
                .where(
                    Agendamento.slot_id.in_(ids),
                    Agendamento.status.in_(("ATIVO", "PROPOSTO")),
                    Agendamento.deleted_at.is_(None),
                )
                .group_by(Agendamento.slot_id)
            )
        ).all()
        return {str(slot_id): int(total) for slot_id, total in linhas}

    async def listar(
        self,
        *,
        de: Optional[datetime] = None,
        ate: Optional[datetime] = None,
        unidade: str = "",
        codigo_exame: str = "",
    ) -> List[Dict[str, Any]]:
        """Lista vagas ativas que se sobrepõem ao intervalo e aos filtros."""
        stmt = select(AgendaSlot).where(AgendaSlot.deleted_at.is_(None))
        if de is not None:
            stmt = stmt.where(AgendaSlot.fim >= para_utc_naive(de))
        if ate is not None:
            stmt = stmt.where(AgendaSlot.inicio <= para_utc_naive(ate))
        if unidade:
            stmt = stmt.where(AgendaSlot.unidade.ilike(f"%{unidade}%"))
        if codigo_exame:
            stmt = stmt.where(AgendaSlot.codigo_exame == codigo_exame)
        stmt = stmt.order_by(AgendaSlot.inicio, AgendaSlot.id)
        slots = (await self.db.scalars(stmt)).all()
        ocupadas = await self._ocupadas_por_slot([slot.id for slot in slots])
        return [slot_para_dto(slot, ocupadas.get(slot.id, 0)) for slot in slots]

    async def obter(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Retorna uma vaga ativa pelo id ou None."""
        slot = await self.db.scalar(
            select(AgendaSlot).where(AgendaSlot.id == slot_id, AgendaSlot.deleted_at.is_(None))
        )
        if not slot:
            return None
        ocupadas = await self._ocupadas_por_slot([slot.id])
        return slot_para_dto(slot, ocupadas.get(slot.id, 0))

    async def criar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma vaga local sem fazer commit (o controller audita e confirma)."""
        agora = datetime.now(timezone.utc)
        slot = AgendaSlot(
            id=str(uuid.uuid4()),
            unidade=str(dados["unidade"]),
            codigo_exame=str(dados.get("codigoExame") or ""),
            nome_exame=str(dados.get("nomeExame") or ""),
            inicio=para_utc_naive(parse_datetime(dados["inicio"])),
            fim=para_utc_naive(parse_datetime(dados["fim"])),
            capacidade=int(dados["capacidade"]),
            situacao=str(dados.get("situacao") or "DISPONIVEL").upper(),
            criado_em=agora,
            atualizado_em=agora,
        )
        self.db.add(slot)
        await self.db.flush()
        return slot_para_dto(slot, 0)

    async def atualizar(self, slot_id: str, dados: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza campos enviados de uma vaga ativa sem fazer commit."""
        slot = await self.db.scalar(
            select(AgendaSlot).where(AgendaSlot.id == slot_id, AgendaSlot.deleted_at.is_(None))
        )
        if not slot:
            return None
        campos = {
            "unidade": "unidade",
            "codigoExame": "codigo_exame",
            "nomeExame": "nome_exame",
            "situacao": "situacao",
        }
        for chave, atributo in campos.items():
            if dados.get(chave) is not None:
                setattr(slot, atributo, str(dados[chave]).upper() if chave == "situacao" else str(dados[chave]))
        if dados.get("inicio") is not None:
            slot.inicio = para_utc_naive(parse_datetime(dados["inicio"]))
        if dados.get("fim") is not None:
            slot.fim = para_utc_naive(parse_datetime(dados["fim"]))
        if dados.get("capacidade") is not None:
            slot.capacidade = int(dados["capacidade"])
        slot.atualizado_em = datetime.now(timezone.utc)
        await self.db.flush()
        ocupadas = await self._ocupadas_por_slot([slot.id])
        return slot_para_dto(slot, ocupadas.get(slot.id, 0))


class AghuSlotProvider(SlotProviderInterface):
    """Ponto de extensão reservado: vagas reais do AGHU ainda não habilitadas."""

    async def listar(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Avisa que a integração real com o AGHU não foi implementada."""
        raise NotImplementedError("Vagas do AGHU ainda não implementadas: use a agenda local.")

    async def obter(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Avisa que a integração real com o AGHU não foi implementada."""
        raise NotImplementedError("Vagas do AGHU ainda não implementadas: use a agenda local.")

    async def criar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Vagas do AGHU não podem ser criadas pelo sistema local."""
        raise NotImplementedError("Vagas do AGHU ainda não implementadas: use a agenda local.")

    async def atualizar(self, slot_id: str, dados: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Vagas do AGHU não podem ser alteradas pelo sistema local."""
        raise NotImplementedError("Vagas do AGHU ainda não implementadas: use a agenda local.")
