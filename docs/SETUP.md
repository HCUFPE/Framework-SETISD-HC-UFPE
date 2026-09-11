# Guia de Instalação, Execução, Testes e Deploy

Este documento é o guia definitivo para configurar, executar, testar e implantar aplicações baseadas no **Framework-SETISD-HC-UFPE**.

---

## 📋 Pré-requisitos do Ambiente
 
 - **Python:** 3.12 ou superior (recomendado uso do gerenciador `uv`)
 - **Node.js:** 20 ou superior
 - **Git:** Para controle de versão
 - **Contêineres (Opcional, apenas para deploy em VM):** Podman ou Docker com suporte a compose

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

# 3. Crie e edite o arquivo de variáveis de ambiente
cp .env.example .env

# Dica: Para desenvolvimento offline (sem acesso ao banco AGHU), use PACIENTE_PROVIDER_TYPE=CSV
nano .env
```

---

## 2. Configuração do Frontend

Estes passos devem ser executados na pasta do frontend para instalar as dependências do Vue 3:

```bash
# 1. Navegue até a pasta do frontend
cd frontend

# 2. Instale as dependências do Node.js
npm install
```

---

## 3. Executando a Aplicação em Desenvolvimento

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

## 🧪 4. Execução da Suíte de Testes Automatizados

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

## 🚀 5. Opções de Implantação em Servidores e VMs

O framework suporta dois modelos de deploy em produção: **Direto no Sistema Operacional (Bare-Metal / Systemd)** ou **Encapsulado em Contêineres (Podman / Docker)**.

---

### Opção A: Implantação Direta na VM (Sem Contêineres / Systemd)

Esta é a opção mais leve e rápida, ideal para servidores onde o Python 3.12+ e Node.js já estão instalados:

#### 1. Preparação e Build Inicial na VM
```bash
# Clone ou copie o projeto para a pasta de destino (ex: /var/app/meu-sistema)
cd /var/app/meu-sistema

# Instale as dependências e faça o build do frontend
uv sync
cd frontend && npm install && npm run build && cd ..

# Configure o arquivo de variáveis de ambiente de produção
cp .env.example .env
nano .env
```

#### 2. Testar Execução Manual
Você pode usar o script [start.sh](file:///c:/Users/daniel.turmina/Documents/FrameworkSETISD/start.sh) que valida dependências, faz build e inicia o Uvicorn:
```bash
chmod +x start.sh
./start.sh
```

#### 3. Criar Serviço no Linux (`systemd`) para Inicialização Automática
Para manter a aplicação rodando como serviço de fundo permanente e reiniciar após reboot da VM, crie o arquivo `/etc/systemd/system/meu-sistema.service`:

```ini
[Unit]
Description=Serviço Backend/Frontend FastAPI - HC-UFPE
After=network.target

[Service]
Type=simple
User=ebserh
WorkingDirectory=/var/app/meu-sistema
ExecStart=/var/app/meu-sistema/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
EnvironmentFile=/var/app/meu-sistema/.env

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable meu-sistema
sudo systemctl start meu-sistema
sudo systemctl status meu-sistema
```

---

### Opção B: Implantação em Contêineres (Podman / Docker)

Para quem prefere isolar a aplicação e suas dependências de SO em um contêiner OCI:

#### Execução via Compose
```bash
# Build e execução em segundo plano (detached)
podman compose up -d --build
# (ou com docker: docker compose up -d --build)

# Verificar o status dos contêineres rodando
podman compose ps

# Acompanhar os logs do servidor em tempo real
podman compose logs -f
```

#### Comandos de Manutenção do Contêiner
```bash
# Parar os serviços
podman compose down

# Reiniciar o contêiner da aplicação
podman compose restart
```

---

## 🛠️ 6. Comandos Utilitários de Diagnóstico

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
