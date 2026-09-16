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

    # 3. Active Directory (LDAP)
    AD_URL: str = os.getenv("AD_URL", "")
    AD_BASEDN: str = os.getenv("AD_BASEDN", "DC=ebserhnet,DC=gov,DC=br")
    AD_BIND_USER: str = os.getenv("AD_BIND_USER", "")
    AD_BIND_PASSWORD: str = os.getenv("AD_BIND_PASSWORD", "")

    # 4. Segurança e Criptografia (JWT)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_EXP_HOURS: int = int(os.getenv("JWT_EXP_HOURS", "24"))
    REFRESH_TOKEN_EXP_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "30"))

    @classmethod
    def validate_config(cls):
        """Valida a integridade das configurações e dispara avisos de segurança."""
        if cls.ENV == "production":
            if "change-in-production" in cls.JWT_SECRET or "SUA_CHAVE_SECRETA" in cls.JWT_SECRET:
                logger.error(
                    "❌ ERRO CRÍTICO DE SEGURANÇA: A variável 'JWT_SECRET' está usando a chave padrão. "
                    "Altere para uma chave secreta aleatória forte no arquivo .env antes de rodar em produção!"
                )
            if not cls.AD_URL:
                logger.warning(
                    "⚠️ AVISO: Variável 'AD_URL' não definida em produção. "
                    "O sistema está operando no modo Mock de desenvolvimento."
                )
        logger.info(f"Configurações carregadas com sucesso. Ambiente: '{cls.ENV.upper()}'")


# Instância global de configurações
settings = Settings()
settings.validate_config()
