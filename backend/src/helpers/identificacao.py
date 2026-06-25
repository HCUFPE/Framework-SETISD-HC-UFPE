"""
Geração de identificadores de amostras.

IMPORTANTE: nada aqui depende de hardware. O `qr_code` é apenas uma STRING.
Quando a impressora térmica chegar, essa string será renderizada como imagem
de QR Code; quando o leitor (pistola HID) chegar, ele apenas digitará essa
mesma string no campo de busca. O backend permanece idêntico.

Formato do QR Code (doc 04.banco-de-dados):
    {TIPO}|{uuid}|{numero_solicitacao}|{timestamp_iso8601}
Exemplo:
    FRASCO|550e8400-...-440000|HP-0001/26.1|2026-06-22T10:30:00Z

Formato do número de solicitação (igual ao padrão da equipe e do frontend):
    PREFIXO-NNNN/AA.S
    Ex: HP-0001/26.1  (HP, sequencial 1, ano 2026, semestre 1)
        IH-0012/26.2  (IHQ, sequencial 12, ano 2026, semestre 2)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.exame import Exame

# Mapeamento tipo_exame -> prefixo do código (igual a frontend/src/constants/examTypes.ts)
TIPO_EXAME_PREFIXO: dict[str, str] = {
    "HP": "HP",
    "IHQ": "IH",
    "HPDerm": "HD",
    "CCV": "CV",
    "CG": "CG",
    "RevInt": "RI",
    "Congela": "CO",
}

TIPOS_EXAME_VALIDOS = set(TIPO_EXAME_PREFIXO.keys())


def _agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def semestre_de(data: datetime | None = None) -> int:
    """Retorna 1 (jan-jun) ou 2 (jul-dez) para a data informada (ou agora)."""
    mes = (data or datetime.now(timezone.utc)).month
    return 1 if mes <= 6 else 2


def formatar_numero_solicitacao(tipo_exame: str, sequencial: int, ano: int, semestre: int) -> str:
    """
    Monta o código no padrão da equipe: PREFIXO-NNNN/AA.S
    Ex: formatar_numero_solicitacao('HP', 1, 2026, 1) -> 'HP-0001/26.1'
    """
    prefixo = TIPO_EXAME_PREFIXO.get(tipo_exame, tipo_exame)
    ano_curto = str(ano)[-2:]
    return f"{prefixo}-{sequencial:04d}/{ano_curto}.{semestre}"


async def gerar_numero_solicitacao(
    session: AsyncSession,
    tipo_exame: str = "HP",
    ano: int | None = None,
    semestre: int | None = None,
) -> tuple[str, int, int, int]:
    """
    Gera o próximo número de solicitação no formato HP-NNNN/AA.S.

    Retorna (numero_solicitacao, sequencial, ano, semestre) para que o
    controller persista os campos separados no modelo.

    O sequencial é derivado do máximo já existente para o mesmo tipo+ano+semestre
    dentro da transação; a unicidade final é garantida pela constraint UNIQUE
    em Exame.numero_solicitacao.
    """
    if ano is None:
        ano = datetime.now(timezone.utc).year
    if semestre is None:
        semestre = semestre_de()

    stmt = (
        select(func.max(Exame.sequencial))
        .where(
            Exame.tipo_exame == tipo_exame,
            Exame.ano == ano,
            Exame.semestre == semestre,
        )
    )
    ultimo = (await session.execute(stmt)).scalar_one_or_none()
    proximo = (ultimo or 0) + 1

    numero = formatar_numero_solicitacao(tipo_exame, proximo, ano, semestre)
    return numero, proximo, ano, semestre


def gerar_qr_code(tipo: str, numero_solicitacao: str, identificador: str | None = None) -> str:
    """
    Monta a string de identificação de um subproduto.

    `tipo`: FRASCO | CASSETE | BLOCO | LAMINA
    `identificador`: UUID do subproduto (se omitido, um novo é gerado).
    """
    if identificador is None:
        identificador = str(uuid.uuid4())
    return f"{tipo.upper()}|{identificador}|{numero_solicitacao}|{_agora_iso()}"


def gerar_codigo_interno_frasco(numero_solicitacao: str) -> str:
    """Código interno legível do frasco (derivado do número de solicitação)."""
    return f"{numero_solicitacao}-F1"


def letra_fragmento(indice: int) -> str:
    """
    Converte um índice 0-based em rótulo de fragmento estilo planilha:
    0->A, 1->B, ..., 25->Z, 26->AA, 27->AB, ...
    """
    if indice < 0:
        raise ValueError("Índice de fragmento não pode ser negativo.")
    letras = ""
    indice += 1
    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(ord("A") + resto) + letras
    return letras
