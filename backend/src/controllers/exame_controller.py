from datetime import datetime, timezone, date
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.exame import Exame
from ..models.paciente_local import PacienteLocal
from ..models.frasco import Frasco
from ..models.cassete import Cassete
from ..models.macroscopia import Macroscopia
from ..models.bloco_parafina import BlocoParafina
from ..models.lamina import Lamina
from ..models.lote_processamento import LoteProcessamento
from ..models.historico_movimentacao import HistoricoMovimentacao
from ..providers.implementations.exame_repository import ExameRepository

_SLA_DIAS = 20


def _idade(nascimento: date | None) -> int:
    if not nascimento:
        return 0
    hoje = datetime.now(timezone.utc).date()
    return max(
        0,
        hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day)),
    )


def _dias_desde(data: datetime) -> int:
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = agora - data.replace(tzinfo=None) if data else None
    return delta.days if delta else 0


async def listar_exames(session: AsyncSession) -> List[Exame]:
    return await ExameRepository(session).listar()


async def obter_exame(session: AsyncSession, id_exame: str) -> Exame:
    exame = await ExameRepository(session).obter(id_exame)
    if exame is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exame não encontrado."
        )
    return exame


async def obter_detalhe(session: AsyncSession, id_exame: str) -> dict:
    """
    Visão unificada do caso: agrega exame + paciente + frasco + macroscopia +
    cassetes + blocos + lâminas numa estrutura pronta para o modal do frontend.
    """
    exame = await ExameRepository(session).obter(id_exame)
    if exame is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exame não encontrado.")

    paciente = await session.get(PacienteLocal, exame.id_paciente)

    frascos = list(
        (await session.execute(select(Frasco).where(Frasco.id_exame == exame.id))).scalars().all()
    )
    frasco = frascos[0] if frascos else None
    frasco_ids = [f.id for f in frascos]

    macro = None
    cassetes: list[Cassete] = []
    if frasco_ids:
        macro = (
            await session.execute(select(Macroscopia).where(Macroscopia.id_frasco.in_(frasco_ids)))
        ).scalars().first()
        cassetes = list(
            (
                await session.execute(
                    select(Cassete)
                    .where(Cassete.id_frasco.in_(frasco_ids))
                    .order_by(Cassete.letra_fragmento.asc())
                )
            ).scalars().all()
        )

    cassete_ids = [c.id for c in cassetes]
    por_cassete = {c.id: c.letra_fragmento for c in cassetes}

    blocos: list[BlocoParafina] = []
    if cassete_ids:
        blocos = list(
            (
                await session.execute(
                    select(BlocoParafina)
                    .where(BlocoParafina.id_cassete.in_(cassete_ids))
                    .order_by(BlocoParafina.codigo_bloco.asc())
                )
            ).scalars().all()
        )

    bloco_ids = [b.id for b in blocos]
    por_bloco = {b.id: por_cassete.get(b.id_cassete, b.codigo_bloco) for b in blocos}

    laminas: list[Lamina] = []
    lote = None
    if bloco_ids:
        laminas = list(
            (
                await session.execute(
                    select(Lamina)
                    .where(Lamina.id_bloco.in_(bloco_ids))
                    .order_by(Lamina.codigo_lamina.asc())
                )
            ).scalars().all()
        )
        lote = await session.get(LoteProcessamento, blocos[0].id_lote)

    # --- montagem da estrutura (snake_case; frontend mapeia p/ ExamCaseDetail) ---
    aghu = {
        "nome_paciente": paciente.nome if paciente else "—",
        "prontuario": (paciente.cns or paciente.cpf) if paciente else "—",
        "idade": _idade(paciente.data_nascimento) if paciente else 0,
        "origem": paciente.origem if paciente else "—",
        "tipo_material": exame.tipo_peca or "",
        "tipo_exame": exame.tipo_exame,
        "numero_solicitacao_aghu": exame.numero_exame_aghu or "—",
        "procedimento_sus": "—",
        "indicacao_clinica": (f"Topografia: {exame.topografia}" if exame.topografia else "—"),
    }

    recepcao = None
    if frasco:
        recepcao = {
            "data_entrada": exame.data_recebimento,
            "quantidade_frascos": len(frascos),
            "descricao_fisica": frasco.descricao_macroscopia or exame.tipo_peca or "—",
            "frascos_ids": [f.codigo_interno for f in frascos],
            "responsavel": exame.criado_por or "—",
        }

    macroscopia = None
    if macro:
        macroscopia = {
            "data_macro": macro.data_realizacao,
            "responsavel": macro.responsavel or "—",
            "descricao": macro.descricao,
            "sobra_material": False,
            "cassetes": [
                {"id": c.letra_fragmento, "estrutura": exame.tipo_peca or "—", "coloracao": c.coloracao_padrao or "HE"}
                for c in cassetes
            ],
        }

    processamento = None
    if blocos:
        processamento = {
            "blocos": [
                {
                    "id": por_bloco.get(b.id, b.codigo_bloco),
                    "cassete_id": por_cassete.get(b.id_cassete, ""),
                    "responsavel": b.criado_por or (lote.responsavel if lote else "—"),
                    "data_inclusao": b.data_criacao,
                }
                for b in blocos
            ],
            "laminas": [
                {"id": lm.codigo_lamina, "bloco_id": por_bloco.get(lm.id_bloco, ""), "coloracao": lm.coloracao}
                for lm in laminas
            ],
            "data_liberacao": (lote.data_fim if lote else (blocos[0].data_criacao if blocos else None)),
            "responsavel": (lote.responsavel if lote else "—"),
        }

    microscopia = None
    if exame.status in ("Em Microscopia", "Revisão Pendente", "Liberado") and laminas:
        # Laudo/observação mais recente registrada na etapa de microscopia (histórico).
        hist = (
            await session.execute(
                select(HistoricoMovimentacao)
                .where(
                    HistoricoMovimentacao.id_exame == exame.id,
                    HistoricoMovimentacao.etapa == "Microscopia",
                    HistoricoMovimentacao.observacoes.isnot(None),
                )
                .order_by(HistoricoMovimentacao.timestamp_transicao.desc())
            )
        ).scalars().first()
        microscopia = {
            "data_recebimento": laminas[0].data_criacao,
            "data_liberacao_laudo": exame.data_conclusao,
            "responsavel": (hist.usuario_responsavel if hist else "—"),
            "laudo": (hist.observacoes if hist else None),
        }

    return {
        "codigo_local": exame.numero_solicitacao,
        "etapa_atual": exame.status,
        "urgente": False,
        "aghu": aghu,
        "recepcao": recepcao,
        "macroscopia": macroscopia,
        "processamento": processamento,
        "microscopia": microscopia,
    }


async def listar_dashboard(
    session: AsyncSession,
    etapa: str | None = None,
    codigo_aghu: str | None = None,
    codigo_interno: str | None = None,
    nome_paciente: str | None = None,
) -> list[dict]:
    """
    Retorna exames com nome do paciente e flag de SLA para o dashboard do frontend,
    aplicando filtros por etapa, código AGHU, código interno e nome do paciente.
    """
    stmt = (
        select(
            Exame.id,
            Exame.numero_solicitacao,
            Exame.numero_exame_aghu,
            Exame.status,
            Exame.data_recebimento,
            PacienteLocal.nome.label("nome_paciente"),
        )
        .join(PacienteLocal, Exame.id_paciente == PacienteLocal.id)
    )

    if etapa:
        stmt = stmt.where(Exame.status == etapa)
    if codigo_aghu:
        stmt = stmt.where(Exame.numero_exame_aghu.ilike(f"%{codigo_aghu.strip()}%"))
    if codigo_interno:
        stmt = stmt.where(Exame.numero_solicitacao.ilike(f"%{codigo_interno.strip()}%"))
    if nome_paciente:
        stmt = stmt.where(PacienteLocal.nome.ilike(f"%{nome_paciente.strip()}%"))

    stmt = stmt.order_by(Exame.data_recebimento.desc())
    rows = (await session.execute(stmt)).all()

    result = []
    for row in rows:
        dias = _dias_desde(row.data_recebimento) if row.data_recebimento else 0
        result.append(
            {
                "id": row.id,
                "solicitacao": row.numero_solicitacao,
                "codigo_aghu": row.numero_exame_aghu,
                "paciente": row.nome_paciente or "",
                "etapa": row.status,
                "data_entrada": row.data_recebimento,
                "atrasado": dias >= _SLA_DIAS,
            }
        )
    return result

