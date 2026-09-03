# Guia de Instalação, Execução, Testes e Deploy

Este documento é o guia definitivo para configurar, executar, testar e implantar aplicações baseadas no **Framework-SETISD-HC-UFPE**.

---

## 📋 Pré-requisitos do Ambiente

- **Python:** 3.12 ou superior (recomendado uso do gerenciador `uv`)
- **Node.js:** 20 ou superior
- **Contêineres:** Podman (com `podman-compose` / `podman compose`) ou Docker
- **Git:** Para controle de versão

### Dependências de Sistema em Servidores Linux (Ubuntu / Debian / RHEL)
```bash
sudo apt update && sudo apt install -y build-essential libpq-dev libsasl2-dev libldap2-dev libssl-dev git
```

---

## 1. Configuração do Ambiente de Desenvolvimento

Siga os passos a partir da raiz do repositório:

```bash
# 1. Instale o gerenciador uv (caso não possua)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sincronize o ambiente e instale as dependências automaticamente
uv sync

# 3. Crie o arquivo de variáveis de ambiente
cp .env.example .env
```

---

## 2. Executando a Aplicação em Desenvolvimento

### A. Modo de Desenvolvimento Paralelo (`./dev.sh`) — RECOMENDADO
Inicia o Backend (FastAPI) na porta `8000` e o Frontend (Vite) na porta `5173` com atualização instantânea (Hot Reload):

```bash
chmod +x dev.sh
./dev.sh
```
- **Acesse o Frontend:** `http://localhost:5173`
- **Acesse a API / Swagger:** `http://localhost:8000/docs`

### B. Modo Produção Local (`./start.sh`)
Realiza o build do Vue e serve a aplicação consolidada em porta única:
```bash
chmod +x start.sh
./start.sh
```
- **Acesse a Aplicação Consolidada:** `http://localhost:8000`

---

## 🧪 3. Execução da Suíte de Testes Automatizados

O framework possui uma suíte de testes integrada com `pytest` para verificar a integridade da aplicação antes de commits ou deploys:

```bash
# Executar todos os testes automatizados
uv run pytest

# Executar com saída detalhada (verbose)
uv run pytest -v
```

Os testes validam:
- Endpoint de monitoramento de infraestrutura (`GET /api/health`).
- Fluxo de login e geração de tokens JWT (`POST /api/login`).
- Proteção de rotas autenticadas (`GET /api/users/me`).

---

## 🐳 4. Implantando nas VMs com Podman / Docker

Este framework vem configurado de fábrica para ser executado em contêineres nas VMs do hospital via **Podman**:

### Execução via Podman Compose (Recomendado)
```bash
# Build e execução em segundo plano (detached)
podman compose up -d --build

# Verificar o status dos contêineres rodando
podman compose ps

# Acompanhar os logs do servidor em tempo real
podman compose logs -f
```

### Comandos de Manutenção no Servidor
```bash
# Parar os serviços
podman compose down

# Reiniciar o contêiner da aplicação
podman compose restart
```

---

## 🛠️ 5. Comandos Utilitários de Diagnóstico

**Backend Isolado:**
```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Isolado:**
```bash
cd frontend
npm run dev
```

**Build Manual do Frontend:**
```bash
cd frontend
npm run build
```
