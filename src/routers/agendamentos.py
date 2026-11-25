"""
Routers da Gestão de Agendamentos (v0.3.0)
==========================================
Todos os roteadores declaram JWT no nível do `APIRouter` (default-private) e
reforçam RBAC no backend. O grupo `GLO-SEC-HCPE-SETISD` do usuário mock
`admin/admin` tem acesso equivalente a ADMIN_TI em todas as rotas.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..controllers import agendamento_controller as controller
from ..dependencies import get_slot_provider
from ..helpers.string_helper import parse_datetime
from ..providers.interfaces.slot_provider_interface import SlotProviderInterface
from ..resources.database import get_app_db_session

# Perfis locais do framework + grupos corporativos mapeados para ADMIN_TI.
GRUPOS_LEITURA = {
    "OPERADOR",
    "CHEFIA",
    "AREA_GESTORA",
    "ADMIN_TI",
    "COORDENACAO",
    "GLO-SEC-HCPE-SETISD",
}
GRUPOS_ESCRITA = {
    "OPERADOR",
    "CHEFIA",
    "AREA_GESTORA",
    "ADMIN_TI",
    "GLO-SEC-HCPE-SETISD",
}
GRUPOS_ADMIN_AGENDA = {"AREA_GESTORA", "ADMIN_TI", "GLO-SEC-HCPE-SETISD"}


def _grupos(current_user: dict) -> set[str]:
    """Lê perfis/grupos do token, aceitando `groups`, `perfis` e `profiles`."""
    valores = set(current_user.get("groups") or [])
    valores.update(current_user.get("perfis") or [])
    valores.update(current_user.get("profiles") or [])
    return {str(valor) for valor in valores}


async def verificar_leitura(current_user: dict = Depends(auth_handler.decode_token)) -> dict:
    """Permite consultas a operação, chefia, gestão, TI, coordenação e admin."""
    if not (_grupos(current_user) & GRUPOS_LEITURA):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil sem permissão para consultar agendamentos.",
        )
    return current_user


async def verificar_escrita(current_user: dict = Depends(auth_handler.decode_token)) -> dict:
    """Permite mutações somente a operação, chefia, gestão, TI e admin."""
    if not (_grupos(current_user) & GRUPOS_ESCRITA):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil sem permissão para alterar agendamentos.",
        )
    return current_user


async def verificar_admin_agenda(
    current_user: dict = Depends(auth_handler.decode_token),
) -> dict:
    """Restringe a gestão de vagas à Área Gestora, TI e admin do framework."""
    if not (_grupos(current_user) & GRUPOS_ADMIN_AGENDA):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil sem permissão para administrar a agenda de vagas.",
        )
    return current_user


def _ip(request: Request) -> Optional[str]:
    """Obtém o IP de origem para a auditoria."""
    return request.client.host if request.client else None


router = APIRouter(
    prefix="/api/agendamentos",
    tags=["Agendamentos"],
    dependencies=[Depends(auth_handler.decode_token)],
)
solicitacoes_router = APIRouter(
    prefix="/api/solicitacoes",
    tags=["Agendamentos — Solicitações"],
    dependencies=[Depends(auth_handler.decode_token)],
)
admin_router = APIRouter(
    prefix="/api/admin/agenda",
    tags=["Admin — Agenda"],
    dependencies=[Depends(auth_handler.decode_token)],
)


class SlotPayload(BaseModel):
    """Corpo de criação/edição de vaga local (camelCase do contrato)."""

    unidade: Optional[str] = Field(default=None, validation_alias=AliasChoices("unidade", "unidadeSolicitante"))
    codigoExame: Optional[str] = Field(default=None, validation_alias=AliasChoices("codigoExame", "codigo_exame"))
    nomeExame: Optional[str] = Field(default=None, validation_alias=AliasChoices("nomeExame", "nome_exame"))
    inicio: Optional[str] = None
    fim: Optional[str] = None
    capacidade: Optional[int] = None
    situacao: Optional[str] = None

    def como_dict(self) -> Dict[str, Any]:
        """Remove campos não informados antes da validação no controller."""
        return {chave: valor for chave, valor in self.model_dump(exclude_none=True).items()}


class AgendarPayload(BaseModel):
    """Corpo de efetivação de agendamento."""

    solicitacaoId: str = Field(min_length=1)
    slotId: str = Field(min_length=1)
    autor: str = Field(min_length=1)


class RemarcarPayload(BaseModel):
    """Corpo de remarcação; justificativa é obrigatória no controller."""

    slotId: str = Field(min_length=1)
    justificativa: Optional[str] = None
    autor: str = Field(min_length=1)


class CancelarPayload(BaseModel):
    """Corpo de cancelamento; justificativa é obrigatória no controller."""

    justificativa: Optional[str] = None
    autor: str = Field(min_length=1)


class ValidacaoPayload(BaseModel):
    """Justificativas opcionais das divergências tratadas."""

    justificativas: Optional[Dict[str, str]] = None


class ContatoPayload(BaseModel):
    """Registro do retorno do contato com o paciente."""

    canal: str = Field(min_length=1)
    resultado: str = Field(min_length=1)
    observacao: Optional[str] = None
    operador: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Calendário, consultas e sugestões
# ---------------------------------------------------------------------------

@router.get("/calendario")
async def calendario_agendamentos(
    de: Optional[str] = Query(default=None),
    ate: Optional[str] = Query(default=None),
    unidade: str = Query(default=""),
    codigoExame: str = Query(default=""),
    pacienteChave: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_leitura),
):
    """Retorna slots e agendamentos; ocupadas ignora o filtro de paciente."""
    return await controller.listar_calendario(
        db,
        provider,
        de=de,
        ate=ate,
        unidade=unidade,
        codigo_exame=codigoExame,
        paciente_chave=pacienteChave,
    )


@router.get("/pacientes/buscar")
async def buscar_pacientes_agendamento(
    q: str = Query(default="", min_length=1),
    db: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(verificar_leitura),
):
    """Busca por prontuário, nome ou protocolo, sem CPF/CNS nem endereço."""
    return await controller.buscar_pacientes(db, q)


@router.get("/paciente/{paciente_chave}")
async def agendamentos_do_paciente(
    paciente_chave: str,
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_leitura),
):
    """Lista todos os status do paciente, ordenados por dataHora desc."""
    return await controller.listar_por_paciente(db, provider, paciente_chave)


@router.get("/sugestoes/{solicitacao_id}")
async def sugestoes_de_agendamento(
    solicitacao_id: str,
    limite: Optional[int] = Query(default=None, ge=1, le=20),
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_leitura),
):
    """Sugere vagas ordenadas por score; distância nunca supera prioridade."""
    return await controller.listar_sugestoes(db, provider, solicitacao_id, limite=limite)


# ---------------------------------------------------------------------------
# Mutções de agendamento
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
async def criar_agendamento(
    payload: AgendarPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_escrita),
):
    """Efetiva o agendamento após conferência, aceite e checagem de vagas."""
    return await controller.criar_agendamento(
        db,
        provider,
        solicitacao_id=payload.solicitacaoId,
        slot_id=payload.slotId,
        autor=payload.autor,
        ip=_ip(request),
    )


@router.post("/{agendamento_id}/remarcar")
async def remarcar_agendamento(
    agendamento_id: str,
    payload: RemarcarPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_escrita),
):
    """Troca a vaga, devolvendo a anterior na mesma transação."""
    return await controller.remarcar_agendamento(
        db,
        provider,
        agendamento_id=agendamento_id,
        slot_id=payload.slotId,
        justificativa=payload.justificativa,
        autor=payload.autor,
        ip=_ip(request),
    )


@router.post("/{agendamento_id}/cancelar")
async def cancelar_agendamento(
    agendamento_id: str,
    payload: CancelarPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_escrita),
):
    """Cancela com justificativa e libera a vaga na mesma transação."""
    return await controller.cancelar_agendamento(
        db,
        provider,
        agendamento_id=agendamento_id,
        justificativa=payload.justificativa,
        autor=payload.autor,
        ip=_ip(request),
    )


# ---------------------------------------------------------------------------
# Pré-condições da solicitação
# ---------------------------------------------------------------------------

@solicitacoes_router.post("/{solicitacao_id}/validacao")
async def validar_solicitacao(
    solicitacao_id: str,
    payload: ValidacaoPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(verificar_escrita),
):
    """Trata divergências e prepara a solicitação para contato (RN-04)."""
    return await controller.validar_divergencias(
        db,
        solicitacao_id=solicitacao_id,
        justificativas=payload.justificativas,
        autor=str(current_user.get("username") or "operador"),
        ip=_ip(request),
    )


@solicitacoes_router.post("/{solicitacao_id}/contatos", status_code=status.HTTP_201_CREATED)
async def registrar_contato_paciente(
    solicitacao_id: str,
    payload: ContatoPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(verificar_escrita),
):
    """Registra aceite/recusa/sem resposta para evitar contatos duplicados."""
    return await controller.registrar_contato(
        db,
        solicitacao_id=solicitacao_id,
        canal=payload.canal,
        resultado=payload.resultado,
        observacao=payload.observacao,
        operador=payload.operador,
        ip=_ip(request),
    )


# ---------------------------------------------------------------------------
# Administração local de vagas
# ---------------------------------------------------------------------------

@admin_router.get("/slots")
async def listar_slots_admin(
    de: Optional[str] = Query(default=None),
    ate: Optional[str] = Query(default=None),
    unidade: str = Query(default=""),
    codigoExame: str = Query(default=""),
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_admin_agenda),
):
    """Lista vagas locais para gestão administrativa."""
    agora = datetime.now(timezone.utc)
    inicio_padrao = agora - timedelta(days=1)
    inicio = parse_datetime(de, inicio_padrao) if de else inicio_padrao
    fim_padrao = inicio + timedelta(days=365)
    fim = parse_datetime(ate, fim_padrao) if ate else fim_padrao
    return await provider.listar(
        de=inicio, ate=fim, unidade=unidade, codigo_exame=codigoExame
    )


@admin_router.post("/slots", status_code=status.HTTP_201_CREATED)
async def criar_slot_admin(
    payload: SlotPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_admin_agenda),
):
    """Cria uma vaga local e registra auditoria CONFIGURACAO."""
    return await controller.criar_slot(
        db,
        provider,
        dados=payload.como_dict(),
        autor=str(current_user.get("username") or "admin"),
        ip=_ip(request),
    )


@admin_router.patch("/slots/{slot_id}")
async def atualizar_slot_admin(
    slot_id: str,
    payload: SlotPayload,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
    provider: SlotProviderInterface = Depends(get_slot_provider),
    current_user: dict = Depends(verificar_admin_agenda),
):
    """Atualiza capacidade/situação/horário de uma vaga local."""
    return await controller.atualizar_slot(
        db,
        provider,
        slot_id=slot_id,
        dados=payload.como_dict(),
        autor=str(current_user.get("username") or "admin"),
        ip=_ip(request),
    )
