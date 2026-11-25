"""
Helper de Criptografia de Dados Sensíveis (LGPD)
================================================
CPF/CNS são armazenados com AES-GCM (nonce de 12 bytes) e nunca aparecem em
logs, auditoria ou respostas de API. A chave vem de `Settings.chave_cripto()`.
"""

import base64
import hashlib
import hmac
import os
import re
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..config import settings

PREFIXO = "v1:"
NUMERO_NAO_DIGITO = re.compile(r"\D")


def _texto(value: Optional[str]) -> Optional[str]:
    """Normaliza um valor opcional para texto não vazio."""
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None


def encrypt_phi(value: Optional[str]) -> Optional[str]:
    """Criptografa um dado sensível e retorna `v1:<base64(nonce+ciphertext)>`."""
    texto = _texto(value)
    if texto is None:
        return None
    nonce = os.urandom(12)
    ciphertext = AESGCM(settings.chave_cripto()).encrypt(nonce, texto.encode("utf-8"), None)
    return PREFIXO + base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_phi(value: Optional[str]) -> Optional[str]:
    """Decifra um dado sensível previamente criptografado por `encrypt_phi`."""
    texto = _texto(value)
    if texto is None:
        return None
    if not texto.startswith(PREFIXO):
        raise ValueError("Formato de dado criptografado desconhecido.")
    bruto = base64.b64decode(texto[len(PREFIXO):], validate=True)
    return AESGCM(settings.chave_cripto()).decrypt(bruto[:12], bruto[12:], None).decode("utf-8")


def hash_phi(value: Optional[str]) -> Optional[str]:
    """Hash HMAC-SHA256 para busca/deduplicação sem revelar o dado original."""
    texto = _texto(value)
    if texto is None:
        return None
    # Domínio separado da chave AES (evita reutilizar a mesma chave para fins distintos).
    chave_hash = hashlib.sha256(settings.chave_cripto() + b"sae-hc:phi-hash").digest()
    return hmac.new(chave_hash, texto.encode("utf-8"), hashlib.sha256).hexdigest()


def mask_phi(value: Optional[str]) -> Optional[str]:
    """Mascara CPF/CNS preservando apenas os últimos 4 dígitos para exibição."""
    texto = _texto(value)
    if texto is None:
        return None
    digitos = NUMERO_NAO_DIGITO.sub("", texto)
    if len(digitos) < 4:
        return "***"
    return "***." + digitos[-4:]


def to_dict_seguro(valores: dict) -> dict:
    """Remove chaves sensíveis antes de gravar em auditoria."""
    sensiveis = {"cpf", "cns", "cpf_cripto", "cns_cripto", "cpf_hash", "cns_hash", "payload", "resposta"}
    return {chave: valor for chave, valor in valores.items() if chave not in sensiveis}
