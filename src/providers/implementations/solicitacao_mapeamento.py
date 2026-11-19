"""Converte as linhas da view de solicitações do AGHU no formato usado pelo sistema."""
import re
from datetime import date, datetime
from typing import Any, Dict, List, Mapping, Optional

# Colunas da vw_solicitacao, uma linha por amostra.
COLUNAS_VIEW = (
    "codigo_solicitacao",
    "numero_amostra",
    "cod_status_item",
    "status_item_exame",
    "data_solicitacao",
    "nome_paciente",
    "data_nascimento",
    "prontuario",
    "especialidade",
    "convenio",
    "origem",
    "unidade",
    "codigo_lab",
    "informacoes_clinica",
    "sigla_exame",
    "nome_exame",
    "descricao_material",
)

FORMATO_DATA_AGHU = "%d/%m/%Y"
# O AGHU traz caracteres invisíveis, que quebrariam comparações e filtros por andar.
_CARACTERES_INVISIVEIS = re.compile("[​‌‍⁠﻿]")
_ESPACOS = re.compile(r"\s+")


def limpar_texto(valor: Any) -> str:
    """Remove caracteres invisíveis e espaços repetidos ou nas bordas."""
    if valor is None:
        return ""
    texto = _CARACTERES_INVISIVEIS.sub("", str(valor))
    return _ESPACOS.sub(" ", texto).strip()


def limpar_texto_com_linhas(valor: Any) -> str:
    """Limpa cada linha do texto clínico, preservando as quebras e removendo linhas vazias."""
    if valor is None:
        return ""
    linhas = (limpar_texto(linha) for linha in str(valor).splitlines())
    return "\n".join(linha for linha in linhas if linha)


def _texto_ou_nulo(valor: Any) -> Optional[str]:
    """Limpa o texto e converte o vazio em None."""
    return limpar_texto(valor) or None


def converter_data(valor: Any) -> Optional[str]:
    """Converte uma data do AGHU (`DD/MM/AAAA` ou tipo date) em `AAAA-MM-DD`; inválida vira None."""
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    texto = limpar_texto(valor)
    if not texto:
        return None
    try:
        return datetime.strptime(texto, FORMATO_DATA_AGHU).date().isoformat()
    except ValueError:
        return None


def _item(linha: Mapping[str, Any]) -> Dict[str, Any]:
    """Converte uma linha da view em uma amostra da solicitação."""
    return {
        "numero_amostra": int(limpar_texto(linha["numero_amostra"])),
        "codigo_lab": limpar_texto(linha["codigo_lab"]),
        "sigla_exame": limpar_texto(linha["sigla_exame"]),
        "nome_exame": limpar_texto(linha["nome_exame"]),
        "descricao_material": _texto_ou_nulo(linha["descricao_material"]),
        "cod_status_item": limpar_texto(linha["cod_status_item"]),
        "status_item_exame": limpar_texto(linha["status_item_exame"]),
    }


def montar_solicitacao(linhas: List[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """Agrupa as linhas de uma solicitação. Os dados do paciente se repetem em cada linha."""
    if not linhas:
        return None
    primeira = linhas[0]
    return {
        "codigo": limpar_texto(primeira["codigo_solicitacao"]),
        "data_solicitacao": converter_data(primeira["data_solicitacao"]),
        "nome_paciente": limpar_texto(primeira["nome_paciente"]),
        "data_nascimento": converter_data(primeira["data_nascimento"]),
        "prontuario": _texto_ou_nulo(primeira["prontuario"]),
        "especialidade": _texto_ou_nulo(primeira["especialidade"]),
        "convenio": _texto_ou_nulo(primeira["convenio"]),
        "origem": limpar_texto(primeira["origem"]),
        "unidade": _texto_ou_nulo(primeira["unidade"]),
        "informacoes_clinica": limpar_texto_com_linhas(primeira["informacoes_clinica"]) or None,
        "itens": sorted(
            (_item(linha) for linha in linhas), key=lambda item: item["numero_amostra"]
        ),
    }
