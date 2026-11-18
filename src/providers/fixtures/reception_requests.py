"""Dados inteiramente fictícios para o provider de solicitações em desenvolvimento."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def carregar_estado_demo() -> dict:
    """Carrega a mesma carga de demonstração que o módulo AP já usava no frontend."""
    caminho = Path(__file__).with_name("reception_demo.json")
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def solicitacoes_ficticias() -> list[dict[str, Any]]:
    """Cria grupos fictícios no contrato SolicitacaoAghu usado pela Recepção."""
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
            "informacoesClinicas": "Dados fictícios para desenvolvimento.",
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

    alfa = {
        "prontuario": "2390114",
        "nomePaciente": "PACIENTE FICTÍCIO ALFA",
        "dataNascimento": "1962-11-27",
        "origem": "AMBULATORIO",
        "unidade": "Ambulatório de Gastroenterologia",
        "especialidade": "Gastroenterologia",
    }
    return [
        grupo("7712301", "HP", [("1", "BIÓPSIA DE ESÔFAGO DISTAL")], 5, **alfa),
        grupo("7712301", "CG", [("2", "LÍQUIDO PERITONEAL")], 5, **alfa),
        grupo("7712318", "CG", [("1", "LÍQUIDO PERITONEAL")], 4,
              prontuario="2391560", nomePaciente="PACIENTE FICTÍCIO BETA", dataNascimento="1954-02-04",
              origem="INTERNACAO", unidade="Enfermaria de Cirurgia", especialidade="Cirurgia Geral"),
        grupo("7712325", "CCV", [("1", "ESFREGAÇO CÉRVICO-VAGINAL")], 3,
              prontuario="2392007", nomePaciente="PACIENTE FICTÍCIO GAMA", dataNascimento="1983-05-19",
              origem="EXTERNO", unidade="UBS fictícia Jardim das Acácias", especialidade="Ginecologia"),
        grupo("7712340", "CO", [("1", "NÓDULO HEPÁTICO – PEÇA INTRAOPERATÓRIA")], 1,
              prontuario="2392843", nomePaciente="PACIENTE FICTÍCIO DELTA", dataNascimento="1965-10-10",
              origem="CIRURGIA", unidade="Bloco Cirúrgico Central – Sala 5", especialidade="Cirurgia Geral"),
        grupo("7712356", "IHQ", [("1", "BLOCO A – CASO FICTÍCIO (AMPLIAÇÃO DE PAINEL)")], 2,
              prontuario="2315528", nomePaciente="PACIENTE FICTÍCIO ÉPSILON", dataNascimento="1972-06-25",
              origem="AMBULATORIO", unidade="Serviço de Anatomia Patológica", especialidade="Gastroenterologia"),
    ]
