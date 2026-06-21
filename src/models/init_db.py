import asyncio
import sys
import os

# Adiciona o diretório pai ao sys.path para permitir importações do pacote src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa a base do SQLAlchemy e a engine configurada
from src.resources.database import Base
from src.resources.postgres import postgres_db_manager

# Importa TODOS os models para que o SQLAlchemy saiba quais tabelas criar
# A simples importação registra as classes no objeto 'Base.metadata'
from src.models.paciente import Paciente
from src.models.exame import Exame
from src.models.funcionario import Funcionario
from src.models.solicitacao import Solicitacao
from src.models.refresh_token import RefreshToken

async def init_models():
    print("Iniciando a criação das tabelas no banco de dados...")
    
    # Inicia a conexão com o banco
    async with postgres_db_manager.engine.begin() as conn:
        # Base.metadata.create_all não suporta execução assíncrona direta,
        # portanto, usamos run_sync para executar a DDL (Data Definition Language)
        await conn.run_sync(Base.metadata.create_all)
        
    print("Tabelas verificadas/criadas com sucesso!")
    
    # Fecha a engine para liberar recursos
    await postgres_db_manager.close_connection()

if __name__ == "__main__":
    # Executa a corrotina
    asyncio.run(init_models())