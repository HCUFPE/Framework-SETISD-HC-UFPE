"""
Triagem / Recepção: registro de recebimento de peça e encaminhamento para a
macroscopia.
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.identificacao import (
    TIPOS_EXAME_VALIDOS,
    gerar_codigo_interno_frasco,
    gerar_numero_solicitacao,
    gerar_qr_code,
)
from ..models.exame import Exame
from ..models.frasco import Frasco
from ..models.paciente_local import PacienteLocal
from ..providers.implementations.exame_repository import ExameRepository
from ..providers.implementations.frasco_repository import FrascoRepository
from ..providers.implementations.paciente_local_repository import (
    PacienteLocalRepository,
)
from ..schemas.etiqueta import EtiquetaOut
from ..schemas.exame import ExameCreate
from ..services.maquina_estados import (
    Etapa,
    StatusExame,
    StatusFrasco,
    registrar_historico,
    transicionar,
)


async def registrar_recebimento(
    session: AsyncSession,
    dados: ExameCreate,
    usuario: Optional[str],
    ip: Optional[str],
) -> dict:
    """
    Cria (ou reaproveita) o paciente, gera o número de solicitação, cria o
    exame e o frasco com seus identificadores, e registra o histórico — tudo
    numa única transação.
    """
    paciente_repo = PacienteLocalRepository(session)
    exame_repo = ExameRepository(session)
    frasco_repo = FrascoRepository(session)

    p = dados.paciente
    if not p.cpf and not p.cns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe ao menos CPF ou CNS do paciente.",
        )

    tipo_exame = dados.tipo_exame.strip()
    if tipo_exame not in TIPOS_EXAME_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tipo_exame inválido: '{tipo_exame}'. Válidos: {sorted(TIPOS_EXAME_VALIDOS)}.",
        )

    paciente = await paciente_repo.buscar_por_documento(p.cpf, p.cns)
    if paciente is None:
        paciente = PacienteLocal(
            id=str(uuid.uuid4()),
            nome=p.nome,
            cpf=p.cpf,
            cns=p.cns,
            data_nascimento=p.data_nascimento,
            origem=p.origem,
            criado_por=usuario,
        )
        paciente_repo.adicionar(paciente)

    numero_solicitacao, sequencial, ano, semestre = await gerar_numero_solicitacao(
        session, tipo_exame=tipo_exame
    )

    exame = Exame(
        id=str(uuid.uuid4()),
        numero_solicitacao=numero_solicitacao,
        tipo_exame=tipo_exame,
        sequencial=sequencial,
        ano=ano,
        semestre=semestre,
        id_paciente=paciente.id,
        numero_exame_aghu=dados.numero_exame_aghu,
        tipo_peca=dados.tipo_peca,
        topografia=dados.topografia,
        status=StatusExame.NA_RECEPCAO,
        criado_por=usuario,
    )
    exame_repo.adicionar(exame)

    frasco_id = str(uuid.uuid4())
    codigo_interno = gerar_codigo_interno_frasco(numero_solicitacao)
    qr_code = gerar_qr_code("FRASCO", numero_solicitacao, identificador=frasco_id)
    frasco = Frasco(
        id=frasco_id,
        id_exame=exame.id,
        codigo_interno=codigo_interno,
        qr_code=qr_code,
        status=StatusFrasco.NA_RECEPCAO,
        criado_por=usuario,
    )
    frasco_repo.adicionar(frasco)

    registrar_historico(
        session,
        exame,
        status_anterior=None,
        status_novo=StatusExame.NA_RECEPCAO,
        etapa=Etapa.TRIAGEM,
        usuario=usuario,
        ip=ip,
        observacoes="Exame criado na recepção",
    )
    registrar_historico(
        session,
        frasco,
        status_anterior=None,
        status_novo=StatusFrasco.NA_RECEPCAO,
        etapa=Etapa.TRIAGEM,
        usuario=usuario,
        ip=ip,
        observacoes="Frasco recebido na recepção",
    )

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito ao gerar identificadores. Tente novamente.",
        )

    await session.refresh(exame)
    await session.refresh(frasco)

    etiqueta = EtiquetaOut(
        tipo="FRASCO",
        numero_solicitacao=numero_solicitacao,
        codigo=codigo_interno,
        qr_code=qr_code,
    )
    return {"exame": exame, "frasco": frasco, "etiqueta": etiqueta}


async def encaminhar_para_macroscopia(
    session: AsyncSession,
    id_frasco: str,
    usuario: Optional[str],
    ip: Optional[str],
) -> Frasco:
    """
    Sinaliza que o frasco está pronto para a macroscopia, mudando apenas o
    status do Frasco (Na Recepção → Aguardando Macroscopia).
    O Exame permanece 'Na Recepção' até que a macroscopia seja iniciada.
    """
    frasco_repo = FrascoRepository(session)

    frasco = await frasco_repo.obter(id_frasco)
    if frasco is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Frasco não encontrado."
        )

    transicionar(
        session,
        frasco,
        StatusFrasco.AGUARDANDO_MACROSCOPIA,
        etapa=Etapa.TRIAGEM,
        usuario=usuario,
        ip=ip,
        observacoes="Encaminhado para macroscopia",
    )

    await session.commit()
    await session.refresh(frasco)
    return frasco


async def obter_etiqueta_frasco(session: AsyncSession, id_frasco: str) -> EtiquetaOut:
    frasco = await FrascoRepository(session).obter(id_frasco)
    if frasco is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Frasco não encontrado."
        )
    exame = await ExameRepository(session).obter(frasco.id_exame)
    numero = exame.numero_solicitacao if exame else ""
    return EtiquetaOut(
        tipo="FRASCO",
        numero_solicitacao=numero,
        codigo=frasco.codigo_interno,
        qr_code=frasco.qr_code,
    )
