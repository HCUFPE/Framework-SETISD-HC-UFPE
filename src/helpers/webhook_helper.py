"""
Helper de Autenticação do Webhook (HMAC-SHA256)
===============================================
O webhook é uma exceção pública ao padrão default-private, mas exige assinatura
sobre `timestamp . nonce . corpo_bruto`, tolerância de relógio e nonce único.
"""

import hashlib
import hmac
import time
from typing import Optional

from fastapi import HTTPException, status

from ..config import settings


def calcular_assinatura(secret: str, timestamp: str, nonce: str, body: bytes) -> str:
    """Calcula a assinatura HMAC no mesmo formato exigido pelo cabeçalho."""
    mensagem = timestamp.encode("utf-8") + b"." + nonce.encode("utf-8") + b"." + body
    return "sha256=" + hmac.new(secret.encode("utf-8"), mensagem, hashlib.sha256).hexdigest()


def validar_assinatura_webhook(
    body: bytes,
    timestamp: Optional[str],
    nonce: Optional[str],
    assinatura: Optional[str],
    secret: Optional[str] = None,
    agora: Optional[float] = None,
) -> None:
    """Valida cabeçalhos obrigatórios, janela temporal e assinatura do webhook.

    Lança HTTPException 401 para qualquer falha, sem detalhar qual parte falhou.
    """
    secret = secret or settings.FORMS_WEBHOOK_SECRET
    if not secret or not timestamp or not nonce or not assinatura:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura do webhook ausente ou inválida.",
        )
    try:
        instante = int(timestamp)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Timestamp do webhook inválido.",
        ) from exc
    atual = int(agora if agora is not None else time.time())
    if abs(atual - instante) > settings.WEBHOOK_MAX_SKEW_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Timestamp do webhook fora da janela permitida.",
        )
    esperada = calcular_assinatura(secret, timestamp, nonce, body)
    if not hmac.compare_digest(esperada, assinatura):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura do webhook inválida.",
        )
