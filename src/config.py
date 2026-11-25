"""
Módulo Centralizado de Configurações e Validação de Segredos (Settings)
=======================================================================
Garante o Padrão de Governança de Variáveis de Ambiente (Env Vars & Secrets) do HC-UFPE.
Carrega o arquivo .env e valida se os parâmetros essenciais e chaves de segurança estão corretos.
"""

import base64
import json
import logging
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("config")

# Mapa padrão de apelidos do Microsoft Forms. Pode ser sobrescrito por
# FORMS_FIELD_MAP (JSON) sem alterar código quando o questionário mudar.
DEFAULT_FORMS_FIELD_MAP: Dict[str, List[str]] = {
    "nome": ["nome", "nomeCompleto", "name", "patientName", "paciente"],
    "prontuario": ["prontuario", "prontuarioPaciente", "registration", "codigoPaciente"],
    "codigoSolicitacaoAghux": ["codigoSolicitacao", "codigo_solicitacao", "solicitationId"],
    "cpf": ["cpf", "CPF"],
    "cns": ["cns", "CNS"],
    "telefone": ["telefone", "celular", "phone", "contato"],
    "cep": ["cep", "cepPaciente", "postalCode", "zipCode"],
    "logradouro": ["logradouro", "endereco", "endereço", "address", "rua", "avenida"],
    "numero": ["numero", "número", "numeroEndereco", "number"],
    "complemento": ["complemento", "complementoEndereco", "complement"],
    "bairro": ["bairro", "district", "neighborhood"],
    "cidade": ["cidade", "city"],
    "estado": ["estado", "uf", "state"],
    "codigoExame": ["codigoExame", "codigo_exame", "examCode", "exame"],
    "nomeExame": ["nomeExame", "nome_exame", "examName", "exame"],
    "unidadeSolicitante": ["unidadeSolicitante", "unidade", "unit", "setorSolicitante"],
    "submittedAt": ["submittedAt", "dataEnvio", "dataSolicitacao", "submissionDate"],
}


def _carregar_mapa_campos() -> Dict[str, List[str]]:
    """Carrega o mapa de campos do Forms a partir de FORMS_FIELD_MAP (JSON)."""
    raw = os.getenv("FORMS_FIELD_MAP", "")
    if not raw:
        return {chave: list(valores) for chave, valores in DEFAULT_FORMS_FIELD_MAP.items()}
    try:
        carregado = json.loads(raw)
        if not isinstance(carregado, dict):
            raise ValueError("FORMS_FIELD_MAP deve ser um objeto JSON.")
        mapa: Dict[str, List[str]] = {}
        for chave, apelidos in carregado.items():
            if isinstance(apelidos, str):
                apelidos = [apelidos]
            if not isinstance(apelidos, list) or not all(isinstance(item, str) for item in apelidos):
                raise ValueError(f"Apelidos inválidos para '{chave}' em FORMS_FIELD_MAP.")
            mapa[str(chave)] = [str(item) for item in apelidos]
        return mapa
    except (ValueError, TypeError) as exc:
        logger.error("FORMS_FIELD_MAP inválido (%s). Usando o mapa padrão.", exc)
        return {chave: list(valores) for chave, valores in DEFAULT_FORMS_FIELD_MAP.items()}


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

    # 5. Integração Microsoft Forms → AGHUX (TASK-026 a TASK-032)
    FORMS_WEBHOOK_SECRET: str = os.getenv("FORMS_WEBHOOK_SECRET", "")
    FORMS_PROVIDER_TYPE: str = os.getenv("FORMS_PROVIDER_TYPE", "MOCK").upper()
    FORMS_API_BASE_URL: str = os.getenv(
        "FORMS_API_BASE_URL", "https://forms.office.com/formapi/api"
    )
    FORMS_FORM_ID: str = os.getenv("FORMS_FORM_ID", "")
    FORMS_FIELD_MAP: Dict[str, List[str]] = _carregar_mapa_campos()
    WEBHOOK_MAX_SKEW_SECONDS: int = int(os.getenv("WEBHOOK_MAX_SKEW_SECONDS", "300"))
    AGHUX_PROVIDER_TYPE: str = os.getenv("AGHUX_PROVIDER_TYPE", "JSON").upper()
    AGHUX_FIXTURE_PATH: str = os.getenv(
        "AGHUX_FIXTURE_PATH", "frontend/src/mocks/dadosAghux.json"
    )
    PHI_ENCRYPTION_KEY: str = os.getenv("PHI_ENCRYPTION_KEY", "")

    # 6. Gestão de Agendamentos e Distância (v0.3.0)
    DISTANCE_PROVIDER_TYPE: str = os.getenv("DISTANCE_PROVIDER_TYPE", "OSM").upper()
    OSM_NOMINATIM_URL: str = os.getenv(
        "OSM_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search"
    )
    OSM_OSRM_URL: str = os.getenv("OSM_OSRM_URL", "https://router.project-osrm.org")
    OSM_USER_AGENT: str = os.getenv(
        "OSM_USER_AGENT", "SAE-HC/0.4.0 (contato: ti@hc.ebserh.gov.br)"
    )
    HOSPITAL_LATITUDE: str = os.getenv("HOSPITAL_LATITUDE", "-8.0476")
    HOSPITAL_LONGITUDE: str = os.getenv("HOSPITAL_LONGITUDE", "-34.8770")
    DISTANCE_TIMEOUT_SECONDS: float = float(os.getenv("DISTANCE_TIMEOUT_SECONDS", "5"))
    DISTANCE_CACHE_TTL_HOURS: float = float(os.getenv("DISTANCE_CACHE_TTL_HOURS", "168"))
    MOCK_DISTANCE_KM: float = float(os.getenv("MOCK_DISTANCE_KM", "12.5"))
    AGENDA_SUGGESTION_HORIZON_DAYS: int = int(os.getenv("AGENDA_SUGGESTION_HORIZON_DAYS", "30"))
    AGENDA_SUGGESTION_LIMIT: int = int(os.getenv("AGENDA_SUGGESTION_LIMIT", "3"))
    AGENDA_WEIGHT_PRIORIDADE: float = float(os.getenv("AGENDA_WEIGHT_PRIORIDADE", "35"))
    AGENDA_WEIGHT_VAGAS: float = float(os.getenv("AGENDA_WEIGHT_VAGAS", "15"))
    AGENDA_WEIGHT_COMPATIBILIDADE: float = float(os.getenv("AGENDA_WEIGHT_COMPATIBILIDADE", "20"))
    AGENDA_WEIGHT_ESPERA: float = float(os.getenv("AGENDA_WEIGHT_ESPERA", "20"))
    AGENDA_WEIGHT_DISTANCIA: float = float(os.getenv("AGENDA_WEIGHT_DISTANCIA", "10"))

    @classmethod
    def chave_cripto(cls) -> bytes:
        """
        Retorna a chave AES de 32 bytes. Em desenvolvimento, deriva uma chave
        estável do JWT_SECRET apenas para permitir testes offline; em produção,
        exige PHI_ENCRYPTION_KEY em base64.
        """
        valores_placeholder = ("ALTERAR", "CHAVE_BASE64", "SUA_CHAVE")
        chave_configurada = cls.PHI_ENCRYPTION_KEY.strip()
        placeholder = any(marca in chave_configurada.upper() for marca in valores_placeholder)
        if chave_configurada and not placeholder:
            try:
                chave = base64.b64decode(chave_configurada, validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError("PHI_ENCRYPTION_KEY deve estar em base64 válido.") from exc
            if len(chave) != 32:
                raise ValueError("PHI_ENCRYPTION_KEY deve decodificar exatamente 32 bytes.")
            return chave
        if cls.ENV == "production":
            raise ValueError("PHI_ENCRYPTION_KEY é obrigatória em produção.")
        # SHA256 determinístico somente para desenvolvimento/testes.
        import hashlib

        return hashlib.sha256(cls.JWT_SECRET.encode("utf-8")).digest()

    @classmethod
    def validate_config(cls) -> None:
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
            if not cls.FORMS_WEBHOOK_SECRET or "ALTERAR" in cls.FORMS_WEBHOOK_SECRET.upper():
                logger.error(
                    "❌ ERRO CRÍTICO: 'FORMS_WEBHOOK_SECRET' não configurado em produção; "
                    "o webhook do Microsoft Forms não pode ser protegido."
                )
            chave_phi = cls.PHI_ENCRYPTION_KEY.strip()
            if (
                not chave_phi
                or "ALTERAR" in chave_phi.upper()
                or "CHAVE_BASE64" in chave_phi.upper()
            ):
                logger.error(
                    "❌ ERRO CRÍTICO: 'PHI_ENCRYPTION_KEY' não configurada em produção; "
                    "CPF/CNS não podem ser criptografados com segurança."
                )
            if cls.FORMS_PROVIDER_TYPE == "MOCK" or cls.AGHUX_PROVIDER_TYPE == "JSON":
                logger.warning(
                    "⚠️ AVISO: provedores MOCK/JSON ativos em produção. "
                    "Configure FORMS_PROVIDER_TYPE e AGHUX_PROVIDER_TYPE com as fontes reais."
                )
            marcadores_user_agent = ("ALTERAR", "SEU_USER", "PLACEHOLDER", "SUBSTITUIR")
            if (
                not cls.OSM_USER_AGENT.strip()
                or any(marca in cls.OSM_USER_AGENT.upper() for marca in marcadores_user_agent)
            ):
                logger.error(
                    "❌ ERRO CRÍTICO: 'OSM_USER_AGENT' está vazio/placeholder em produção. "
                    "Informe um User-Agent identificável com contato para o OpenStreetMap."
                )
            if not cls.HOSPITAL_LATITUDE.strip() or not cls.HOSPITAL_LONGITUDE.strip():
                logger.error(
                    "❌ ERRO CRÍTICO: 'HOSPITAL_LATITUDE'/'HOSPITAL_LONGITUDE' vazias em produção; "
                    "o cálculo de distância até o hospital ficará indisponível."
                )
            if cls.DISTANCE_PROVIDER_TYPE == "MOCK":
                logger.error(
                    "❌ ERRO CRÍTICO: 'DISTANCE_PROVIDER_TYPE=MOCK' em produção; "
                    "distâncias simuladas não podem orientar agendamentos reais."
                )
        logger.info(f"Configurações carregadas com sucesso. Ambiente: '{cls.ENV.upper()}'")


# Instância global de configurações
settings = Settings()
settings.validate_config()
