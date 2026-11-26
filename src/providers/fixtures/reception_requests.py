"""Dados inteiramente fictícios para o provider de solicitações em desenvolvimento."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def carregar_estado_demo() -> dict:
    """Carrega a carga de demonstração mesclando os cenários multi-amostra."""
    caminho = Path(__file__).with_name("reception_demo.json")
    with caminho.open(encoding="utf-8") as arquivo:
        estado = json.load(arquivo)

    solicitacoes = estado.setdefault("solicitacoes", [])
    ids_existentes = {item["id"] for item in solicitacoes}
    por_codigo = {item["codigoSolicitacao"]: item for item in solicitacoes}

    for grupo in solicitacoes_ficticias():
        if grupo["id"] in ids_existentes:
            continue
        base = por_codigo.get(grupo["codigoSolicitacao"])
        if base:
            for campo in (
                "prontuario",
                "nomePaciente",
                "dataNascimento",
                "origem",
                "unidade",
                "especialidade",
                "dataSolicitacao",
            ):
                if campo in base:
                    grupo[campo] = base[campo]
        solicitacoes.append(grupo)
        ids_existentes.add(grupo["id"])

    return estado


def solicitacoes_ficticias() -> list[dict[str, Any]]:
    """Cria grupos fictícios realistas no contrato SolicitacaoAghu usado pela Recepção."""
    agora = datetime.now(timezone.utc)

    def data(horas_atras: float) -> str:
        return (agora - timedelta(hours=horas_atras)).isoformat()

    def grupo(
        codigo: str,
        tipo: str,
        amostras: list[tuple[str, str]],
        horas: float,
        **dados: str,
    ) -> dict:
        """Monta uma solicitação agrupada por tipo de exame."""
        siglas = {"HP": "APECR", "CG": "CITOP", "CCV": "CCVM", "CO": "CONGE", "IHQ": "IMUHI"}
        nomes = {
            "HP": "Anatomopatológico",
            "CG": "Citopatológico",
            "CCV": "Citopatológico cérvico-vaginal",
            "CO": "Exame transoperatório de congelação",
            "IHQ": "Imuno-histoquímica",
        }
        sigla = siglas[tipo]
        return {
            "id": f"{codigo}:{tipo}",
            "codigoSolicitacao": codigo,
            "prontuario": dados["prontuario"],
            "nomePaciente": dados["nomePaciente"],
            "dataNascimento": dados["dataNascimento"],
            "origem": dados["origem"],
            "unidade": dados["unidade"],
            "especialidade": dados["especialidade"],
            "dataSolicitacao": data(horas),
            "siglaExame": sigla,
            "nomeExame": nomes[tipo],
            "tipoExameSugerido": tipo,
            "informacoesClinicas": dados.get(
                "informacoesClinicas",
                "Investigação diagnóstica – material encaminhado ao SAP.",
            ),
            "amostras": [
                {
                    "numeroAmostra": numero,
                    "siglaExame": sigla,
                    "nomeExame": nomes[tipo],
                    "descricaoMaterial": material,
                    "codStatusItem": "AC",
                    "statusItemDescricao": "A COLETAR",
                }
                for numero, material in amostras
            ],
            "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO",
        }

    pac_antonio = {
        "prontuario": "23901148",
        "nomePaciente": "ANTÔNIO CARLOS CAVALCANTI",
        "dataNascimento": "1962-11-27",
        "origem": "AMBULATORIO",
        "unidade": "Ambulatório de Gastroenterologia",
        "especialidade": "Gastroenterologia",
        "informacoesClinicas": "Dispepsia com lesão ulcerada em esôfago distal e ascite a esclarecer.",
    }
    pac_osvaldo = {
        "prontuario": "23928435",
        "nomePaciente": "OSVALDO FERRAZ LIMEIRA",
        "dataNascimento": "1965-10-10",
        "origem": "CIRURGIA",
        "unidade": "Bloco Cirúrgico Central – Sala 5",
        "especialidade": "Cirurgia Geral",
        "informacoesClinicas": "Lesão nodular em segmento IV hepático identificada no intraoperatório.",
    }
    pac_marlene = {
        "prontuario": "23941029",
        "nomePaciente": "MARLENE VASCONCELOS DE SOUZA",
        "dataNascimento": "1969-09-23",
        "origem": "AMBULATORIO",
        "unidade": "Ambulatório de Oncologia",
        "especialidade": "Oncologia – Mastologia",
        "informacoesClinicas": "Nódulo suspeito em QSE de mama esquerda (BI-RADS 4C).",
    }
    return [
        grupo("7712301", "HP", [("1", "BIÓPSIA DE ESÔFAGO DISTAL")], 5, **pac_antonio),
        grupo("7712301", "CG", [("2", "LÍQUIDO ASCÍTICO")], 5, **pac_antonio),
        grupo(
            "7712318",
            "CG",
            [("1", "LÍQUIDO PERITONEAL")],
            4,
            prontuario="23915602",
            nomePaciente="SEVERINO RAMOS DA SILVA",
            dataNascimento="1954-02-04",
            origem="INTERNACAO",
            unidade="Enfermaria de Cirurgia – 8º Norte",
            especialidade="Cirurgia Geral",
            informacoesClinicas="Derrame peritoneal em pós-operatório tardio; pesquisa de células neoplásicas.",
        ),
        grupo(
            "7712325",
            "CCV",
            [("1", "ESFREGAÇO CÉRVICO-VAGINAL")],
            3,
            prontuario="23920074",
            nomePaciente="JANDIRA NOVAES COELHO",
            dataNascimento="1983-05-19",
            origem="EXTERNO",
            unidade="UBS Jardim das Acácias",
            especialidade="Ginecologia",
            informacoesClinicas="Rastreamento citológico preventivo de rotina.",
        ),
        grupo("7712340", "CO", [("1", "NÓDULO HEPÁTICO – PEÇA INTRAOPERATÓRIA")], 1, **pac_osvaldo),
        grupo(
            "7712340",
            "HP",
            [
                ("2", "NÓDULO HEPÁTICO – SEGMENTO IV (PEÇA DEFINITIVA)"),
                ("3", "VESÍCULA BILIAR – COLECISTECTOMIA"),
            ],
            1,
            **pac_osvaldo,
        ),
        grupo(
            "7712356",
            "IHQ",
            [("1", "BLOCO A – BIÓPSIA GÁSTRICA (AMPLIAÇÃO DE PAINEL)")],
            2,
            prontuario="23155281",
            nomePaciente="NEIDE CAMPELO SARMENTO",
            dataNascimento="1972-06-25",
            origem="AMBULATORIO",
            unidade="Serviço de Anatomia Patológica",
            especialidade="Gastroenterologia",
            informacoesClinicas="Complementação imuno-histoquímica para definição de histogênese.",
        ),
        grupo("7712385", "HP", [("1", "BIÓPSIA DE MAMA ESQUERDA – CORE BIOPSY")], 2, **pac_marlene),
        grupo(
            "7712385",
            "IHQ",
            [("2", "PAINEL PROGNÓSTICO DE MAMA (RE, RP, HER2, KI-67)")],
            2,
            **pac_marlene,
        ),
        grupo(
            "7712390",
            "HP",
            [(str(i), f"BIÓPSIA PROSTÁTICA – FRAGMENTO {i:02d}") for i in range(1, 13)],
            1,
            prontuario="23958816",
            nomePaciente="SEBASTIÃO GOMES DA SILVA",
            dataNascimento="1951-02-10",
            origem="AMBULATORIO",
            unidade="Ambulatório de Urologia",
            especialidade="Urologia",
            informacoesClinicas="PSA elevado (9,4 ng/mL); mapeamento prostático em 12 sextantes.",
        ),
    ]
