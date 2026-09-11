# Framework-SETISD-HC-UFPE

> **Arquitetura Web Full-Stack de Referência (Python / FastAPI + Vue 3 / Vite)**  
> *Padrão Oficial de Desenvolvimento de Sistemas para o Hospital das Clínicas da UFPE (HC-UFPE / EBSERH).*

---

## 🏛️ Visão Geral

O **Framework-SETISD-HC-UFPE** é a base arquitetural monolítica limpa, desacoplada e padronizada para a criação de novas aplicações web corporativas no HC-UFPE. 

Ele consolida as melhores práticas de engenharia de software da equipe de TI (SETISD), garantindo que todos os novos sistemas sigam os mesmos padrões de **tecnologia, segurança, acesso a dados (AGHU) e interface visual**, além de oferecer suporte pronto para **conteinerização opcional (Podman / Docker)**.

---

## 🚀 Pilares da Arquitetura

- **🛡️ Autenticação Híbrida & Segurança Corporativa (AD + RBAC):**
  - Suporte nativo ao **Active Directory (AD/LDAP Ebserh)** em produção com busca/validação prévia de usuários (`displayName`, `mail`, `department`).
  - Provedor **Mock** automático para desenvolvimento local sem dependência de rede.
  - Controle de sessão via **JWT Access Tokens** e **Refresh Tokens HttpOnly** com auto-renovação transparente no frontend.
- **⚡ Backend Moderno e Assíncrono (FastAPI):**
  - Construído com Python 3.12+, FastAPI e SQLAlchemy 2.0 com pools de conexões assíncronas para o **PostgreSQL do AGHU**.
  - Documentação interativa **Swagger UI (`/docs`)** com autenticação integrada via botão cadeado (**Authorize**).
  - Manipulador global de erros garantindo respostas padronizadas em formato JSON (`{"detail": "..."}`).
- **🎨 Frontend Reativo & UI Standard (Vue 3 / Vite):**
  - Vue 3 (Composition API / TypeScript) empacotado e servido diretamente pelo FastAPI.
  - Interceptadores Axios automáticos para injeção de tokens `Bearer` e renovação de sessão sem deslogar o usuário.
  - Biblioteca de componentes base reusáveis (`DataTable`, `Modal`, `Button`, `Card`, `ProfileDropdown`).
- **🩺 Monitoramento & Resiliência:**
  - Rota dedicada de diagnóstico de infraestrutura `GET /api/health` para sondagem de status do servidor e dos bancos de dados.
- **🧪 Garantia de Qualidade & Testes Automatizados:**
  - Suíte de testes integrada com `pytest` e `httpx` para validação imediata de status do servidor, autenticação e rotas.
- **🐳 DevOps & Conteinerização Opcional (Podman / Docker):**
  - `Dockerfile` multi-stage (Build Vue 3 + Runtime Python 3.12) e `compose.yaml` fornecidos como opção pronta para deploy em homologação e produção nas VMs do hospital.

---

## 📂 Estrutura do Projeto

```text
Framework-SETISD-HC-UFPE/
├── .env.example          # Modelo de variáveis de ambiente
├── AGENTS.md             # Diretrizes universais para Agentes de IA (Gemini, Claude, ChatGPT, Cursor)
├── Dockerfile            # Receita de build multi-estágio (opcional para Podman / Docker)
├── compose.yaml          # Orquestração de contêiner para VMs (opcional)
├── pyproject.toml        # Dependências e configurações do projeto Python (uv)
├── requirements.txt      # Lista congelada de pacotes Python
├── dev.sh                # Script de execução paralela para desenvolvimento
├── start.sh              # Script de build e execução local do servidor
├── docs/                 # Documentação detalhada da arquitetura e manuais
│   ├── especificacao/    # Gabarito oficial de Especificação de Software (Visão, Requisitos, SDD)
│   ├── ARCHITECTURE.md   # Arquitetura em camadas e padrão Provider
│   ├── AUTHENTICATION.md # Sistema de Autenticação (AD / Mock / JWT)
│   ├── GUIA_DESENVOLVIMENTO.md # Tutorial passo a passo para criar novas telas/rotas
│   └── SETUP.md          # Guia de instalação, testes e deploy
├── frontend/             # Aplicação SPA Vue 3 (Vite + TypeScript)
│   ├── src/
│   │   ├── components/   # Componentes visuais reusáveis (DataTable, Modal, etc.)
│   │   ├── layouts/      # Layouts de página (DefaultLayout, LoginLayout)
│   │   ├── router/       # Roteamento e guards de autenticação
│   │   ├── services/     # Cliente HTTP Axios com interceptadores de token
│   │   ├── stores/       # Gerenciamento de estado Pinia (auth, ui)
│   │   └── views/        # Telas da aplicação (Home, Login, Pacientes, Admin)
│   └── package.json      # Dependências do frontend (Node.js)
├── src/                  # Backend em Python FastAPI
│   ├── auth/             # Módulos de autenticação AD, JWT e Mock
│   ├── controllers/      # Regras de negócio e casos de uso
│   ├── helpers/          # Funções utilitárias (sql_helper)
│   ├── models/           # Modelos de dados SQLAlchemy (banco local)
│   ├── providers/        # Acesso a dados desacoplado (Interfaces, Postgres, CSV, SQLs)
│   ├── resources/        # Gerenciamento de conexões de banco de dados
│   ├── routers/          # Endpoints HTTP da API REST (Swagger)
│   └── main.py           # Ponto de entrada FastAPI e servidor SPA
└── tests/                # Testes automatizados assíncronos (pytest)
    ├── conftest.py       # Fixtures de teste do FastAPI TestClient
    ├── test_auth.py      # Testes de login Mock e validação de tokens
    └── test_status_servidor.py # Testes de status da aplicação e infraestrutura
```

---

## 🚦 Início Rápido (Quick Start)

### 1. Configuração do Ambiente
```bash
# Clone o repositório
git clone https://github.com/HCUFPE/Framework-SETISD-HC-UFPE.git
cd Framework-SETISD-HC-UFPE

# Copie o arquivo de exemplo de ambiente
cp .env.example .env
```

### 2. Executar em Modo Desenvolvimento (Hot Reload)
Executa o Backend (`http://localhost:8000`) e o Frontend Vite (`http://localhost:5173`) em paralelo:
```bash
./dev.sh
```

### 3. Rodar a Suíte de Testes Automatizados
```bash
uv run pytest
```

---

## 🚀 Opções de Deploy em Servidores e VMs

O framework oferece flexibilidade total para colocar o sistema no ar:

### 1. Implantação Direta na VM (Sem Contêineres / Systemd)
Para quem prefere rodar direto no sistema operacional sem overhead de contêiner:
```bash
# 1. Instalar dependências e compilar frontend
uv sync && cd frontend && npm install && npm run build && cd ..

# 2. Teste rápido manual (opcional)
./start.sh

# 3. Execução permanente como serviço do Linux (systemd)
sudo systemctl enable meu-sistema && sudo systemctl start meu-sistema
```

### 2. Implantação em Contêineres (Podman / Docker)
Para quem prefere isolamento completo:
```bash
# 1. Build da imagem e inicialização do contêiner em background
podman compose up -d --build
# (ou com docker: docker compose up -d --build)

# 2. Verificar os logs da aplicação
podman compose logs -f
```

A aplicação ficará disponível consolidada em `http://IP-DA-VM:8000/`. Para o passo a passo completo da configuração do arquivo de serviço do Linux (`systemd`), consulte o [Guia de Instalação e Deploy (`docs/SETUP.md`)](./docs/SETUP.md).

---

## 📚 Documentação Detalhada

Para se aprofundar nos padrões arquiteturais do hospital, consulte a documentação oficial na pasta `docs/`:

- **[ Guia de Instalação, Execução e Deploy (`docs/SETUP.md`)](./docs/SETUP.md)**
- **[ Gabarito de Especificação de Requisitos - SDD (`docs/especificacao/README.md`)](./docs/especificacao/README.md)**
- **[ Diretrizes e Regras para Agentes de IA (`AGENTS.md`)](./AGENTS.md)**
- **[ Arquitetura em Camadas e Padrão Provider (`docs/ARCHITECTURE.md`)](./docs/ARCHITECTURE.md)**
- **[ Manual de Autenticação AD, Mock e JWT (`docs/AUTHENTICATION.md`)](./docs/AUTHENTICATION.md)**
- **[ Tutorial de Criação de Novas Funcionalidades (`docs/GUIA_DESENVOLVIMENTO.md`)](./docs/GUIA_DESENVOLVIMENTO.md)**

---

**SETISD - Setor de TI e Saúde Digital | HC-UFPE (EBSERH)**
