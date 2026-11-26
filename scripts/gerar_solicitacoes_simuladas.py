"""Gera solicitações simuladas recentes para o fixture de demonstração.

Os registros derivados do export real do AGHUX terminam em 28/09/2026. Para que
a fila e a agenda possam ser exercitadas como em uma operação corrente, este
script acrescenta solicitações fictícias ancoradas em uma data de referência
próxima à atual (por padrão, 25/11/2026). A aleatoriedade usa semente fixa, de
modo que o fixture seja reproduzível; nenhum CPF, CNS ou endereço é criado.

Uso:
    python scripts/gerar_solicitacoes_simuladas.py
    python scripts/gerar_solicitacoes_simuladas.py --quantidade 12 --referencia 2026-11-25T16:05:34.227
"""

from __future__ import annotations

import argparse
import json
import random
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

from importar_dados_aghux import RAIZ, tipo_exame

FIXTURA_PADRAO = RAIZ / "frontend" / "src" / "mocks" / "dadosAghux.json"
PREFIXO_CODIGO = "SIM-"
REFERENCIA_PADRAO = "2026-11-25T16:05:34.227"
SEED_PADRAO = 20261125
QUANTIDADE_PADRAO = 30
HORAS_JANELA = 24 * 10

NOMES = (
    "Ana", "Bruno", "Carla", "Diego", "Elena", "Felipe", "Gabriela", "Hugo",
    "Isabela", "João", "Larissa", "Marcelo", "Natália", "Otávio", "Paula", "Rafael",
)
SOBRENOMES = (
    "Almeida", "Barbosa", "Carvalho", "Dias", "Ferreira", "Gomes", "Lima",
    "Moraes", "Nogueira", "Oliveira", "Pereira", "Ribeiro", "Santos", "Teixeira",
)


def eh_sintetica(solicitacao: Dict[str, Any]) -> bool:
    """Identifica uma solicitação criada por este gerador."""
    return str(solicitacao.get("codigoSolicitacao", "")).startswith(PREFIXO_CODIGO)


def extrair_sinteticas(documento: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Devolve as solicitações simuladas já presentes no fixture."""
    return [item for item in documento.get("solicitacoes", []) if eh_sintetica(item)]


def carregar(caminho: Path) -> Dict[str, Any]:
    """Lê o fixture JSON."""
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar(documento: Dict[str, Any], caminho: Path) -> None:
    """Grava o fixture JSON com indentação estável."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


EXAMES_SIMULADOS: Dict[str, str] = {
    "COLON": "Colonoscopia",
    "DESITO": "Desitometria",
    "ECO": "Ecocardiograma",
    "ENDO": "Endoscopia",
    "OFTA": "Exames de oftalmologia",
    "MAMO": "Mamografia",
    "RX": "Raio X",
    "ERGO": "Teste ergométrico",
    "US": "Ultrassonografias (inclusive com Doppler)",
}


def _catalogos(reais: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, str], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Extrai unidades, exames, solicitantes e cidades do export real."""
    unidades = sorted({
        str(item["unidadeSolicitante"]).strip()
        for item in reais if str(item.get("unidadeSolicitante", "")).strip()
    })
    exames: Dict[str, str] = {}
    for item in reais:
        for exame in item.get("itens", []):
            codigo = str(exame.get("codigoExame", "")).strip()
            if codigo:
                exames.setdefault(codigo, str(exame.get("nomeExame", "")).strip())
    # Acrescenta exames de demonstração para compor os filtros e a agenda simulada.
    exames.update(EXAMES_SIMULADOS)
    solicitantes = sorted({
        (str(item["solicitante"]["codigo"]).strip(), str(item["solicitante"]["nome"]).strip())
        for item in reais if item.get("solicitante", {}).get("codigo")
    })
    cidades = sorted({
        (str(item.get("cidade", "")).strip(), str(item.get("estado", "")).strip())
        for item in reais if item.get("cidade")
    })
    return unidades, exames, solicitantes, cidades


def compor(
    reais: List[Dict[str, Any]],
    sinteticas: List[Dict[str, Any]],
    total_registros_reais: int,
    referencia: str | None = None,
) -> Dict[str, Any]:
    """Recompõe o documento com contagens e referência derivadas dos registros."""
    solicitacoes = sorted(
        [*reais, *sinteticas],
        key=lambda item: str(item.get("dataSolicitacao", "")),
        reverse=True,
    )
    referencia_em = max(str(item["dataSolicitacao"]) for item in solicitacoes)
    if referencia:
        referencia_em = max(referencia_em, referencia)
    return {
        "fonte": "",
        "referenciaEm": referencia_em,
        "totalRegistros": total_registros_reais + sum(len(item.get("itens", [])) for item in sinteticas),
        "totalSolicitacoes": len(solicitacoes),
        "solicitacoes": solicitacoes,
    }


def gerar(
    documento: Dict[str, Any],
    quantidade: int = QUANTIDADE_PADRAO,
    referencia: str = REFERENCIA_PADRAO,
    seed: int = SEED_PADRAO,
) -> Dict[str, Any]:
    """Substitui as solicitações simuladas por um lote novo e determinístico."""
    if quantidade < 0:
        raise ValueError("A quantidade de solicitações não pode ser negativa.")
    rng = random.Random(seed)
    referencia_dt = datetime.fromisoformat(referencia)

    reais = [item for item in documento.get("solicitacoes", []) if not eh_sintetica(item)]
    antigas = extrair_sinteticas(documento)
    unidades, exames, solicitantes, cidades = _catalogos(reais)
    if not unidades or not exames:
        raise ValueError("O fixture de origem não possui unidades/exames para compor a simulação.")

    codigos_exames = list(exames.keys())
    sinteticas: List[Dict[str, Any]] = []
    prontuarios: set[str] = set()
    for indice in range(1, quantidade + 1):
        prontuario = f"SIM{rng.randint(10_000_000, 99_999_999)}"
        while prontuario in prontuarios:
            prontuario = f"SIM{rng.randint(10_000_000, 99_999_999)}"
        prontuarios.add(prontuario)

        data = referencia_dt - timedelta(hours=rng.randint(1, HORAS_JANELA))
        unidade = rng.choice(unidades)
        codigo_solicitante, nome_solicitante = rng.choice(solicitantes)
        cidade, estado = rng.choice(cidades)
        itens_selecionados = rng.sample(
            codigos_exames, k=min(rng.randint(1, 3), len(codigos_exames))
        )
        sinteticas.append({
            "codigoSolicitacao": f"{PREFIXO_CODIGO}{referencia[:10].replace('-', '')}-{indice:03d}",
            "prontuario": prontuario,
            "nome": f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)} (SIMULAÇÃO)",
            "telefone": f"(81) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}",
            "cidade": cidade,
            "estado": estado,
            "dataSolicitacao": data.isoformat(timespec="milliseconds"),
            "unidadeSolicitante": unidade,
            "tipoExame": tipo_exame(unidade),
            "solicitante": {"codigo": codigo_solicitante, "nome": nome_solicitante},
            "itens": [
                {"codigoExame": codigo, "nomeExame": exames[codigo]}
                for codigo in itens_selecionados
            ],
        })

    total_registros_reais = max(
        0,
        int(documento.get("totalRegistros", 0)) - sum(len(item.get("itens", [])) for item in antigas),
    )
    resultado = compor(reais, sinteticas, total_registros_reais, referencia)
    resultado["fonte"] = documento.get("fonte", "")
    return resultado


def mesclar_sinteticas(
    documento_real: Dict[str, Any], documento_existente: Dict[str, Any]
) -> Dict[str, Any]:
    """Reaproveita as solicitações simuladas ao reimportar o CSV do AGHUX."""
    sinteticas = extrair_sinteticas(documento_existente)
    if not sinteticas:
        return documento_real
    resultado = compor(
        list(documento_real.get("solicitacoes", [])),
        sinteticas,
        int(documento_real.get("totalRegistros", 0)),
        str(documento_existente.get("referenciaEm", "")) or None,
    )
    resultado["fonte"] = documento_real.get("fonte", "")
    return resultado


def main() -> None:
    """Aplica o gerador ao fixture e imprime um resumo da operação."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=FIXTURA_PADRAO, help="Fixture atual")
    parser.add_argument("--saida", type=Path, default=FIXTURA_PADRAO, help="Fixture gerado")
    parser.add_argument("--quantidade", type=int, default=QUANTIDADE_PADRAO, help="Quantidade de solicitações simuladas")
    parser.add_argument("--referencia", default=REFERENCIA_PADRAO, help="Data/hora de referência ISO local")
    parser.add_argument("--seed", type=int, default=SEED_PADRAO, help="Semente do gerador aleatório")
    args = parser.parse_args()

    documento = gerar(
        carregar(args.entrada.resolve()),
        quantidade=args.quantidade,
        referencia=args.referencia,
        seed=args.seed,
    )
    salvar(documento, args.saida.resolve())
    print(
        f"{documento['totalSolicitacoes']} solicitações "
        f"({args.quantidade} simuladas até {documento['referenciaEm']}) | {args.saida}"
    )


if __name__ == "__main__":
    main()
