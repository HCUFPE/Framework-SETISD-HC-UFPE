"""
Routers da integração Microsoft Forms → AGHUX
==============================================
O webhook é a única exceção pública documentada: não usa JWT, mas exige HMAC,
timestamp e nonce. Os endpoints administrativos usam o padrão default-private
do framework (`dependencies=[Depends(auth_handler.decode_token)]`).
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import auth_handler
from ..config import settings
from ..controllers.forms_webhook_controller import (
    evento_para_dict,
    listar_eventos,
    processar_resposta,
    receber_evento,
    reprocessar_evento,
)
from ..dependencies import get_aghux_provider, get_forms_provider
from ..helpers.webhook_helper import validar_assinatura_webhook
from ..resources.database import get_app_db_session

GRUPOS_ADMIN = {"GLO-SEC-HCPE-SETISD", "AREA_GESTORA", "ADMIN_TI"}

# Roteador privado: herda autenticação JWT do framework.
router = APIRouter(
    prefix="/api/integracoes",
    tags=["Integrações"],
    dependencies=[Depends(auth_handler.decode_token)],
)

# Roteador público: protegido por HMAC no próprio endpoint.
public_router = APIRouter(prefix="/api/integracoes/forms", tags=["Integrações — Webhook"])


class FormsWebhookPayload(BaseModel):
    """Corpo enviado pelo Power Automate quando chega uma nova resposta."""

    formId: str = Field(min_length=1, validation_alias=AliasChoices("formId", "form_id"))
    responseId: str = Field(min_length=1, validation_alias=AliasChoices("responseId", "response_id"))
    submittedAt: Optional[str] = Field(default=None, validation_alias=AliasChoices("submittedAt", "submitted_at"))
    resposta: Optional[Dict[str, Any]] = None


async def verify_forms_webhook_signature(request: Request) -> bytes:
    """Dependency que valida HMAC/timestamp/nonce e devolve o corpo bruto."""
    corpo = await request.body()
    validar_assinatura_webhook(
        body=corpo,
        timestamp=request.headers.get("X-SAE-Timestamp"),
        nonce=request.headers.get("X-SAE-Nonce"),
        assinatura=request.headers.get("X-SAE-Signature"),
    )
    return corpo


async def verify_integracoes_access(current_user: dict = Depends(auth_handler.decode_token)) -> dict:
    """Restringe os endpoints administrativos à gestão e à TI."""
    grupos = set(current_user.get("groups") or [])
    perfis = set(current_user.get("perfis") or current_user.get("profiles") or [])
    if not (grupos & GRUPOS_ADMIN or perfis & GRUPOS_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil sem permissão para acompanhar integrações.",
        )
    return current_user


async def _processar_em_background(
    response_id: str,
    gerenciador_banco: Any,
    ip_origem: Optional[str],
) -> None:
    """Executa o processamento em sessão própria após responder 202 ao Power Automate."""
    async for db in gerenciador_banco.get_session():
        await processar_resposta(
            db,
            response_id,
            get_forms_provider(),
            get_aghux_provider(),
            ip_origem,
        )


@public_router.post("/webhook")
async def receber_webhook_forms(
    request: Request,
    background_tasks: BackgroundTasks,
    corpo: bytes = Depends(verify_forms_webhook_signature),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Recebe o aviso de nova resposta e agenda a ingestão idempotente."""
    try:
        payload = FormsWebhookPayload.model_validate_json(corpo)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Corpo do webhook inválido: {exc}",
        ) from exc

    if settings.FORMS_FORM_ID and payload.formId != settings.FORMS_FORM_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="formId não corresponde ao formulário configurado no sistema.",
        )

    ip_origem = request.client.host if request.client else None
    evento, duplicado = await receber_evento(
        db,
        form_id=payload.formId,
        response_id=payload.responseId,
        nonce=request.headers["X-SAE-Nonce"],
        resposta=payload.resposta,
        submitted_at=payload.submittedAt,
        ip_origem=ip_origem,
    )
    if duplicado:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "DUPLICADO", "responseId": evento.response_id},
        )

    background_tasks.add_task(
        _processar_em_background,
        evento.response_id,
        request.app.state.app_db,
        ip_origem,
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "ACEITO", "responseId": evento.response_id},
    )


@router.get("/forms/eventos", dependencies=[Depends(verify_integracoes_access)])
async def listar_eventos_forms(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_app_db_session),
):
    """Lista eventos do webhook para a tela administrativa."""
    return await listar_eventos(db, limit)


@router.post("/forms/eventos/{response_id}/reprocessar", dependencies=[Depends(verify_integracoes_access)])
async def reprocessar_evento_forms(
    response_id: str,
    request: Request,
    db: AsyncSession = Depends(get_app_db_session),
):
    """Reexecuta a ingestão de um evento sem criar um novo registro."""
    ip_origem = request.client.host if request.client else None
    evento = await reprocessar_evento(
        db,
        response_id,
        get_forms_provider(),
        get_aghux_provider(),
        ip_origem,
    )
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento do webhook não encontrado.",
        )
    # Recarrega o DTO para incluir os contadores atualizados de divergências/alertas.
    for item in await listar_eventos(db, 200):
        if item["responseId"] == response_id:
            return item
    return evento_para_dict(evento)
