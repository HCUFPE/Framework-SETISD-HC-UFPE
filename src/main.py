from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from .resources.database import DatabaseManager, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")

    # Initialize AGHU DB Manager and store in app.state
    aghu_dsn = os.getenv("POSTGRES_DSN")
    if aghu_dsn:
        app.state.aghu_db = DatabaseManager(aghu_dsn)
        print("AGHU PostgreSQL connection pool initialized.")
    else:
        print("WARNING: POSTGRES_DSN not found. Skipping AGHU DB initialization.")

    # Initialize App DB Manager (SQLite) and store in app.state
    app_dsn = os.getenv("SQLITE_DSN")
    if not app_dsn:
        raise ValueError("SQLITE_DSN not found in environment variables.")
    app.state.app_db = DatabaseManager(app_dsn)
    print("App SQLite connection pool initialized.")

    # Create tables for App DB (if they don't exist) - for development only, Alembic handles this in production
    async with app.state.app_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("App SQLite tables checked/created.")

    yield

    # Shutdown
    print("Shutting down...")
    if hasattr(app.state, 'aghu_db') and app.state.aghu_db:
        await app.state.aghu_db.close_connection()
        print("AGHU PostgreSQL connection pool closed.")
    if hasattr(app.state, 'app_db') and app.state.app_db:
        await app.state.app_db.close_connection()
        print("App SQLite connection pool closed.")

app = FastAPI(
    title="Framework-SETISD-HC-UFPE",
    description="Framework Monolítico Padrão (API REST FastAPI + Vue 3 SPA) para desenvolvimento de sistemas no HC-UFPE.",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)

# Configuração de CORS (Cross-Origin Resource Sharing)
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve o frontend Vue 3 empacotado
app.mount("/assets", StaticFiles(directory="src/static/dist/assets"), name="assets")
# Outros arquivos estáticos na raiz do dist (como favicon.ico)
app.mount("/static", StaticFiles(directory="src/static/dist"), name="static")

# Roteadores da API
from .routers import paciente, auth, admin, aih, bpa, material, health
app.include_router(health.router)
app.include_router(paciente.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(aih.router)
app.include_router(bpa.router)
app.include_router(material.router)

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """
    Serve o arquivo index.html para todas as rotas que não são da API ou arquivos estáticos.
    Isso é necessário para que o roteamento do Vue (SPA) funcione.
    """
    # Se a rota começa com 'api', deixa o roteador do FastAPI lidar
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    index_path = os.path.join("src", "static", "dist", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend build not found"}

# Exemplo:
# from .routers import aih, bpa, material
# app.include_router(aih.router)
# app.include_router(bpa.router)
# app.include_router(material.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
