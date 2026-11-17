"""
Módulo Centralizado de Configurações e Validação de Segredos (Settings)
=======================================================================
Garante o Padrão de Governança de Variáveis de Ambiente (Env Vars & Secrets) do HC-UFPE.
Carrega o arquivo .env e valida se os parâmetros essenciais e chaves de segurança estão corretos.
"""

import os
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("config")


class Settings:
    # 1. Configurações do Servidor
    ENV: str = os.getenv("ENV", "development").lower()
    AUTH_PROVIDER: str = os.getenv("AUTH_PROVIDER", "mock").lower()
    AP_REQUEST_PROVIDER: str = os.getenv("AP_REQUEST_PROVIDER", "mock").lower()
    AP_REQUEST_FIXTURE: str = os.getenv("AP_REQUEST_FIXTURE", "demo").strip().lower()
    AP_MOCK_REQUESTS_AVAILABLE: bool = os.getenv("AP_MOCK_REQUESTS_AVAILABLE", "true").strip().lower() not in {
        "0", "false", "no", "off"
    }
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").lower()
    RAW_ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    ALLOWED_ORIGINS: List[str] = [
        origin.strip() for origin in RAW_ALLOWED_ORIGINS.split(",") if origin.strip()
    ]

    # 2. Provedores e Bancos de Dados
    PACIENTE_PROVIDER_TYPE: str = os.getenv("PACIENTE_PROVIDER_TYPE", "POSTGRES").upper()
    APP_DB_URL: str = os.getenv("APP_DB_URL", "sqlite+aiosqlite:///data/app.db")
    POSTGRES_DSN: str = os.getenv("POSTGRES_DSN", "")
    ORACLE_DSN: str = os.getenv("ORACLE_DSN", "")

    # 4. Segurança e Criptografia (JWT)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_EXP_HOURS: int = int(os.getenv("JWT_EXP_HOURS", "24"))
    REFRESH_TOKEN_EXP_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "30"))

    @classmethod
    def validate_config(cls):
        """Valida a integridade das configurações e dispara avisos de segurança."""
        if cls.AP_REQUEST_PROVIDER == "mock" and cls.ENV not in {"development", "test", "testing"}:
            raise RuntimeError("AP_REQUEST_PROVIDER=mock is restricted to development/test")
        if cls.AP_REQUEST_PROVIDER != "mock":
            raise RuntimeError("Institutional AP request provider is not implemented")
        if cls.AP_REQUEST_FIXTURE not in {"demo", "minimal"}:
            raise RuntimeError("AP_REQUEST_FIXTURE must be 'demo' or 'minimal'")
        if cls.ENV == "production":
            if "change-in-production" in cls.JWT_SECRET or "SUA_CHAVE_SECRETA" in cls.JWT_SECRET:
                logger.error(
                    "❌ ERRO CRÍTICO DE SEGURANÇA: A variável 'JWT_SECRET' está usando a chave padrão. "
                    "Altere para uma chave secreta aleatória forte no arquivo .env antes de rodar em produção!"
                )
            if cls.AUTH_PROVIDER == "mock":
                raise RuntimeError("AUTH_PROVIDER=mock é proibido em produção")
        logger.info(f"Configurações carregadas com sucesso. Ambiente: '{cls.ENV.upper()}'")


# Instância global de configurações
settings = Settings()
settings.validate_config()
