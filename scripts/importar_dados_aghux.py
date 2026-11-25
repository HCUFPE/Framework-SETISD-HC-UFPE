"""Importa o export CSV do AGHUX para o fixture de mocks do frontend.

O arquivo de apoio usa CSV em dois níveis: cada linha é um único campo CSV que,
por sua vez, contém a linha real com aspas duplicadas. Por isso é necessário
passar ``csv.reader`` duas vezes. Nenhuma dependência externa é necessária.

Uso:
    python scripts/importar_dados_aghux.py
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
CSV_PADRAO = next(
    (RAIZ / "Documentos de Apoio").glob("_SELECT_Dados_do_Paciente_*.csv"),
    RAIZ / "Documentos de Apoio" / "dados_aghux.csv",
)
SAIDA_PADRAO = RAIZ / "frontend" / "src" / "mocks" / "dadosAghux.json"

CAMPOS = (
    "prontuario",
    "nome",
    "telefone",
    "cidade",
    "estado",
    "codigo_solicitacao",
    "data_solicitao",
    "unidade_solicitante",
    "codigo_exame",
    "nome_exame",
    "id_funcionario",
    "nome_funcionario",
)


def _linha_csv(linha: str) -> list[str]:
    """Decodifica uma linha do export (aspas externas + aspas internas)."""
    externo = next(csv.reader([linha]))
    return next(csv.reader(externo))


def _iso(valor: str) -> str:
    """Converte 'AAAA-MM-DD HH:MM:SS.mmm' para ISO local sem fuso."""
    return datetime.fromisoformat(valor.strip().replace(" ", "T")).isoformat(timespec="milliseconds")


def tipo_exame(unidade: str) -> str:
    """Classifica a unidade solicitante em uma categoria legível para filtros."""
    normalizada = unidade.upper()
    if "MEDICINA NUCLEAR" in normalizada:
        return "Medicina Nuclear"
    if "FONOAUDIOLOGIA" in normalizada:
        return "Fonoaudiologia"
    if any(termo in normalizada for termo in (
        "ULTRASSONOGRAFIA", "MAMOGRAFIA", "DENSITOMETRIA", "RADIOLOGIA",
        "TOMOGRAFIA", "RESSON", "UDI",
    )):
        return "Imagem"
    return "Outro"


def importar(caminho_csv: Path) -> dict[str, Any]:
    """Lê o CSV e devolve o documento JSON com solicitações agrupadas."""
    linhas = caminho_csv.read_text(encoding="utf-8-sig").splitlines()
    cabecalho = _linha_csv(linhas[0])
    if cabecalho != list(CAMPOS):
        raise ValueError(f"Cabeçalho inesperado no CSV: {cabecalho}")

    registros = [dict(zip(cabecalho, _linha_csv(linha))) for linha in linhas[1:] if linha.strip()]
    grupos: dict[str, dict[str, Any]] = {}

    for registro in registros:
        codigo = registro["codigo_solicitacao"].strip()
        if not codigo:
            continue
        solicitacao = grupos.setdefault(codigo, {
            "codigoSolicitacao": codigo,
            "prontuario": registro["prontuario"].strip(),
            "nome": registro["nome"].strip(),
            "telefone": registro["telefone"].strip(),
            "cidade": registro["cidade"].strip(),
            "estado": registro["estado"].strip(),
            "dataSolicitacao": _iso(registro["data_solicitao"]),
            "unidadeSolicitante": registro["unidade_solicitante"].strip(),
            "tipoExame": tipo_exame(registro["unidade_solicitante"]),
            "solicitante": {
                "codigo": registro["id_funcionario"].strip(),
                "nome": registro["nome_funcionario"].strip(),
            },
            "itens": [],
        })
        solicitacao["dataSolicitacao"] = min(
            solicitacao["dataSolicitacao"], _iso(registro["data_solicitao"])
        )
        solicitacao["itens"].append({
            "codigoExame": registro["codigo_exame"].strip(),
            "nomeExame": registro["nome_exame"].strip(),
        })

    solicitacoes = sorted(
        grupos.values(), key=lambda item: item["dataSolicitacao"], reverse=True
    )
    return {
        "fonte": str(caminho_csv.relative_to(RAIZ)),
        "referenciaEm": max(item["dataSolicitacao"] for item in solicitacoes),
        "totalRegistros": len(registros),
        "totalSolicitacoes": len(solicitacoes),
        "solicitacoes": solicitacoes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=CSV_PADRAO, help="Export CSV do AGHUX")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="Arquivo JSON gerado")
    args = parser.parse_args()

    documento = importar(args.csv.resolve())
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(
        json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"{documento['totalRegistros']} registros -> "
        f"{documento['totalSolicitacoes']} solicitações | "
        f"referência {documento['referenciaEm']} | {args.saida}"
    )


if __name__ == "__main__":
    main()
