"""
Processamento Técnico: ciclo de processamento de tecidos (tambor/estufa),
geração de blocos de parafina e lâminas histológicas.

Fluxo da etapa:
  Cassete (Aguardando Processamento)
    → [iniciar lote]  → Em Processamento
    → [concluir lote] → Processamento Completo + BlocoParafina (Aguardando Corte)
    → [gerar lâminas] → BlocoParafina (Aguardando Microscopia) + N Laminas (Aguardando Leitura)
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.identificacao import gerar_qr_code
from ..models.bloco_parafina import BlocoParafina
from ..models.cassete import Cassete
from ..models.lamina import Lamina
from ..models.lote_processamento import LoteProcessamento
from ..providers.implementations.bloco_repository import BlocoRepository
from ..providers.implementations.cassete_repository import CasseteRepository
from ..providers.implementations.exame_repository import ExameRepository
from ..providers.implementations.frasco_repository import FrascoRepository
from ..providers.implementations.lamina_repository import LaminaRepository
from ..providers.implementations.lote_repository import LoteRepository
from ..schemas.bloco import GerarLaminasRequest
from ..schemas.processamento import IniciarLoteRequest, ConcluirLoteRequest
from ..services.maquina_estados import (
    Etapa,
    StatusBloco,
    StatusCassete,
    StatusExame,
    registrar_historico,
    transicionar,
)


async def listar_pendencias(session: AsyncSession) -> List[dict]:
    """Fila de cassetes aguardando entrada no lote de processamento."""
    cassete_repo = CasseteRepository(session)
    return await cassete_repo.listar_pendencias_processamento()


async def iniciar_lote(
    session: AsyncSession,
    dados: IniciarLoteRequest,
    usuario: Optional[str],
    ip: Optional[str],
) -> dict:
    """
    Inicia um lote de processamento: cria o LoteProcessamento e move todos os
    cassetes informados para 'Em Processamento'. Tudo numa transação.
    """
    cassete_repo = CasseteRepository(session)
    lote_repo = LoteRepository(session)

    # Verifica e coleta os cassetes
    cassetes: List[Cassete] = []
    for cid in dados.cassete_ids:
        cassete = await cassete_repo.obter(cid)
        if cassete is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cassete {cid} não encontrado.",
            )
        if cassete.status != StatusCassete.AGUARDANDO_PROCESSAMENTO:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cassete {cid} não está 'Aguardando Processamento'. "
                    f"Status atual: '{cassete.status}'."
                ),
            )
        cassetes.append(cassete)

    # Cria o lote
    lote = LoteProcessamento(
        id=str(uuid.uuid4()),
        responsavel=usuario or dados.responsavel,
        observacoes=dados.observacoes,
    )
    lote_repo.adicionar(lote)

    # Associa cassetes e transiciona
    for cassete in cassetes:
        cassete.id_lote_processamento = lote.id
        transicionar(
            session,
            cassete,
            StatusCassete.EM_PROCESSAMENTO,
            etapa=Etapa.PROCESSAMENTO,
            usuario=usuario,
            ip=ip,
            observacoes=f"Incluído no lote {lote.id[:8]}",
        )

    await session.commit()
    await session.refresh(lote)
    return {"lote": lote, "cassetes": cassetes}


async def concluir_lote(
    session: AsyncSession,
    id_lote: str,
    dados: ConcluirLoteRequest,
    usuario: Optional[str],
    ip: Optional[str],
) -> dict:
    """
    Conclui o lote: todos os cassetes associados vão para 'Processamento Completo'
    e um BlocoParafina é gerado para cada um. Avança o exame para
    'Aguardando Microscopia' quando todos os cassetes do exame estiverem prontos.
    """
    lote_repo = LoteRepository(session)
    cassete_repo = CasseteRepository(session)
    bloco_repo = BlocoRepository(session)
    frasco_repo = FrascoRepository(session)
    exame_repo = ExameRepository(session)

    lote = await lote_repo.obter(id_lote)
    if lote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado."
        )
    if lote.status != "Em Andamento":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lote já está '{lote.status}'.",
        )

    cassetes = await cassete_repo.listar_por_lote(id_lote)
    if not cassetes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nenhum cassete associado a este lote.",
        )

    blocos: List[BlocoParafina] = []
    exames_atualizados: set = set()

    for cassete in cassetes:
        if cassete.status != StatusCassete.EM_PROCESSAMENTO:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cassete {cassete.id} não está 'Em Processamento'. "
                    f"Status atual: '{cassete.status}'."
                ),
            )

        # Busca contexto para gerar codigo_bloco legível
        frasco = await frasco_repo.obter(cassete.id_frasco)
        exame = await exame_repo.obter(frasco.id_exame) if frasco else None
        numero_solicitacao = exame.numero_solicitacao if exame else cassete.id_frasco

        codigo_bloco = f"{numero_solicitacao}-{cassete.letra_fragmento}"
        bloco_id = str(uuid.uuid4())
        qr_bloco = gerar_qr_code("BLOCO", numero_solicitacao, identificador=bloco_id)

        bloco = BlocoParafina(
            id=bloco_id,
            id_cassete=cassete.id,
            id_lote=id_lote,
            codigo_bloco=codigo_bloco,
            qr_code=qr_bloco,
            status=StatusBloco.AGUARDANDO_CORTE,
            criado_por=usuario,
        )
        bloco_repo.adicionar(bloco)

        transicionar(
            session,
            cassete,
            StatusCassete.PROCESSAMENTO_COMPLETO,
            etapa=Etapa.PROCESSAMENTO,
            usuario=usuario,
            ip=ip,
            observacoes=f"Bloco {codigo_bloco} gerado",
        )
        registrar_historico(
            session,
            cassete,
            status_anterior=StatusBloco.AGUARDANDO_CORTE,
            status_novo=StatusBloco.AGUARDANDO_CORTE,
            etapa=Etapa.PROCESSAMENTO,
            usuario=usuario,
            ip=ip,
            observacoes=f"BlocoParafina {codigo_bloco} criado",
        )
        blocos.append(bloco)

        # Marca exame para verificar avanço de status
        if exame:
            exames_atualizados.add(exame.id)

    # Avança exame para Aguardando Microscopia
    for id_exame in exames_atualizados:
        exame = await exame_repo.obter(id_exame)
        if exame and exame.status == StatusExame.EM_PROCESSAMENTO:
            transicionar(
                session,
                exame,
                StatusExame.EM_MICROSCOPIA,
                etapa=Etapa.PROCESSAMENTO,
                usuario=usuario,
                ip=ip,
            )

    # Conclui o lote
    lote.status = "Concluído"
    lote.data_fim = datetime.now(timezone.utc).replace(tzinfo=None)
    if dados.observacoes:
        lote.observacoes = (lote.observacoes or "") + " | " + dados.observacoes

    await session.commit()
    await session.refresh(lote)
    return {"lote": lote, "blocos": blocos}


async def gerar_laminas(
    session: AsyncSession,
    id_bloco: str,
    dados: GerarLaminasRequest,
    usuario: Optional[str],
    ip: Optional[str],
) -> dict:
    """
    Gera N lâminas para um bloco e avança o bloco para 'Aguardando Microscopia'.
    """
    bloco_repo = BlocoRepository(session)
    lamina_repo = LaminaRepository(session)
    cassete_repo = CasseteRepository(session)
    frasco_repo = FrascoRepository(session)
    exame_repo = ExameRepository(session)

    bloco = await bloco_repo.obter(id_bloco)
    if bloco is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bloco não encontrado."
        )
    if bloco.status != StatusBloco.AGUARDANDO_CORTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Bloco precisa estar 'Aguardando Corte' para gerar lâminas. "
                f"Status atual: '{bloco.status}'."
            ),
        )

    # Contexto para QR code e código da lâmina
    cassete = await cassete_repo.obter(bloco.id_cassete)
    frasco = await frasco_repo.obter(cassete.id_frasco) if cassete else None
    exame = await exame_repo.obter(frasco.id_exame) if frasco else None
    numero_solicitacao = exame.numero_solicitacao if exame else bloco.codigo_bloco

    existentes = await lamina_repo.contar_por_bloco(id_bloco)

    laminas: List[Lamina] = []
    etiquetas: List[dict] = []
    for i in range(dados.quantidade):
        numero = existentes + i + 1
        lamina_id = str(uuid.uuid4())
        codigo_lamina = f"{bloco.codigo_bloco}-L{numero}"
        qr_lamina = gerar_qr_code("LAMINA", numero_solicitacao, identificador=lamina_id)

        lamina = Lamina(
            id=lamina_id,
            id_bloco=id_bloco,
            numero_lamina=numero,
            codigo_lamina=codigo_lamina,
            qr_code=qr_lamina,
            coloracao=dados.coloracao,
            criado_por=usuario,
        )
        lamina_repo.adicionar(lamina)
        laminas.append(lamina)
        etiquetas.append(
            {
                "tipo": "LAMINA",
                "numero_solicitacao": numero_solicitacao,
                "codigo": codigo_lamina,
                "qr_code": qr_lamina,
            }
        )

    # Avança bloco
    bloco.status = StatusBloco.AGUARDANDO_MICROSCOPIA
    registrar_historico(
        session,
        cassete,
        status_anterior=StatusBloco.AGUARDANDO_CORTE,
        status_novo=StatusBloco.AGUARDANDO_MICROSCOPIA,
        etapa=Etapa.PROCESSAMENTO,
        usuario=usuario,
        ip=ip,
        observacoes=f"{dados.quantidade} lâmina(s) gerada(s) para bloco {bloco.codigo_bloco}",
    )

    await session.commit()
    await session.refresh(bloco)

    return {
        "bloco_id": bloco.id,
        "codigo_bloco": bloco.codigo_bloco,
        "laminas": laminas,
        "etiquetas": etiquetas,
    }


async def listar_blocos_pendentes(session: AsyncSession) -> List[dict]:
    """Fila de blocos aguardando corte microtômico."""
    return await BlocoRepository(session).listar_pendencias_corte()


async def buscar_bloco(session: AsyncSession, codigo_bloco: Optional[str]) -> List[dict]:
    """Busca manual por código de bloco."""
    if not codigo_bloco:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe codigo_bloco.",
        )
    resultados = await BlocoRepository(session).buscar_detalhe(codigo_bloco)
    if not resultados:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum bloco encontrado."
        )
    return resultados


async def listar_laminas(session: AsyncSession, id_bloco: str) -> List[Lamina]:
    bloco = await BlocoRepository(session).obter(id_bloco)
    if bloco is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bloco não encontrado."
        )
    return await LaminaRepository(session).listar_por_bloco(id_bloco)
