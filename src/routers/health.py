# src/routers/health.py
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from sqlalchemy import text

from ..version import VERSION, APP_NAME, ORGANIZATION

router = APIRouter(prefix="/api", tags=["Health & Monitoring"])

@router.get(
    "/health", 
    summary="Health Check Endpoint", 
    description="Verifica a saúde do servidor FastAPI, versão e conexões ativas com os bancos de dados."
)
async def health_check(request: Request):
    """
    Retorna o estado de saúde da aplicação, versão e verifica conexões ativas de banco de dados.
    """
    db_status = {}
    is_healthy = True

    # 1. Checar banco local (SQLite / App DB)
    try:
        if hasattr(request.app.state, 'app_db') and request.app.state.app_db:
            async with request.app.state.app_db.async_session_maker() as session:
                await session.execute(text("SELECT 1"))
            db_status["app_db"] = "connected"
        else:
            db_status["app_db"] = "not_initialized"
            is_healthy = False
    except Exception as e:
        db_status["app_db"] = f"error: {str(e)}"
        is_healthy = False

    # 2. Checar banco AGHU (PostgreSQL, se configurado)
    if hasattr(request.app.state, 'aghu_db') and request.app.state.aghu_db:
        try:
            async with request.app.state.aghu_db.async_session_maker() as session:
                await session.execute(text("SELECT 1"))
            db_status["aghu_postgres"] = "connected"
        except Exception as e:
            db_status["aghu_postgres"] = f"error: {str(e)}"
            is_healthy = False
    else:
        db_status["aghu_postgres"] = "disabled_or_not_configured"

    response_payload = {
        "status": "healthy" if is_healthy else "unhealthy",
        "app_name": APP_NAME,
        "version": VERSION,
        "organization": ORGANIZATION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "databases": db_status
    }

    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response_payload, status_code=status_code)
