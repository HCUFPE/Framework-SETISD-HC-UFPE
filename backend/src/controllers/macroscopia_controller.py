"""
Macroscopia: identificação do frasco (fila de pendências + busca manual),
início da etapa e registro da macroscopia com geração dos cassetes.
"""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.identificacao import gerar_qr_code, letra_fragmento
from ..models.cassete import Cassete
from ..models.macroscopia import Macroscopia
from ..providers.implementations.cassete_repository import CasseteRepository
from ..providers.implementations.exame_repository import ExameRepository
from ..providers.implementations.frasco_repository import FrascoRepository
from ..providers.implementations.macroscopia_repository import MacroscopiaRepository
from ..schemas.etiqueta import EtiquetaOut
from ..schemas.macroscopia import MacroscopiaCreate
from ..services.maquina_estados import (
    Etapa,
    StatusCassete,
    StatusExame,
    StatusFrasco,
    registrar_historico,
    transicionar,
)


async def listar_pendencias(session: AsyncSession) -> List[dict]:
    """Fila da estação: frascos aguardando macroscopia."""
    return await FrascoRepository(session).listar_pendencias_macroscopia()


async def buscar_frasco(
    session: AsyncSession,
    numero_solicitacao: Optional[str],
    codigo_interno: Optional[str],
) -> List[dict]:
    if not numero_solicitacao and not codigo_interno:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe numero_solicitacao ou codigo_interno.",
        )
    resultados = await FrascoRepository(session).buscar_detalhe(
        numero_solicitacao, codigo_interno
    )
    if not resultados:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum frasco encontrado."
        )
    return resultados


async def iniciar_macroscopia(
    session: AsyncSession,
    id_frasco: str,
    usuario: Optional[str],
    ip: Optional[str],
):
    """
    Move frasco 'Aguardando Macroscopia' → 'Em Macroscopia' e exame
    'Na Recepção' → 'Em Macroscopia'.
    """
    frasco_repo = FrascoRepository(session)
    exame_repo = ExameRepository(session)

    frasco = await frasco_repo.obter(id_frasco)
    if frasco is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Frasco não encontrado."
        )
    exame = await exame_repo.obter(frasco.id_exame)

    transicionar(
        session,
        frasco,
        StatusFrasco.EM_MACROSCOPIA,
        etapa=Etapa.MACROSCOPIA,
        usuario=usuario,
        ip=ip,
    )
    if exame is not None:
        transicionar(
            session,
            exame,
            StatusExame.EM_MACROSCOPIA,
            etapa=Etapa.MACROSCOPIA,
            usuario=usuario,
            ip=ip,
        )

    await session.commit()
    await session.refresh(frasco)
    return frasco


async def registrar_macroscopia(
    session: AsyncSession,
    dados: MacroscopiaCreate,
    usuario: Optional[str],
    ip: Optional[str],
) -> dict:
    """
    Registra a macroscopia, gera N cassetes (A, B, C, ...), conclui o frasco e
    move o exame para 'Em Processamento'. Tudo numa única transação.
    """
    frasco_repo = FrascoRepository(session)
    exame_repo = ExameRepository(session)
    cassete_repo = CasseteRepository(session)
    macro_repo = MacroscopiaRepository(session)

    frasco = await frasco_repo.obter(dados.id_frasco)
    if frasco is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Frasco não encontrado."
        )
    if frasco.status != StatusFrasco.EM_MACROSCOPIA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "O frasco precisa estar 'Em Macroscopia' para registrar. "
                f"Status atual: '{frasco.status}'."
            ),
        )

    exame = await exame_repo.obter(frasco.id_exame)
    numero_solicitacao = exame.numero_solicitacao if exame else ""

    macroscopia = Macroscopia(
        id=str(uuid.uuid4()),
        id_frasco=frasco.id,
        descricao=dados.descricao,
        responsavel=usuario,
        numero_cassetes=dados.numero_cassetes,
    )
    macro_repo.adicionar(macroscopia)

    cassetes: List[Cassete] = []
    etiquetas: List[EtiquetaOut] = []
    for i in range(dados.numero_cassetes):
        letra = letra_fragmento(i)
        cassete_id = str(uuid.uuid4())
        qr_code = gerar_qr_code(
            "CASSETE", numero_solicitacao, identificador=cassete_id
        )
        cassete = Cassete(
            id=cassete_id,
            id_frasco=frasco.id,
            letra_fragmento=letra,
            qr_code=qr_code,
            status=StatusCassete.AGUARDANDO_PROCESSAMENTO,
            criado_por=usuario,
        )
        cassete_repo.adicionar(cassete)
        registrar_historico(
            session,
            cassete,
            status_anterior=None,
            status_novo=StatusCassete.AGUARDANDO_PROCESSAMENTO,
            etapa=Etapa.MACROSCOPIA,
            usuario=usuario,
            ip=ip,
            observacoes=f"Cassete {letra} gerado na macroscopia",
        )
        cassetes.append(cassete)
        etiquetas.append(
            EtiquetaOut(
                tipo="CASSETE",
                numero_solicitacao=numero_solicitacao,
                codigo=letra,
                qr_code=qr_code,
            )
        )

    frasco.descricao_macroscopia = dados.descricao
    frasco.numero_cassetes_gerados = dados.numero_cassetes
    transicionar(
        session,
        frasco,
        StatusFrasco.PROCESSAMENTO_COMPLETO,
        etapa=Etapa.MACROSCOPIA,
        usuario=usuario,
        ip=ip,
        observacoes=f"{dados.numero_cassetes} cassete(s) gerado(s)",
    )
    if exame is not None:
        transicionar(
            session,
            exame,
            StatusExame.EM_PROCESSAMENTO,
            etapa=Etapa.MACROSCOPIA,
            usuario=usuario,
            ip=ip,
        )

    await session.commit()
    await session.refresh(macroscopia)
    await session.refresh(frasco)

    return {
        "macroscopia": macroscopia,
        "frasco": frasco,
        "cassetes": cassetes,
        "etiquetas": etiquetas,
    }
