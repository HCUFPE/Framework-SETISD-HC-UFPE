import asyncio
import sys
import os
import pandas as pd
from dotenv import load_dotenv

# 1. Configuração de caminhos absolutos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

sys.path.append(PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from sqlalchemy.dialects.sqlite import insert
from src.resources.database import DatabaseManager
from src.models.paciente import Paciente
from src.models.exame import Exame
from src.models.funcionario import Funcionario
from src.models.solicitacao import Solicitacao

APP_DB_URL = os.getenv("APP_DB_URL")
if not APP_DB_URL:
    raise ValueError("A variável APP_DB_URL não foi definida no .env")

sqlite_db_manager = DatabaseManager(APP_DB_URL)

# 2. Motor de Varredura Profunda (Deep Scan)
def encontrar_arquivo(nome_base, diretorio_raiz):
    for root, dirs, files in os.walk(diretorio_raiz):
        if 'venv' in root or '.venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if nome_base in file and file.endswith('.csv'):
                return os.path.join(root, file)
    return None

# Função para dividir as listas em pequenos pacotes (Chunks) para o SQLite
def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

ARQUIVOS_ALVO = ["dataset_mock_exames", "pacientes_hc"]
BATCH_SIZE = 200  # Tamanho seguro para o SQLite (200 registros * 4 colunas = 800 variáveis. Limite é 999)

async def ingerir_dados():
    print(f"Iniciando varredura profunda em: {PROJECT_ROOT}")
    
    dfs = []
    for nome_base in ARQUIVOS_ALVO:
        caminho_encontrado = encontrar_arquivo(nome_base, PROJECT_ROOT)
        
        if caminho_encontrado:
            print(f"-> Arquivo ENCONTRADO e carregado: {caminho_encontrado}")
            dfs.append(pd.read_csv(caminho_encontrado, dtype=str))
        else:
            print(f"-> AVISO: Nenhum arquivo contendo '{nome_base}' foi encontrado no projeto.")
            
    if not dfs:
        print("Nenhum dado para processar. Ingestão abortada.")
        return

    df_raw = pd.concat(dfs, ignore_index=True)

    if 'data_retorno' in df_raw.columns:
        df_raw['data_retorno'] = pd.to_datetime(df_raw['data_retorno'], errors='coerce').dt.date

    df_pacientes = df_raw[['prontuario', 'telefone', 'cidade', 'estado']].drop_duplicates(subset=['prontuario']).dropna(subset=['prontuario'])
    pacientes_records = df_pacientes.to_dict(orient='records')

    df_exames = df_raw[['codigo_exame', 'nome_exame']].drop_duplicates(subset=['codigo_exame']).dropna(subset=['codigo_exame'])
    df_exames = df_exames.rename(columns={'codigo_exame': 'codigo', 'nome_exame': 'nome'})
    exames_records = df_exames.to_dict(orient='records')

    df_funcionarios = df_raw[['id_funcionario']].drop_duplicates(subset=['id_funcionario']).dropna(subset=['id_funcionario'])
    df_funcionarios = df_funcionarios.rename(columns={'id_funcionario': 'id'})
    funcionarios_records = df_funcionarios.to_dict(orient='records')

    df_solicitacoes = df_raw[['codigo_solicitacao', 'data_retorno', 'unidade_solicitante']].drop_duplicates(subset=['codigo_solicitacao']).dropna(subset=['codigo_solicitacao'])
    df_solicitacoes = df_solicitacoes.rename(columns={'codigo_solicitacao': 'codigo'})
    solicitacoes_records = df_solicitacoes.to_dict(orient='records')

    # Inserção Assíncrona no SQLite (Em Lotes)
    async for session in sqlite_db_manager.get_session():
        async with session.begin():
            try:
                if pacientes_records:
                    for batch in chunk_list(pacientes_records, BATCH_SIZE):
                        await session.execute(insert(Paciente).values(batch).on_conflict_do_nothing(index_elements=['prontuario']))
                
                if exames_records:
                    for batch in chunk_list(exames_records, BATCH_SIZE):
                        await session.execute(insert(Exame).values(batch).on_conflict_do_nothing(index_elements=['codigo']))
                
                if funcionarios_records:
                    for batch in chunk_list(funcionarios_records, BATCH_SIZE):
                        await session.execute(insert(Funcionario).values(batch).on_conflict_do_nothing(index_elements=['id']))
                
                if solicitacoes_records:
                    for batch in chunk_list(solicitacoes_records, BATCH_SIZE):
                        await session.execute(insert(Solicitacao).values(batch).on_conflict_do_nothing(index_elements=['codigo']))

            except Exception as e:
                print(f"Erro crítico durante a execução do banco: {e}")
                await session.rollback()
                raise
            finally:
                await sqlite_db_manager.close_connection()

if __name__ == "__main__":
    asyncio.run(ingerir_dados())