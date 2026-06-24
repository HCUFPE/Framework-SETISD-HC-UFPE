from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.perfis import Perfil, require_perfil
from ..controllers import processamento_controller
from ..resources.database import get_app_db_session
from ..schemas.bloco import BlocoOut, BlocoDetalhe, GerarLaminasRequest
from ..schemas.lamina import LaminaOut, GerarLaminasResult
from ..schemas.processamento import (
    CasseteFilaOut,
    ConcluirLoteRequest,
    IniciarLoteRequest,
    LoteOut,
)

router = APIRouter(prefix="/api/processamento", tags=["Processamento Técnico"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# --- Fila e lotes ---

@router.get("/pendencias", response_model=List[dict])
async def listar_pendencias(
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.TECNICO)),
):
    """Fila de cassetes aguardando processamento técnico."""
    return await processamento_controller.listar_pendencias(session)


@router.post("/lote", response_model=dict, status_code=201)
async def iniciar_lote(
    dados: IniciarLoteRequest,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.TECNICO)),
):
    """Inicia um ciclo de processamento com os cassetes selecionados."""
    result = await processamento_controller.iniciar_lote(
        session, dados, current_user.get("username"), _ip(request)
    )
    return {
        "lote": LoteOut.model_validate(result["lote"]).model_dump(),
        "total_cassetes": len(result["cassetes"]),
    }


@router.post("/lote/{id_lote}/concluir", response_model=dict)
async def concluir_lote(
    id_lote: str,
    dados: ConcluirLoteRequest,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.TECNICO)),
):
    """Conclui o ciclo: gera BlocoParafina para cada cassete e avança o exame."""
    result = await processamento_controller.concluir_lote(
        session, id_lote, dados, current_user.get("username"), _ip(request)
    )
    return {
        "lote": LoteOut.model_validate(result["lote"]).model_dump(),
        "blocos_gerados": len(result["blocos"]),
        "blocos": [BlocoOut.model_validate(b).model_dump() for b in result["blocos"]],
    }


# --- Blocos ---

@router.get("/blocos/pendencias", response_model=List[dict])
async def listar_blocos_pendentes(
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.TECNICO)),
):
    """Fila de blocos aguardando corte microtômico."""
    return await processamento_controller.listar_blocos_pendentes(session)


@router.get("/blocos/buscar", response_model=List[dict])
async def buscar_bloco(
    codigo_bloco: str,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Busca manual de bloco por código (mesma rota que o leitor QR usaria)."""
    return await processamento_controller.buscar_bloco(session, codigo_bloco)


@router.post("/blocos/{id_bloco}/laminas", response_model=GerarLaminasResult, status_code=201)
async def gerar_laminas(
    id_bloco: str,
    dados: GerarLaminasRequest,
    request: Request,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil(Perfil.TECNICO)),
):
    """Gera N lâminas para um bloco e avança o bloco para 'Aguardando Microscopia'."""
    result = await processamento_controller.gerar_laminas(
        session, id_bloco, dados, current_user.get("username"), _ip(request)
    )
    return GerarLaminasResult(
        bloco_id=result["bloco_id"],
        codigo_bloco=result["codigo_bloco"],
        laminas=[LaminaOut.model_validate(l) for l in result["laminas"]],
        etiquetas=result["etiquetas"],
    )


@router.get("/blocos/{id_bloco}/laminas", response_model=List[LaminaOut])
async def listar_laminas(
    id_bloco: str,
    session: AsyncSession = Depends(get_app_db_session),
    current_user: dict = Depends(require_perfil()),
):
    """Lista todas as lâminas de um bloco."""
    laminas = await processamento_controller.listar_laminas(session, id_bloco)
    return [LaminaOut.model_validate(l) for l in laminas]
