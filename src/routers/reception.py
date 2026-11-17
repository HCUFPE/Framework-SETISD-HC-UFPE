"""Endpoints FastAPI para as operações já existentes de Recepção."""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..auth.authorization import Permissao, exigir_permissao
from ..controllers.reception_controller import ReceptionController
from ..dependencies import get_reception_provider
from ..models.audit_log import AuditLog
from ..providers.interfaces.reception_provider_interface import ReceptionProviderInterface
from ..resources.database import get_app_db_session
from ..schemas.reception import (
    AcionarPlantaoInput,
    AtualizarSituacaoDevolucaoInput,
    CancelarCasoInput,
    ConfirmarEntradaInput,
    RegistrarNaoConformidadeInput,
)


router = APIRouter(
    prefix="/api/ap",
    tags=["Recepção"],
    dependencies=[Depends(auth_handler.decode_token)],
)


def _controller(provider: ReceptionProviderInterface, session: AsyncSession) -> ReceptionController:
    """Monta controller sobre a mesma sessão usada por provider e auditoria."""
    return ReceptionController(provider, session)


def _ip_origem(request: Request) -> str | None:
    """Obtém IP do peer HTTP sem confiar em cabeçalhos enviados pelo cliente."""
    return request.client.host if request.client else None


async def _negar_vinculo_ihq_nao_implementado(
    _usuario: dict[str, Any] = Depends(auth_handler.decode_token),
) -> None:
    """Recusa vínculo manual enquanto o mecanismo automático ainda é definido."""
    raise HTTPException(status_code=501, detail="A associação automática de solicitações IHQ ainda não está implementada.")


async def _conflito_integridade(session: AsyncSession, erro: IntegrityError) -> None:
    """Converte conflitos de unicidade/concorrência em erro de domínio previsível."""
    await session.rollback()
    raise HTTPException(status_code=409, detail="A solicitação ou o registro já foi alterado por outra operação.") from erro


@router.get("/solicitacoes/pendentes")
async def listar_solicitacoes_pendentes(
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> list[dict[str, Any]]:
    """Lista solicitações locais aguardando recebimento."""
    return await _controller(provider, session).listar_pendentes()


@router.get("/solicitacoes/pendentes/contagem")
async def contar_solicitacoes_pendentes(
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> int:
    """Retorna a contagem de solicitações pendentes para o menu."""
    return await _controller(provider, session).contar_pendentes()


@router.get("/solicitacoes/{codigo}")
async def ler_solicitacao(
    codigo: str,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Classifica uma solicitação para a Recepção."""
    return await _controller(provider, session).ler_solicitacao(codigo)


@router.get("/casos")
async def listar_casos(
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> list[dict[str, Any]]:
    """Lista casos persistidos."""
    return await _controller(provider, session).listar_casos()


@router.get("/casos/busca")
async def buscar_casos(
    termo: str = Query(default=""),
    limite: int = Query(default=15, ge=0, le=100),
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Busca casos pelo número, prontuário ou nome do paciente."""
    return await _controller(provider, session).buscar_casos(termo, limite)


@router.get("/casos/elegiveis-ihq")
async def buscar_casos_elegiveis_ihq(
    termo: str = Query(default=""),
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> list[dict[str, Any]]:
    """Pesquisa os casos existentes usados pela tela de vínculo IHQ."""
    return await _controller(provider, session).buscar_elegiveis_ihq(termo)


@router.get("/casos/{numero:path}")
async def obter_caso(
    numero: str,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Consulta detalhe por número interno, inclusive com barra de ano."""
    caso = await _controller(provider, session).obter_caso(numero)
    if caso is None:
        raise HTTPException(status_code=404, detail=f"Caso {numero} não encontrado.")
    return caso


@router.post("/recebimentos", status_code=status.HTTP_201_CREATED)
async def confirmar_recebimento(
    entrada: ConfirmarEntradaInput,
    request: Request,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.RECEPCAO_RECEBER)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Confirma recebimento principal sob permissão específica."""
    try:
        return await _controller(provider, session).confirmar_entrada(
            entrada.model_dump(by_alias=True), usuario, _ip_origem(request)
        )
    except IntegrityError as erro:
        await _conflito_integridade(session, erro)


@router.post("/recebimentos/ihq", dependencies=[Depends(_negar_vinculo_ihq_nao_implementado)])
async def vincular_ihq_pendente() -> None:
    """Vínculo IHQ permanece fechado até a permissão ser validada por SAP/HC."""


@router.post("/casos/cancelamento")
async def cancelar_caso(
    entrada: CancelarCasoInput,
    request: Request,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.CASOS_CANCELAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Cancela um caso ativo; autoria é derivada do token."""
    try:
        return await _controller(provider, session).cancelar_caso(
            entrada.numero_interno, entrada.motivo, usuario, _ip_origem(request)
        )
    except IntegrityError as erro:
        await _conflito_integridade(session, erro)


@router.post("/casos/acionamentos-plantao")
async def acionar_plantao(
    entrada: AcionarPlantaoInput,
    request: Request,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.RECEPCAO_ACIONAR_PLANTAO)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Registra acionamento de plantão apenas uma vez para congelação."""
    try:
        return await _controller(provider, session).acionar_plantao(
            entrada.numero_interno, usuario, _ip_origem(request)
        )
    except IntegrityError as erro:
        await _conflito_integridade(session, erro)


@router.post("/nao-conformidades", status_code=status.HTTP_201_CREATED)
async def registrar_nao_conformidade(
    entrada: RegistrarNaoConformidadeInput,
    request: Request,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Registra não conformidade e a devolução associada."""
    try:
        return await _controller(provider, session).registrar_nao_conformidade(
            entrada.model_dump(by_alias=True), usuario, _ip_origem(request)
        )
    except IntegrityError as erro:
        await _conflito_integridade(session, erro)


@router.get("/devolucoes")
async def listar_devolucoes(
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.DEVOLUCOES_CONSULTAR)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> list[dict[str, Any]]:
    """Lista rejeições e devoluções para Recepção e Coordenação/Administrador."""
    return await _controller(provider, session).listar_devolucoes()


@router.patch("/devolucoes/{devolucao_id}/situacao")
async def atualizar_situacao_devolucao(
    devolucao_id: int,
    entrada: AtualizarSituacaoDevolucaoInput,
    request: Request,
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.DEVOLUCOES_ALTERAR_SITUACAO)),
    provider: ReceptionProviderInterface = Depends(get_reception_provider),
    session: AsyncSession = Depends(get_app_db_session),
) -> dict[str, Any]:
    """Atualiza situação para Recepcionista SAP ou Coordenação/Administrador."""
    try:
        return await _controller(provider, session).atualizar_situacao_devolucao(
            devolucao_id, entrada.situacao, usuario, _ip_origem(request)
        )
    except IntegrityError as erro:
        await _conflito_integridade(session, erro)


@router.get("/auditoria")
async def listar_auditoria(
    usuario: dict[str, Any] = Depends(exigir_permissao(Permissao.AUDITORIA_CONSULTAR)),
    session: AsyncSession = Depends(get_app_db_session),
) -> list[dict[str, Any]]:
    """Consulta trilha existente sem permitir alteração pela API AP."""
    resultado = await session.execute(
        select(AuditLog)
        .where(or_(
            AuditLog.recurso.like("caso_ap:%"),
            AuditLog.recurso.like("devolucao:%"),
            AuditLog.recurso.like("exame_ihq:%"),
        ))
        .order_by(AuditLog.created_at.desc())
    )
    eventos = []
    for registro in resultado.scalars().all():
        try:
            anteriores = json.loads(registro.dados_anteriores) if registro.dados_anteriores else None
            novos = json.loads(registro.dados_novos) if registro.dados_novos else None
        except json.JSONDecodeError:
            anteriores, novos = None, None
        eventos.append({
            "id": registro.id,
            "usuario": {"login": registro.usuario, "nome": registro.usuario},
            "categoria": registro.categoria,
            "acao": registro.acao,
            "recurso": registro.recurso,
            "dadosAnteriores": anteriores,
            "dadosNovos": novos,
            "ipOrigem": registro.ip_origem,
            "ocorridoEm": registro.created_at.isoformat(),
        })
    return eventos
