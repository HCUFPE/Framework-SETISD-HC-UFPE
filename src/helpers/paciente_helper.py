"""
Helper de Identificação Pseuônima de Pacientes (LGPD)
===================================================
A chave do paciente é um HMAC-SHA256 estável derivada da chave cripto da
aplicação e calculada sobre o prontuário normalizado (com fallback para
CPF/CNS normalizados). Ela permite agrupar solicitações e bloquear choques de
agendamento sem expor nenhum dado pessoal em APIs, logs ou auditoria.
"""

import hashlib
import hmac
import re
import unicodedata
from typing import Optional

from ..config import settings

DOMINIO_CHAVE = b"sae-hc:paciente-chave"


def normalizar_prontuario(valor: Optional[str]) -> str:
    """Remove acentos e pontuação do prontuário para gerar uma chave estável."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def normalizar_documento(valor: Optional[str]) -> str:
    """Normaliza CPF/CNS mantendo apenas dígitos (sem inventar valores)."""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


def paciente_chave(
    prontuario: Optional[str] = None,
    cpf: Optional[str] = None,
    cns: Optional[str] = None,
) -> str:
    """
    Retorna 64 hex de HMAC-SHA256 sobre a identificação normalizada do paciente.

    Nunca retorna PHI: prontuário, CPF e CNS são apenas entradas do HMAC e não
    aparecem no resultado. Sem nenhum identificador, retorna texto vazio.
    """
    identificador = (
        normalizar_prontuario(prontuario)
        or normalizar_documento(cpf)
        or normalizar_documento(cns)
    )
    if not identificador:
        return ""
    chave_hmac = hashlib.sha256(settings.chave_cripto() + DOMINIO_CHAVE).digest()
    return hmac.new(chave_hmac, identificador.encode("utf-8"), hashlib.sha256).hexdigest()
