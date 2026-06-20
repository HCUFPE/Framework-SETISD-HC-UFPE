"""
src/services/pontuacao.py

Módulo de priorização de solicitações de exame — CORTEx-HC.

Responsabilidade: receber dicionários com dados de paciente e solicitação e retornar uma pontuação numérica (0–100+). Não acessa banco, não faz chamadas HTTP. É chamado pelo controller após os providers buscarem os dados.

Contrato de entrada esperado pelo controller:

    paciente = {
        "cidade": str,           # ex: "Petrolina"
        "data_nascimento": str,  # ex: "1950-03-15" (ISO 8601)
    }

    solicitacao = {
        "data_retorno": str,          # ex: "2026-07-10" (ISO 8601)
        "unidade_solicitante": str,   # ex: "UTI ADULTO"
        "data_entrada_fila": str,     # ex: "2026-06-01" (ISO 8601)
    }
"""

from datetime import date, datetime

# ---------------------------------------------------------------------------
# Pesos — ajustar aqui após validação com a equipe do HC-UFPE
# ---------------------------------------------------------------------------

PESO_DATA_RETORNO      = 40
PESO_URGENCIA          = 30
PESO_LOCALIDADE        = 20
PESO_IDADE             = 10

BONUS_MAXIMO_ESPERA    = 20   # pontos extras máximos por tempo de espera
DIAS_ESPERA_MAXIMO     = 60   # dias para atingir o bônus máximo


# ---------------------------------------------------------------------------
# Mapa de urgência por unidade solicitante
# Fonte: validado com Tati (HC-UFPE) em reunião de 12/06/2026.
# Unidades não listadas recebem valor padrão (DEFAULT_URGENCIA).
# Atualizar conforme formalização com a equipe clínica.
# ---------------------------------------------------------------------------

MAPA_URGENCIA: dict[str, float] = {
    "UTI ADULTO":                  1.0,
    "UTI PEDIÁTRICA":              1.0,
    "CENTRO OBSTÉTRICO":           0.9,
    "PRONTO-SOCORRO":              0.9,
    "EMERGÊNCIA":                  0.9,
    "VASCULAR":                    0.8,
    "ONCOLOGIA":                   0.8,
    "NEFROLOGIA (AMBULATÓRIO)":    0.7,
    "CARDIOLOGIA (AMBULATÓRIO)":   0.65,
    "PNEUMOLOGIA (AMBULATÓRIO)":   0.55,
    "GINECOLOGIA (AMBULATÓRIO)":   0.5,
    "ORTOPEDIA (AMBULATÓRIO)":     0.5,
}

DEFAULT_URGENCIA = 0.4  # unidades não mapeadas


# ---------------------------------------------------------------------------
# Municípios de Pernambuco por faixa de distância ao HC-UFPE (Recife)
# Fonte: estimativa inicial — validar com equipe do HC.
# ---------------------------------------------------------------------------

MUNICIPIOS_REGIAO_METROPOLITANA = {
    "recife", "olinda", "caruaru", "jaboatão", "jaboatão dos guararapes",
    "paulista", "camaragibe", "são lourenço da mata", "abreu e lima",
    "igarassu", "cabo de santo agostinho", "ipojuca", "moreno",
}

MUNICIPIOS_INTERIOR_DISTANTE = {
    "petrolina", "araripina", "ouricuri", "salgueiro", "serra talhada",
    "floresta", "santa maria da boa vista", "lagoa grande", "orocó",
}

# Scores de localidade: quanto mais difícil chegar, menor a prioridade, para ficar para depois
SCORE_REGIAO_METROPOLITANA = 1.0
SCORE_INTERIOR_PROXIMO     = 0.6   # municípios do interior não listados acima
SCORE_INTERIOR_DISTANTE    = 0.2

# ---------------------------------------------------------------------------
# Transformacao da string para data
# ---------------------------------------------------------------------------

def _parse_date(valor: str) -> date:
    """Converte string ISO 8601 para objeto date."""
    return datetime.strptime(valor[:10], "%Y-%m-%d").date()

# ---------------------------------------------------------------------------
# Funções auxiliares de score (cada uma retorna valor entre 0.0 e 1.0)
# ---------------------------------------------------------------------------

def score_data_retorno(data_retorno_str: str, hoje: date | None = None) -> float:
    """
    Quanto mais próxima a data de retorno, maior o score.
    - 0 dias restantes (atrasado ou hoje) → 1.0
    - 90 dias ou mais                     → 0.0
    """
    if hoje is None:
        hoje = date.today() # biblioteca padrão do Python que retorna a data atual do servidor

    try:
        data_retorno = _parse_date(data_retorno_str)
    except (ValueError, TypeError):
        return 0.0

    dias_restantes = (data_retorno - hoje).days
    if dias_restantes <= 0:
        return 1.0
    return max(0.0, 1.0 - (dias_restantes / 90))


def score_urgencia(unidade_solicitante: str) -> float:
    """
    Score baseado na unidade que originou a solicitação.
    !!!!!!!!!!!! Unidades não mapeadas recebem DEFAULT_URGENCIA.
    """
    if not unidade_solicitante:
        return DEFAULT_URGENCIA
    chave = unidade_solicitante.strip().upper()
    return MAPA_URGENCIA.get(chave, DEFAULT_URGENCIA)


def score_localidade(cidade: str) -> float:
    """
    Pacientes de municípios distantes têm maior dificuldade de deslocamento,
    portanto recebem score menos alto para evitar perda de vagas pela falta de planejamento.
    """
    if not cidade:
        return SCORE_INTERIOR_PROXIMO

    cidade_normalizada = cidade.strip().lower()

    if cidade_normalizada in MUNICIPIOS_REGIAO_METROPOLITANA:
        return SCORE_REGIAO_METROPOLITANA
    if cidade_normalizada in MUNICIPIOS_INTERIOR_DISTANTE:
        return SCORE_INTERIOR_DISTANTE
    return SCORE_INTERIOR_PROXIMO


def score_idade(data_nascimento_str: str, hoje: date | None = None) -> float:
    """
    Fator auxiliar de baixo peso. Pacientes mais velhos recebem leve
    incremento. Score proporcional até 90 anos (1.0 a partir daí).
    """
    if hoje is None:
        hoje = date.today()

    try:
        nascimento = _parse_date(data_nascimento_str)
    except (ValueError, TypeError):
        return 0.0

    idade = (hoje - nascimento).days // 365
    return min(1.0, idade / 90)


def bonus_tempo_espera(data_entrada_fila_str: str, hoje: date | None = None) -> float:
    """
    Bônus adicional (não normalizado) que cresce com o tempo de espera.
    Evita que um paciente fique indefinidamente despriorizado.

    Retorna entre 0 e BONUS_MAXIMO_ESPERA pontos.
    """
    if hoje is None:
        hoje = date.today()

    try:
        data_entrada = _parse_date(data_entrada_fila_str)
    except (ValueError, TypeError):
        return 0.0

    dias_esperando = (hoje - data_entrada).days
    proporcao = min(1.0, dias_esperando / DIAS_ESPERA_MAXIMO)
    return proporcao * BONUS_MAXIMO_ESPERA


# ---------------------------------------------------------------------------
# Função principal de pontuação
# ---------------------------------------------------------------------------

def calcular_pontuacao(paciente: dict, solicitacao: dict) -> float:
    """
    Calcula a pontuação de prioridade de uma solicitação.

    Quanto maior o valor retornado, maior a prioridade na fila.
    Pontuação base: 0-100. Bônus de tempo de espera pode ultrapassar 100.

    Args:
        paciente:    dict com "cidade" e "data_nascimento"
        solicitacao: dict com "data_retorno", "unidade_solicitante",
                     "data_entrada_fila"

    Returns:
        float com a pontuação final.
    """
    hoje = date.today()

    score_base = (
        score_data_retorno(solicitacao.get("data_retorno", ""), hoje)   * PESO_DATA_RETORNO +
        score_urgencia(solicitacao.get("unidade_solicitante", ""))      * PESO_URGENCIA +
        score_localidade(paciente.get("cidade", ""))                    * PESO_LOCALIDADE +
        score_idade(paciente.get("data_nascimento", ""), hoje)          * PESO_IDADE
    )

    bonus = bonus_tempo_espera(solicitacao.get("data_entrada_fila", ""), hoje)

    return round(score_base + bonus, 2)


# ---------------------------------------------------------------------------
# Ordenação da fila
# ---------------------------------------------------------------------------

def ordenar_fila(solicitacoes: list[dict]) -> list[dict]:
    """
    Recebe lista de solicitações pendentes, calcula a pontuação de cada uma
    e retorna a lista ordenada por prioridade (maior pontuação primeiro).

    Cada item da lista deve ter as chaves "paciente" e, no mesmo nível,
    os campos de solicitação esperados por calcular_pontuacao().

    Adiciona o campo "pontuacao" em cada item da lista.

    Exemplo de item esperado:
        {
            "id": 42,
            "data_retorno": "2026-07-10",
            "unidade_solicitante": "UTI ADULTO",
            "data_entrada_fila": "2026-06-01",
            "paciente": {
                "cidade": "Petrolina",
                "data_nascimento": "1950-03-15",
            }
        }
    """
    for s in solicitacoes:
        paciente = s.get("paciente", {})
        s["pontuacao"] = calcular_pontuacao(paciente, s)

    return sorted(solicitacoes, key=lambda x: x["pontuacao"], reverse=True)