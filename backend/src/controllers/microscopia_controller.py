"""
Microscopia (Fase 3): fila de laudos, laudo prévio do residente e decisão do
patologista (liberar / revisão interna / pedir complemento).

Persiste as transições de status do exame (que aparecem no dashboard) e registra
o texto do laudo no histórico append-only — nada fica só no frontend.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.exame import Exame
from ..models.paciente_local import PacienteLocal
from ..providers.implementations.exame_repository import ExameRepository
from ..services.maquina_estados import Etapa, StatusExame, transicionar


# ação do frontend -> status de destino do exame
_ACAO_PARA_STATUS = {
    "liberar": StatusExame.LIBERADO,
    "revisao": StatusExame.REVISAO_PENDENTE,
    "complemento": StatusExame.EM_PROCESSAMENTO,
}


async def listar_pendencias(session: AsyncSession) -> List[dict]:
    """Fila da microscopia: exames em análise (Em Microscopia) ou em revisão."""
    stmt = (
        select(
            Exame.id,
            Exame.numero_solicitacao,
            Exame.status,
            Exame.data_recebimento,
            Exame.tipo_exame,
            PacienteLocal.nome.label("paciente_nome"),
        )
        .join(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
        .where(Exame.status.in_([StatusExame.EM_MICROSCOPIA, StatusExame.REVISAO_PENDENTE]))
        .order_by(Exame.data_recebimento.asc())
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows]


async def registrar_laudo(
    session: AsyncSession,
    id_exame: str,
    acao: str,
    responsavel: Optional[str],
    laudo: Optional[str],
    observacoes: Optional[str],
    usuario: Optional[str],
    ip: Optional[str],
) -> dict:
    if acao not in _ACAO_PARA_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ação inválida: '{acao}'. Válidas: {sorted(_ACAO_PARA_STATUS)}.",
        )

    exame = await ExameRepository(session).obter(id_exame)
    if exame is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exame não encontrado.")

    novo_status = _ACAO_PARA_STATUS[acao]
    obs = " | ".join([p for p in [laudo, observacoes] if p]) or None

    # No-op se já está no status de destino (evita 409 em ações repetidas na demo).
    if exame.status != novo_status:
        transicionar(
            session,
            exame,
            novo_status,
            etapa=Etapa.MICROSCOPIA,
            usuario=responsavel or usuario,
            ip=ip,
            observacoes=obs,
        )
        if novo_status == StatusExame.LIBERADO:
            exame.data_conclusao = datetime.now(timezone.utc).replace(tzinfo=None)
        await session.commit()
        await session.refresh(exame)

    return {"exame_id": exame.id, "numero_solicitacao": exame.numero_solicitacao, "status": exame.status}
