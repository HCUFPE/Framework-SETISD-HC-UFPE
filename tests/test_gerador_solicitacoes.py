"""Testes do gerador de solicitações simuladas do fixture de demonstração."""

import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_solicitacoes_simuladas as gerador  # noqa: E402

FIXTURA = RAIZ / "frontend" / "src" / "mocks" / "dadosAghux.json"
REFERENCIA = "2026-11-25T16:05:34.227"
CAMPOS_ESPERADOS = {
    "codigoSolicitacao", "prontuario", "nome", "telefone", "cidade", "estado",
    "dataSolicitacao", "unidadeSolicitante", "tipoExame", "solicitante", "itens",
}


def test_gerador_substitui_lote_e_mantem_referencia():
    """O lote é determinístico, recente e não introduz dados sensíveis."""
    documento = json.loads(FIXTURA.read_text(encoding="utf-8"))

    resultado = gerador.gerar(documento, quantidade=6, referencia=REFERENCIA)
    sinteticas = gerador.extrair_sinteticas(resultado)

    assert len(sinteticas) == 6
    assert resultado["referenciaEm"] == REFERENCIA
    assert resultado["totalSolicitacoes"] == len(resultado["solicitacoes"])
    assert all(set(item) == CAMPOS_ESPERADOS for item in sinteticas)
    assert all(item["dataSolicitacao"] <= REFERENCIA for item in sinteticas)
    limite = datetime.fromisoformat(REFERENCIA) - gerador.timedelta(hours=gerador.HORAS_JANELA)
    assert all(datetime.fromisoformat(item["dataSolicitacao"]) >= limite for item in sinteticas)
    assert resultado == gerador.gerar(documento, quantidade=6, referencia=REFERENCIA)


def test_reimportacao_preserva_solicitacoes_simuladas():
    """Rodar o importador do CSV não apaga o cenário de demonstração."""
    existente = json.loads(FIXTURA.read_text(encoding="utf-8"))
    real = {
        "fonte": existente["fonte"],
        "referenciaEm": "2026-09-28T16:05:34.227",
        "totalRegistros": 576,
        "totalSolicitacoes": 493,
        "solicitacoes": [
            item for item in existente["solicitacoes"] if not gerador.eh_sintetica(item)
        ],
    }

    mesclado = gerador.mesclar_sinteticas(real, existente)

    assert len(gerador.extrair_sinteticas(mesclado)) == gerador.QUANTIDADE_PADRAO
    assert mesclado["referenciaEm"] == existente["referenciaEm"]
    assert mesclado["totalSolicitacoes"] == existente["totalSolicitacoes"]
    assert mesclado["totalRegistros"] == existente["totalRegistros"]
