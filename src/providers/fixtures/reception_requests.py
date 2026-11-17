"""Dados inteiramente fictícios para o provider de solicitações em desenvolvimento."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def carregar_estado_demo() -> dict:
    """Carrega a mesma carga de demonstração que o módulo AP já usava no frontend."""
    caminho = Path(__file__).with_name("reception_demo.json")
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def solicitacoes_ficticias() -> list[dict[str, str]]:
    """Cria a fixture compatível com o contrato SolicitacaoAghu do frontend."""
    agora = datetime.now(timezone.utc)

    def data(horas_atras: float) -> str:
        return (agora - timedelta(hours=horas_atras)).isoformat()

    base = {
        "situacaoRecepcao": "AGUARDANDO_RECEBIMENTO",
        "statusAghuDescricao": "Solicitado",
    }
    return [
        {
            **base,
            "codigoSolicitacao": "7712301",
            "prontuario": "2390114",
            "nomePaciente": "PACIENTE FICTÍCIO ALFA",
            "dataNascimento": "1962-11-27",
            "sexo": "Masculino",
            "origem": "AMBULATORIO",
            "unidade": "Ambulatório de Gastroenterologia",
            "especialidade": "Gastroenterologia",
            "nomeSolicitante": "Dr. Solicitante Fictício",
            "dataSolicitacao": data(5),
            "siglaExame": "AP",
            "nomeExame": "Exame anatomopatológico",
            "tipoExameSugerido": "HP",
            "descricaoMaterial": "BIÓPSIA DE ESÔFAGO DISTAL",
            "informacoesClinicas": "Dados fictícios para desenvolvimento.",
        },
        {
            **base,
            "codigoSolicitacao": "7712318",
            "prontuario": "2391560",
            "nomePaciente": "PACIENTE FICTÍCIO BETA",
            "dataNascimento": "1954-02-04",
            "sexo": "Masculino",
            "origem": "INTERNACAO",
            "unidade": "Enfermaria de Cirurgia",
            "especialidade": "Cirurgia Geral",
            "nomeSolicitante": "Dra. Solicitante Fictícia",
            "dataSolicitacao": data(4),
            "siglaExame": "CITO",
            "nomeExame": "Citologia geral (líquidos e PAAF)",
            "tipoExameSugerido": "CG",
            "descricaoMaterial": "LÍQUIDO PERITONEAL",
            "informacoesClinicas": "Dados fictícios para desenvolvimento.",
        },
        {
            **base,
            "codigoSolicitacao": "7712325",
            "prontuario": "2392007",
            "nomePaciente": "PACIENTE FICTÍCIO GAMA",
            "dataNascimento": "1983-05-19",
            "sexo": "Feminino",
            "origem": "EXTERNO",
            "unidade": "UBS fictícia Jardim das Acácias",
            "especialidade": "Ginecologia",
            "nomeSolicitante": "Dra. Solicitante Fictícia",
            "dataSolicitacao": data(3),
            "siglaExame": "CCV",
            "nomeExame": "Citologia oncótica cérvico-vaginal",
            "tipoExameSugerido": "CCV",
            "descricaoMaterial": "ESFREGAÇO CÉRVICO-VAGINAL",
            "informacoesClinicas": "Dados fictícios para desenvolvimento.",
        },
        {
            **base,
            "codigoSolicitacao": "7712340",
            "prontuario": "2392843",
            "nomePaciente": "PACIENTE FICTÍCIO DELTA",
            "dataNascimento": "1965-10-10",
            "sexo": "Masculino",
            "origem": "BLOCO_CIRURGICO",
            "unidade": "Bloco Cirúrgico Central – Sala 5",
            "especialidade": "Cirurgia Geral",
            "nomeSolicitante": "Dr. Solicitante Fictício",
            "dataSolicitacao": data(1),
            "siglaExame": "CONG",
            "nomeExame": "Exame anatomopatológico por congelação",
            "tipoExameSugerido": "CO",
            "descricaoMaterial": "NÓDULO HEPÁTICO – PEÇA INTRAOPERATÓRIA",
            "informacoesClinicas": "Dados fictícios para desenvolvimento.",
        },
        {
            **base,
            "codigoSolicitacao": "7712356",
            "prontuario": "2315528",
            "nomePaciente": "PACIENTE FICTÍCIO ÉPSILON",
            "dataNascimento": "1972-06-25",
            "sexo": "Feminino",
            "origem": "AMBULATORIO",
            "unidade": "Serviço de Anatomia Patológica",
            "especialidade": "Gastroenterologia",
            "nomeSolicitante": "Dr. Solicitante Fictício",
            "dataSolicitacao": data(2),
            "siglaExame": "IHQ",
            "nomeExame": "Imuno-histoquímica",
            "tipoExameSugerido": "IHQ",
            "descricaoMaterial": "BLOCO A – CASO FICTÍCIO (AMPLIAÇÃO DE PAINEL)",
            "informacoesClinicas": "Solicitação fictícia para validar leitura; vínculo de IHQ depende de permissão SAP/HC.",
        },
    ]
