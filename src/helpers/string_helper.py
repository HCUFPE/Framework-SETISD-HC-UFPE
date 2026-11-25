"""
Helpers de Texto e Normalização de Respostas do Microsoft Forms
===============================================================
O payload do Power Automate pode trazer respostas por nome de pergunta, por
`questionId` ou em listas `answers`. Estes utilitários achatam essa estrutura
sem inventar valores e mantêm a comparação com o AGHUX tolerante a acentos.
"""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Iterable, Optional


def normalizar_chave(texto: str) -> str:
    """Remove acentos/pontuação e deixa a chave em minúsculas para busca."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def normalizar_texto(texto: Optional[str]) -> str:
    """Normaliza texto para comparação (caixa, acentos e espaços)."""
    if texto is None:
        return ""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", sem_acento.lower())).strip()


def valor_texto(valor: Any) -> str:
    """Converte valores simples, listas e dicionários em texto legível."""
    if valor is None:
        return ""
    if isinstance(valor, (str, int, float, bool)):
        return str(valor).strip()
    if isinstance(valor, dict):
        partes = [
            valor_texto(item)
            for chave, item in valor.items()
            if chave.lower() not in {"questionid", "question", "id"}
        ]
        return "; ".join(parte for parte in partes if parte)
    if isinstance(valor, (list, tuple, set)):
        return "; ".join(parte for parte in (valor_texto(item) for item in valor) if parte)
    return str(valor).strip()


def achatar_resposta(payload: Any, destino: Optional[dict] = None) -> dict:
    """Achata recursivamente o payload, indexando perguntas e respostas."""
    destino = destino if destino is not None else {}
    if isinstance(payload, dict):
        pergunta = next(
            (payload[chave] for chave in ("question", "title", "questionId", "pergunta")
             if payload.get(chave)),
            None,
        )
        resposta = next(
            (payload[chave] for chave in ("answer", "resposta", "value", "response")
             if chave in payload),
            None,
        )
        if pergunta is not None and resposta is not None:
            destino[normalizar_chave(valor_texto(pergunta))] = valor_texto(resposta)
        for chave, valor in payload.items():
            chave_norm = normalizar_chave(str(chave))
            if isinstance(valor, (dict, list)):
                achatar_resposta(valor, destino)
            texto = valor_texto(valor)
            if texto and chave_norm not in {"questionid", "question", "answer", "resposta", "value"}:
                destino.setdefault(chave_norm, texto)
    elif isinstance(payload, (list, tuple, set)):
        for item in payload:
            achatar_resposta(item, destino)
    return destino


def obter_campo(payload: Any, apelidos: Iterable[str]) -> str:
    """Retorna o primeiro valor não vazio dentre os apelidos informados."""
    if not payload:
        return ""
    plano = achatar_resposta(payload)
    for apelido in apelidos:
        chave = normalizar_chave(apelido)
        if chave in plano and plano[chave]:
            return plano[chave]
    for apelido in apelidos:
        chave = normalizar_chave(apelido)
        for chave_encontrada, valor in plano.items():
            if chave and (chave in chave_encontrada or chave_encontrada in chave) and valor:
                return valor
    return ""


def parse_datetime(valor: Any, fallback: Optional[datetime] = None) -> datetime:
    """Interpreta ISO-8601 (com `Z`) e garante datetime UTC."""
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
    texto = valor_texto(valor).replace("Z", "+00:00")
    if texto:
        try:
            parse = datetime.fromisoformat(texto)
            return parse if parse.tzinfo else parse.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return fallback or datetime.now(timezone.utc)


def extrair_codigo_exame(nome_ou_codigo: str) -> str:
    """Extrai a sigla do exame quando o formulário traz 'SIGLA - Nome'."""
    texto = (nome_ou_codigo or "").strip()
    if not texto:
        return ""
    primeira = re.split(r"\s[-–—:|]\s|\s{2,}", texto, maxsplit=1)[0].strip()
    return primeira if len(primeira) <= 20 else ""
