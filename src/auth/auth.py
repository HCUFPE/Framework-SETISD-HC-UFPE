"""Autenticação por Adapter e emissão/validação de tokens da aplicação."""

import os
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.refresh_token import RefreshToken
from ..resources.database import get_app_db_session

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "24"))
REFRESH_TOKEN_EXP_DAYS = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "30"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


class IdentityProvider(ABC):
    """Contrato de Adapter: autentica e retorna identidade normalizada."""

    @abstractmethod
    def authenticate(self, username: str, password: str | None) -> dict[str, Any]:
        """Valida credenciais e retorna identificador e atributos de apresentação."""


class MockIdentityProvider(IdentityProvider):
    """Identidades fictícias para desenvolvimento/testes; senha compartilhada `demo`."""

    def authenticate(self, username: str, password: str | None) -> dict[str, Any]:
        from .authorization import USUARIOS_MOCK, resolver_permissoes

        identidade = USUARIOS_MOCK.get(username.strip().lower())
        if identidade is None or (password is not None and password != "demo" and not
                                  (username == "admin" and password == "admin")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Credenciais de desenvolvimento inválidas")
        perfis = list(identidade.perfis)
        return {
            "sub": identidade.username,
            "username": identidade.username,
            "displayName": [identidade.nome],
            "groups": [],  # Grupos do provedor de identidade nunca são permissões locais.
            "profiles": perfis,
            "permissions": resolver_permissoes(perfis),
            "auth_provider": "mock",
        }

    def search_user(self, username: str) -> dict[str, str | bool]:
        """Busca fictícia compatível com a rota legada, sem consultar serviço externo."""
        nome = username.strip().lower()
        known = {
            "admin": ("Administrador do Sistema", "admin@ebserh.gov.br", "SETISD / HC-UFPE"),
            "joao.silva": ("João da Silva", "joao.silva@ebserh.gov.br", "UTI Adulto / HC-UFPE"),
            "maria.souza": ("Maria Souza", "maria.souza@ebserh.gov.br", "Bloco Cirúrgico / HC-UFPE"),
        }
        values = known.get(nome)
        if values is None and "." in nome:
            values = (" ".join(part.capitalize() for part in nome.split(".")),
                      f"{nome}@ebserh.gov.br", "Unidade Hospitalar / HC-UFPE")
        return {"exists": bool(values), "username": nome,
                "displayName": values[0] if values else "",
                "email": values[1] if values else "",
                "department": values[2] if values else ""}


def _build_identity_provider() -> IdentityProvider:
    """Seleciona explicitamente o Adapter e bloqueia mock em produção."""
    environment = os.getenv("ENV", "development").lower()
    provider = os.getenv("AUTH_PROVIDER", "mock").lower()
    if environment == "production" and provider == "mock":
        raise RuntimeError("AUTH_PROVIDER=mock é proibido em produção")
    if provider == "mock" and environment in {"development", "test", "testing"}:
        return MockIdentityProvider()
    raise RuntimeError("Provedor institucional ainda não implementado; defina AUTH_PROVIDER=mock somente em desenvolvimento/testes")


class AuthHandler:
    """Orquestra Adapter de identidade e tokens sem acoplar a autorização ao protocolo."""

    def __init__(self, provider: IdentityProvider | None = None):
        self.provider = provider or _build_identity_provider()

    def authenticate_user(self, username: str, password: str | None) -> dict[str, Any]:
        return self.provider.authenticate(username, password)

    def search_ad_user(self, username: str) -> dict[str, Any]:
        if not isinstance(self.provider, MockIdentityProvider):
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                                detail="Consulta institucional não está configurada")
        return self.provider.search_user(username)

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        payload = dict(data)
        payload["exp"] = int((datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXP_HOURS))).timestamp())
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    async def create_refresh_token(self, user_id: str, groups: list[str], db: AsyncSession) -> str:
        token = secrets.token_urlsafe(64)
        db.add(RefreshToken(user_id=user_id, token=token, groups=groups,
                            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXP_DAYS)))
        await db.commit()
        return token

    async def verify_refresh_token(self, refresh_token: str, db: AsyncSession) -> RefreshToken:
        result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        token_obj = result.scalar_one_or_none()
        if not token_obj or token_obj.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token de renovação inválido ou expirado")
        return token_obj

    async def invalidate_refresh_token(self, refresh_token: str, db: AsyncSession) -> None:
        await db.execute(delete(RefreshToken).where(RefreshToken.token == refresh_token))
        await db.commit()

    def decode_token(self, token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado") from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc


auth_handler = AuthHandler()


def identidade_mock_disponivel() -> bool:
    """Informa se o Adapter ativo é o mock de desenvolvimento/testes."""
    return isinstance(auth_handler.provider, MockIdentityProvider)


async def get_current_user(user: dict = Depends(auth_handler.decode_token)) -> dict:
    """Dependência estável de identidade autenticada para módulos da aplicação."""
    return user
