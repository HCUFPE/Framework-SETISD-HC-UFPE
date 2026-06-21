"""
Gerador de dataset mock - Solicitação de Exames

Replica a estrutura observada no CSV de exemplo (400 linhas) e expande
para um volume maior usando a lib Faker (locale pt_BR), preservando os
relacionamentos reais entre as colunas. O dataset gerado é completamente
íntegro/coerente (sem valores nulos ou inconsistentes), pensado para
testar a aplicação como um todo sem ruído nos dados:

- prontuario          -> identifica um paciente (8 dígitos, sempre preenchido)
- telefone            -> DDD pernambucano (81/87), fixo por paciente
- cidade              -> município de Pernambuco, fixo por paciente
- estado              -> sempre "Pernambuco"
- codigo_solicitacao  -> identifica um "pedido": linhas com o mesmo
                         codigo_solicitacao compartilham data_retorno,
                         prontuario e unidade_solicitante (um pedido
                         pode conter de 1 a 20 exames)
- data_retorno        -> timestamp do pedido (mesmo para todas as
                         linhas daquele codigo_solicitacao)
- unidade_solicitante -> setor/ambulatório que solicitou (catálogo fixo)
- codigo_exame /
  nome_exame          -> catálogo fixo de exames (mapeamento 1:1, sempre
                         preenchido)
- id_funcionario /
  nome_funcionario    -> atendente que registrou o pedido (mapeamento 1:1)

"""

import argparse
import random
from datetime import datetime

import pandas as pd
from faker import Faker

fake = Faker("pt_BR")

# Catálogo de exames: codigo_exame -> nome_exame (69 exames do exemplo)
CATALOGO_EXAMES = [
    ("(TSH)", "(TSH)"),
    ("TCABI", "ABDOMEINFERIOR COM CONTRASTE"),
    ("RXAB6", "ABDOMEN SIMPLES (DECÚBITO DORSAL E ORTOSTÁTICA)"),
    ("TCABC", "ABDOMEN SUPERIOR COM CONTRASTE"),
    ("USABT", "ABDÔMEN TOTAL"),
    ("ALT", "ALANINA AMINOTRANSFERASE  TGP"),
    ("ALB", "ALBUMINA"),
    ("AMI", "AMILASE"),
    ("TCAVT", "ANGIOTOMOGRAFIA VENOSA DE TÓRAX"),
    ("AST", "ASPARTATO AMINOTRANSFERASE  TGO"),
    ("BAC", "BACTERIOLÓGICO"),
    ("GRA", "BACTERIOSCÓPICO"),
    ("BTFR", "BILIRRUBINA TOTAL E FRAÇÕES"),
    ("CLO", "CLORO"),
    ("HDL", "COLESTEROL HDL"),
    ("LDL", "COLESTEROL LDL"),
    ("COLT", "COLESTEROL TOTAL"),
    ("CLN", "COLONOSCOPIA"),
    ("CRE", "CREATININA"),
    ("CA", "CÁLCIO TOTAL"),
    ("COVID", "DETECÇÃO QUALITATIVA DE ANTIGENO - SARS - COV - 2"),
    ("USTDO", "ECO DE TIREÓIDE COM DOPPLER A CORES"),
    ("ECO", "ECOCARDIOGRAMA"),
    ("ECGR", "ELETROCARDIOGRAMA EM REPOUSO"),
    ("EDA", "ENDOSCOPIA DIGESTIVA ALTA"),
    ("ERGO", "ERGOMETRIA"),
    ("ESPB", "ESPIROMETRIA COM PROVA FARMACODINÂMICA"),
    ("FAN", "FATOR ANTI NUCLEAR"),
    ("(FR)", "FATOR REUMATÓIDE"),
    ("FERRI", "FERRITINA"),
    ("FER", "FERRO"),
    ("FIB", "FIBRINOGÊNIO"),
    ("FAL", "FOSFATASE ALCALINA"),
    ("FOS", "FÓSFORO"),
    ("GGT", "GAMA GLUTAMIL TRANSFERASE"),
    ("GLI", "GLICOSE"),
    ("HT.", "HEMATOCRITO."),
    ("HEFA", "HEMOCULTURA AERÓBICA E FUNGOS"),
    ("HB", "HEMOGLOBINA"),
    ("A1C", "HEMOGLOBINA GLICOSILADA"),
    ("H", "HEMOGRAMA COMPLETO"),
    ("ITS", "IDENTIFICAÇÃO E TESTE DE SENSIBILIDADE"),
    ("(IGE)", "IMUNOGLOBULINA IGE"),
    ("LDH", "LDH"),
    ("LIP", "LIPASE"),
    ("MAG", "MAGNÉSIO"),
    ("RXMM1", "MAMOGRAFIA BILATERAL"),
    ("K", "POTÁSSIO"),
    ("PCR", "PROTEÍNA C REATIVA"),
    ("RXPAP", "RX TÓRAX (PA+PERFIL)"),
    ("SOD", "SÓDIO"),  # código próprio atribuído (no exemplo original vinha sem código; evitamos "NA" pois é lido como nulo por pandas/Excel)
    ("T4", "T4"),
    ("TP", "TEMPO DE PROTROMBINA"),
    ("TTP", "TEMPO DE TROMBOPLASTINA PARCIAL ATIVADO"),
    ("TCA6", "TESTE DA CAMINHADA"),
    ("TRI", "TRIGLICERÍDIOS"),
    ("TNI", "TROPONINA I."),
    ("TCTX1", "TÓRAX"),
    ("RXTX1", "TÓRAX ( AP )  LEITO"),
    ("RXTX4", "TÓRAX (PA+P+OBL)"),
    ("UROC", "UROCULTURA DE URINA CATETERIZADA"),
    ("U", "URÉIA"),
    ("USIDA", "USG DOPPLER DO MEMBRO INFERIOR DIREITO ARTERIAL"),
    ("USIDV", "USG DOPPLER DO MEMBRO INFERIOR DIREITO VENOSO"),
    ("USIEA", "USG DOPPLER DO MEMBRO INFERIOR ESQUERDO ARTERIAL"),
    ("USIEV", "USG DOPPLER DO MEMBRO INFERIOR ESQUERDO VENOSO"),
    ("USGOD", "USG OBSTETRICA COM DOPPLERFLUXOMETRIA COLORIDA"),
    ("B12", "VITAMINA B12"),
    ("ACU", "ÁCIDO ÚRICO"),
]

# Unidades solicitantes: as 13 originais do exemplo + setores hospitalares
# adicionais plausíveis (mesmo padrão de nomenclatura: ambulatórios,
# alas numeradas/cardeais, UTIs, centros cirúrgicos)
UNIDADES_SOLICITANTES = [
    "PNEUMOLOGIA (AMBULATÓRIO)",
    "UDI: MAMOGRAFIA",
    "7 º SUL",
    "UTI ADULTO",
    "8º NORTE",
    "CIRURGIA GERAL (AMBULATÓRIO)",
    "CARDIOLOGIA (AMBULATÓRIO)",
    "CENTRO OBSTETRICO",
    "10º NORTE",
    "9º  SUL",
    "NEFROLOGIA (AMBULATÓRIO)",
    "CIRURGIA BARIATRICA",
    "OBSTETRÍCIA (AMBULATÓRIO)",
    "UTI PEDIÁTRICA",
    "UTI NEONATAL",
    "EMERGÊNCIA ADULTO",
    "EMERGÊNCIA PEDIÁTRICA",
    "ENDOCRINOLOGIA (AMBULATÓRIO)",
    "GASTROENTEROLOGIA (AMBULATÓRIO)",
    "ORTOPEDIA (AMBULATÓRIO)",
    "UROLOGIA (AMBULATÓRIO)",
    "ONCOLOGIA (AMBULATÓRIO)",
    "NEUROLOGIA (AMBULATÓRIO)",
    "6º NORTE",
    "11º SUL",
    "CENTRO CIRÚRGICO",
]

# Municípios de Pernambuco usados na coluna "cidade", com peso aproximado
# de porte populacional (cidades maiores aparecem mais, refletindo onde
# pacientes de um hospital de Recife/RMR tendem a vir). Pesos são
# ilustrativos, não censitários exatos.
MUNICIPIOS_PE_PESOS = [
    # Região Metropolitana do Recife (alta concentração)
    ("Recife", 30), ("Jaboatão dos Guararapes", 14), ("Olinda", 9),
    ("Paulista", 8), ("Cabo de Santo Agostinho", 5), ("Camaragibe", 5),
    ("São Lourenço da Mata", 3), ("Abreu e Lima", 3), ("Igarassu", 3),
    ("Ipojuca", 2), ("Moreno", 2), ("Itamaracá", 1), ("Araçoiaba", 1),

    # Agreste (Caruaru e polo de confecções)
    ("Caruaru", 6), ("Garanhuns", 3), ("Santa Cruz do Capibaribe", 2),
    ("Belo Jardim", 2), ("Gravatá", 2), ("Bezerros", 2), ("Toritama", 1),
    ("Pesqueira", 1), ("São Caitano", 1), ("Bom Conselho", 1),

    # Sertão (Petrolina e polo do São Francisco)
    ("Petrolina", 4), ("Serra Talhada", 2), ("Araripina", 2),
    ("Salgueiro", 2), ("Arcoverde", 2), ("Ouricuri", 1),
    ("Floresta", 1), ("Afogados da Ingazeira", 1),

    # Zona da Mata (cana-de-açúcar, litoral sul/norte)
    ("Vitória de Santo Antão", 3), ("Carpina", 2), ("Goiana", 2),
    ("Palmares", 1), ("Vicência", 1), ("Nazaré da Mata", 1),
    ("Timbaúba", 1), ("Água Preta", 1), ("Ribeirão", 1),
    ("Barreiros", 1), ("Escada", 1), ("Sirinhaém", 1),
]

DDDS_PERNAMBUCO = ["81", "87"]  

ESTADO = "Pernambuco"

# Faixa de datas observada no exemplo
DATA_MIN = datetime(2022, 10, 27)
DATA_MAX = datetime(2026, 4, 15)

# Distribuição de "exames por pedido" observada no exemplo (codigo_solicitacao
# -> quantidade de linhas). Reaproveitamos a mesma distribuição empírica para
# que os pedidos sintéticos tenham um tamanho realista.
DISTRIBUICAO_EXAMES_POR_PEDIDO = (
    [1] * 48 + [2] * 8 + [3] * 4 + [4] * 2 + [5] * 2 + [6] * 5 + [7] * 3 +
    [8] * 3 + [9] * 7 + [10] * 3 + [11] * 3 + [13] * 3 + [14] * 1 +
    [15] * 1 + [17] * 1 + [20] * 1
)


#GERAÇÃO DE ENTIDADES BASE (pacientes e funcionários)

def gerar_hash_funcionario() -> str:
    """Replica o padrão observado em nome_funcionario, ex.:
    'DBC53 5B96B49 40269' -> blocos hexadecimais de tamanho variável."""
    blocos = []
    for _ in range(random.randint(2, 4)):
        tamanho = random.randint(5, 8)
        blocos.append(fake.hexify("^" * tamanho, upper=True))
    return " ".join(blocos)


def gerar_funcionarios(qtd: int) -> pd.DataFrame:
    registros = []
    ids_usados = set()
    for _ in range(qtd):
        while True:
            id_func = random.randint(1000, 19999)
            if id_func not in ids_usados:
                ids_usados.add(id_func)
                break
        primeiro_nome = fake.first_name().upper()
        nome_funcionario = f"{primeiro_nome} {gerar_hash_funcionario()}"
        registros.append({"id_funcionario": id_func, "nome_funcionario": nome_funcionario})
    return pd.DataFrame(registros)


def gerar_pacientes(qtd: int) -> pd.DataFrame:
    registros = []
    prontuarios_usados = set()
    telefones_usados = set()

    cidades = [c for c, _ in MUNICIPIOS_PE_PESOS]
    pesos = [p for _, p in MUNICIPIOS_PE_PESOS]

    for _ in range(qtd):
        while True:
            # prontuario sempre com 8 dígitos, como no exemplo (1xxxxxxx / 2xxxxxxx)
            prontuario = random.randint(10_000_000, 22_999_999)
            if prontuario not in prontuarios_usados:
                prontuarios_usados.add(prontuario)
                break
        while True:
            ddd = random.choice(DDDS_PERNAMBUCO)
            # número de celular pernambucano: DDD + 9 + 8 dígitos
            telefone = f"{ddd}9{random.randint(10_000_000, 99_999_999)}"
            if telefone not in telefones_usados:
                telefones_usados.add(telefone)
                break
        cidade = random.choices(cidades, weights=pesos, k=1)[0]
        registros.append({
            "prontuario": prontuario,
            "telefone": telefone,
            "cidade": cidade,
        })
    return pd.DataFrame(registros)


#GERAÇÃO DOS "PEDIDOS" (codigo_solicitacao) E EXPANSÃO PARA LINHAS

def gerar_dataset(n_linhas: int, n_pacientes: int, n_funcionarios: int,
                   seed: int | None = 42) -> pd.DataFrame:
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    pacientes = gerar_pacientes(n_pacientes)
    funcionarios = gerar_funcionarios(n_funcionarios)

    codigos_usados = set()

    def novo_codigo_solicitacao() -> int:
        while True:
            codigo = random.randint(90_000, 1_400_000)
            if codigo not in codigos_usados:
                codigos_usados.add(codigo)
                return codigo

    linhas = []

    DISTRIBUICAO_ENXUTA = [1] * 6 + [2] * 3 + [3] * 1

    def gerar_pedido(paciente_row, distribuicao):
        funcionario = funcionarios.sample(1).iloc[0]
        unidade = random.choice(UNIDADES_SOLICITANTES)
        codigo_solicitacao = novo_codigo_solicitacao()
        data_retorno = fake.date_time_between(start_date=DATA_MIN, end_date=DATA_MAX)
        data_retorno_str = data_retorno.strftime("%Y-%m-%d %H:%M:%S.") + f"{random.randint(0, 999):03d}"

        qtd_exames = random.choice(distribuicao)
        qtd_exames = min(qtd_exames, n_linhas - len(linhas))
        if qtd_exames <= 0:
            return False
        exames_do_pedido = random.sample(CATALOGO_EXAMES, k=min(qtd_exames, len(CATALOGO_EXAMES)))
        if qtd_exames > len(exames_do_pedido):
            extra = random.choices(CATALOGO_EXAMES, k=qtd_exames - len(exames_do_pedido))
            exames_do_pedido += extra

        for codigo_exame, nome_exame in exames_do_pedido:
            linhas.append({
                "prontuario": paciente_row["prontuario"],
                "telefone": paciente_row["telefone"],
                "cidade": paciente_row["cidade"],
                "estado": ESTADO,
                "codigo_solicitacao": codigo_solicitacao,
                "data_retorno": data_retorno_str,
                "unidade_solicitante": unidade,
                "codigo_exame": codigo_exame,
                "nome_exame": nome_exame,
                "id_funcionario": funcionario["id_funcionario"],
                "nome_funcionario": funcionario["nome_funcionario"],
            })
        return True

    # --- Fase 1: garante que TODO paciente do pool apareça pelo menos uma
    # vez, com pedidos enxutos (1-3 exames) para preservar orçamento de
    # linhas e deixar espaço para a Fase 2 (retornos/recorrência). ---
    pacientes_pendentes = pacientes.sample(frac=1).to_dict("records")  # embaralhado
    for paciente_row in pacientes_pendentes:
        if len(linhas) >= n_linhas:
            break
        gerar_pedido(paciente_row, DISTRIBUICAO_ENXUTA)

    # --- Fase 2: ~30% dos pacientes ganham pedidos adicionais (retornos),
    # simulando recorrência real (paciente crônico, acompanhamento, etc.).
    # Usa a distribuição completa observada no exemplo (1 a 20 exames). ---
    n_pacientes_recorrentes = int(len(pacientes) * 0.30)
    pacientes_recorrentes = pacientes.sample(n=n_pacientes_recorrentes).to_dict("records")

    idx = 0
    while len(linhas) < n_linhas and pacientes_recorrentes:
        paciente_row = pacientes_recorrentes[idx % len(pacientes_recorrentes)]
        if not gerar_pedido(paciente_row, DISTRIBUICAO_EXAMES_POR_PEDIDO):
            break
        idx += 1

    # --- Fase 3 (fallback): se ainda sobrar orçamento de linhas (caso raro,
    # ex. poucos pacientes recorrentes para um volume muito grande), completa
    # sorteando livremente entre todos os pacientes. ---
    while len(linhas) < n_linhas:
        paciente_row = pacientes.sample(1).iloc[0].to_dict()
        if not gerar_pedido(paciente_row, DISTRIBUICAO_EXAMES_POR_PEDIDO):
            break

    df = pd.DataFrame(linhas[:n_linhas])

    # prontuario como inteiro "puro" (sem .0), já que agora não há nulos
    df["prontuario"] = df["prontuario"].astype("int64")

    # ordena por data_retorno, como no exemplo original (que está em ordem
    # aproximadamente cronológica por bloco de pedido)
    df["_dt"] = pd.to_datetime(df["data_retorno"])
    df = df.sort_values("_dt").drop(columns="_dt").reset_index(drop=True)

    return df


#CLI

def main():
    parser = argparse.ArgumentParser(description="Gera dataset mock de Solicitação de Exames")
    parser.add_argument("--linhas", type=int, default=50_000, help="Quantidade de linhas a gerar")
    parser.add_argument("--pacientes", type=int, default=12_000, help="Quantidade de pacientes únicos")
    parser.add_argument("--funcionarios", type=int, default=35, help="Quantidade de funcionários únicos")
    parser.add_argument("--saida", type=str, default="dataset_mock_exames.csv", help="Caminho do CSV de saída")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade (use -1 para aleatório)")
    args = parser.parse_args()

    seed = None if args.seed == -1 else args.seed

    df = gerar_dataset(
        n_linhas=args.linhas,
        n_pacientes=args.pacientes,
        n_funcionarios=args.funcionarios,
        seed=seed,
    )

    # quoting padrão (QUOTE_MINIMAL) reproduz o comportamento do CSV de
    # exemplo: só recebem aspas os campos que precisam (texto com vírgula,
    # ou que o pandas decide citar por ser string, como "telefone").
    df.to_csv(args.saida, index=False)
    print(f"Dataset gerado: {args.saida} | {len(df)} linhas | {df['codigo_solicitacao'].nunique()} pedidos")
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()