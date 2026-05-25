# Guia de Instalacao e Execucao

Este guia contem os passos detalhados para configurar e executar os ambientes de desenvolvimento do backend e do frontend.

## Pre-requisitos

- Python 3.10 ou superior
- Node.js 18 ou superior
- Git

## 1. Configuracao do Backend

Siga estes passos a partir da raiz do repositorio.

```bash
# 1. Clone o repositorio (se ainda nao o fez)
# git clone <url-do-repositorio>
# cd <nome-do-repositorio>

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 3. Instale as dependencias do Python
pip install -r requirements.txt

# 4. Configure as variaveis de ambiente
# Copie o arquivo de exemplo para criar seu arquivo de configuracao local
cp .env.example .env

# Edite o arquivo .env com suas configuracoes (banco de dados, segredos, etc.)
# Dica: Para desenvolvimento offline, voce pode deixar as variaveis de AD e POSTGRES comentadas.
nano .env
```

## 2. Configuracao do Frontend

Estes passos devem ser executados em um novo terminal.

```bash
# 1. Navegue ate a pasta do frontend
cd frontend

# 2. Instale as dependencias do Node.js
npm install
```

## 3. Executando a Aplicacao

### Servidor de Backend

Com o ambiente virtual (`.venv`) ativado, execute o servidor FastAPI a partir da raiz do projeto.

```bash
uvicorn src.main:app --reload
```

- O backend estara disponivel em `http://127.0.0.1:8000`.
- A documentacao interativa da API (Swagger UI) estara em `http://127.0.0.1:8000/docs`.
- A documentacao alternativa (ReDoc) estara em `http://127.0.0.1:8000/redoc`.

### Servidor de Frontend

Na pasta `frontend/`, execute o servidor de desenvolvimento do Vite.

```bash
npm run dev
```

- O frontend estara disponivel em `http://127.0.0.1:5173` (ou outra porta indicada pelo Vite). O servidor de desenvolvimento do Vite ja vem configurado com um proxy para o backend, entao todas as chamadas de API para `/api` serao redirecionadas automaticamente para `http://127.0.0.1:8000`.

## 4. Build de Producao do Frontend

Para gerar a versao de producao do frontend, que e servida diretamente pelo FastAPI:

```bash
# Na pasta frontend/
npm run build
```

Os arquivos gerados em `frontend/dist/` serao servidos pela aplicacao FastAPI quando ela nao estiver em modo de desenvolvimento, na rota raiz (`/`).
