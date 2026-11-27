from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple

from fastapi import HTTPException, status

from ..providers.interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface

# --- MAPA SIGLA DO EXAME (AGHU) → TIPO DE EXAME (SAP) -------------------------
# Siglas fora deste mapa são ignoradas (não são exames de Anatomia Patológica).
# ATENÇÃO: o mapeamento de "CITO" → CCV ainda precisa ser confirmado com o HC.
SIGLA_PARA_TIPO_EXAME: Dict[str, str] = {
    # Histopatológico
    "APECR": "HP",
    "HPDER": "HP",
    "MBIOP": "HP",
    "MPCIR": "HP",
    "COUT2": "HP",
    "COLUT": "HP",
    # Citologia cérvico-vaginal
    "CCVM": "CCV",
    "CITO": "CCV",
    # Citologia geral
    "CITOP": "CG",
    "CPMAM": "CG",
    # Congelação
    "CONGE": "CO",
    # Imuno-histoquímica
    "IMUHI": "IHQ",
}

# --- MAPA ORIGEM (AGHU) → OrigemAtendimento (SAP) -----------------------------
ORIGEM_PARA_CODIGO: Dict[str, str] = {
    "Ambulatório": "AMBULATORIO",
    "Internação": "INTERNACAO",
    "Cirurgia": "CIRURGIA",
    "Paciente Externo": "EXTERNO",
}

SITUACAO_RECEPCAO_INICIAL = "AGUARDANDO_RECEBIMENTO"

_FORMATOS_DATA = (
    ("%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
    ("%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M"),
    ("%d/%m/%Y", "%Y-%m-%d"),
)


def _converter_data(valor: Optional[str]) -> Optional[str]:
    """Converte `DD/MM/AAAA[ HH:MM[:SS]]` para ISO 8601. Retorna None se vazio/inválido."""
    if not valor:
        return None
    texto = valor.strip()
    for formato_entrada, formato_saida in _FORMATOS_DATA:
        try:
            return datetime.strptime(texto, formato_entrada).strftime(formato_saida)
        except ValueError:
            continue
    return None


def _texto(row: Dict[str, Any], chave: str) -> str:
    """Retorna o valor da coluna como string (vazia se ausente)."""
    valor = row.get(chave)
    return "" if valor is None else str(valor)


# Caracteres invisíveis encontrados em valores do AGHU (ver data/dicionario_dados.md).
_INVISIVEIS = "\u200b\u200c\u200d\ufeff"


def _texto_limpo(row: Dict[str, Any], chave: str) -> str:
    """Retorna o valor da coluna sem caracteres invisíveis nem espaços nas pontas."""
    texto = _texto(row, chave)
    for caractere in _INVISIVEIS:
        texto = texto.replace(caractere, "")
    return texto.strip()


SEPARADOR_ID = "-"


def _montar_id(codigo_solicitacao: str, numero_amostra: str) -> str:
    """Monta o id único do item no formato `<codigoSolicitacao>-<numeroAmostra>`."""
    return f"{codigo_solicitacao}{SEPARADOR_ID}{numero_amostra}"


def _separar_id(valor: str) -> Tuple[str, Optional[str]]:
    """Separa um identificador em (codigoSolicitacao, numeroAmostra).

    Aceita o código da solicitação puro ("1234" → ("1234", None)) ou o id
    composto ("1234-2" → ("1234", "2")).
    """
    texto = valor.strip()
    if SEPARADOR_ID in texto:
        codigo, numero_amostra = texto.rsplit(SEPARADOR_ID, 1)
        return codigo.strip(), numero_amostra.strip()
    return texto, None


def _mapear_linha(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Mapeia uma linha da fonte para o formato `SolicitacaoAghu` (camelCase).

    Retorna None quando a sigla do exame não pertence ao mapa de tipos de exame.
    """
    sigla = _texto(row, "sigla_exame").strip().upper()
    nome_exame = _texto(row, "nome_exame")
    nome_normalizado = _normalizar_texto(nome_exame)
    tipo = SIGLA_PARA_TIPO_EXAME.get(sigla)
    if tipo is None and (sigla.startswith("REV") or "REVISAO" in nome_normalizado):
        tipo = "REVISAO"
    if tipo is None:
        return None

    codigo = _texto(row, "codigo_solicitacao")
    numero_amostra = _texto(row, "numero_amostra")

    return {
        # Identificador único do item: "<codigoSolicitacao>-<numeroAmostra>"
        "id": _montar_id(codigo, numero_amostra),
        "codigoSolicitacao": codigo,
        "prontuario": _texto(row, "prontuario"),
        "nomePaciente": _texto(row, "nome_paciente"),
        "dataNascimento": _converter_data(_texto(row, "data_nascimento")),
        "sexo": None,
        "origem": ORIGEM_PARA_CODIGO.get(_texto(row, "origem").strip()),
        "unidade": _texto_limpo(row, "unidade"),
        "especialidade": _texto(row, "especialidade"),
        "nomeSolicitante": None,
        "dataSolicitacao": _converter_data(_texto(row, "data_solicitacao")),
        "siglaExame": sigla,
        "nomeExame": nome_exame,
        "tipoExameSugerido": tipo,
        "descricaoMaterial": _texto(row, "descricao_material"),
        "informacoesClinicas": _texto(row, "informacoes_clinica"),
        "statusAghuDescricao": _texto(row, "status_item_exame"),
        "situacaoRecepcao": SITUACAO_RECEPCAO_INICIAL,
        # Campos extras do AGHU sem correspondência no tipo do frontend
        "numeroAmostra": numero_amostra,
        "codigoLab": _texto(row, "codigo_lab"),
        "convenio": _texto(row, "convenio"),
        "codStatusItem": _texto(row, "cod_status_item"),
    }


def _normalizar_texto(valor: str) -> str:
    """Normaliza texto do AGHU para reconhecer rótulos de Revisão com ou sem acento."""
    import unicodedata

    sem_acentos = "".join(
        caractere for caractere in unicodedata.normalize("NFD", valor)
        if unicodedata.category(caractere) != "Mn"
    )
    return " ".join(sem_acentos.upper().split())


def _mapear_linhas(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mapeia as linhas e descarta as de siglas fora do mapa."""
    return [m for m in (_mapear_linha(r) for r in rows) if m is not None]


async def listar_solicitacoes(
    provider: SolicitacaoProviderInterface,
    limite: int = 100,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    tipo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista itens de exame de AP, filtrados por período e tipo, mais recentes primeiro.

    O `limite` conta solicitações distintas: todas as amostras de cada solicitação
    incluída são devolvidas, para que nenhuma solicitação venha cortada ao meio.
    """
    itens = _mapear_linhas(await provider.listar_solicitacoes())

    inicio = data_inicio.isoformat() if data_inicio else None
    fim = data_fim.isoformat() if data_fim else None

    def no_periodo(item: Dict[str, Any]) -> bool:
        """Verifica se a data da solicitação está no intervalo inclusivo informado."""
        if inicio is None and fim is None:
            return True
        dia = (item["dataSolicitacao"] or "")[:10]
        if not dia:
            return False
        return (inicio is None or dia >= inicio) and (fim is None or dia <= fim)

    filtrados = [
        i for i in itens
        if no_periodo(i) and (tipo is None or i["tipoExameSugerido"] == tipo)
    ]
    filtrados.sort(
        key=lambda i: (i["dataSolicitacao"] or "", i["codigoSolicitacao"], i["numeroAmostra"]),
        reverse=True,
    )
    codigos_incluidos: set = set()
    resultado: List[Dict[str, Any]] = []
    for item in filtrados:
        codigo = item["codigoSolicitacao"]
        if codigo not in codigos_incluidos:
            if len(codigos_incluidos) >= limite:
                continue
            codigos_incluidos.add(codigo)
        resultado.append(item)
    return resultado


async def obter_solicitacao(
    codigo: str,
    provider: SolicitacaoProviderInterface,
) -> List[Dict[str, Any]]:
    """Retorna os itens de exame de AP de uma solicitação ou 404 se não houver.

    `codigo` pode ser o código da solicitação (todas as amostras) ou o id
    composto `<codigoSolicitacao>-<numeroAmostra>` (apenas aquela amostra).
    """
    codigo_solicitacao, numero_amostra = _separar_id(codigo)
    itens = _mapear_linhas(await provider.obter_itens_por_codigo(codigo_solicitacao))
    if numero_amostra is not None:
        itens = [i for i in itens if i["numeroAmostra"] == numero_amostra]
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitação {codigo} não encontrada.",
        )
    return itens
