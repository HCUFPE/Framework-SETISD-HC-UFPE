# Framework-SETISD-HC-UFPE

> **Arquitetura Web Full-Stack de Referência (Python / FastAPI + Vue 3 / Vite)**  
> *Padrão Oficial de Desenvolvimento de Sistemas para o Hospital das Clínicas da UFPE (HC-UFPE / EBSERH).*

---

## 🏛️ Visão Geral

O **Framework-SETISD-HC-UFPE** é a base arquitetural monolítica limpa, desacoplada e padronizada para a criação de novas aplicações web corporativas no HC-UFPE. 

Ele consolida as melhores práticas de engenharia de software da equipe de TI (SETISD), garantindo que todos os novos sistemas sigam os mesmos padrões de **tecnologia, segurança, acesso a dados (AGHU), interface visual e conteinerização (Podman)**.

---

## 🚀 Pilares da Arquitetura

- **🛡️ Autenticação Híbrida & Segurança Corporativa:**
  - Suporte nativo ao **Active Directory (AD/LDAP Ebserh)** em produção.
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
- **🐳 DevOps & Conteinerização (Podman / Docker):**
  - `Dockerfile` multi-stage (Build Vue 3 + Runtime Python 3.12) e `compose.yaml` otimizados para deploy em homologação e produção nas VMs do hospital.

---

## 📂 Estrutura do Projeto

```text
Framework-SETISD-HC-UFPE/
├── .env.example          # Modelo de variáveis de ambiente
├── Dockerfile            # Receita de build multi-estágio (Podman / Docker)
├── compose.yaml          # Orquestração do contêiner para VMs
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
│   │   ├── services/     # Serviços HTTP (api.ts com Axios Interceptors)
│   │   └── stores/       # Gerenciamento de estado (Pinia)
├── src/                  # Backend FastAPI (API REST)
│   ├── auth/             # Provedores de Autenticação (Active Directory, Mock, JWT)
│   ├── controllers/      # Regras de negócio da aplicação
│   ├── dependencies.py   # Fábrica de injeção de dependências
│   ├── main.py           # Ponto de entrada do FastAPI, CORS, middlewares e erros
│   ├── models/           # Modelos ORM (SQLAlchemy) e Schemas (Pydantic)
│   ├── providers/        # Camada de acesso a dados (PostgreSQL AGHU, CSV)
│   ├── resources/        # Gerenciamento de conexões com banco de dados (database.py)
│   └── routers/          # Definição dos endpoints da API (/api/*)
└── tests/                # Suíte de testes automatizados oficial (pytest)
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

## 🐳 Deploy nas VMs com Podman / Docker

Para realizar o build e executar a aplicação em contêiner na VM oficial do hospital:

```bash
# 1. Build da imagem e inicialização do contêiner em background
podman compose up -d --build

# 2. Verificar os logs da aplicação
podman compose logs -f
```

A aplicação ficará disponível consolidada em `http://IP-DA-VM:8000/`.

---

## 📚 Documentação Detalhada

Para se aprofundar nos padrões arquiteturais do hospital, consulte a documentação oficial na pasta `docs/`:

- **[ Guia de Instalação, Execução e Deploy (`docs/SETUP.md`)](./docs/SETUP.md)**
- **[ Gabarito de Especificação de Requisitos - SDD (`docs/especificacao/README.md`)](./docs/especificacao/README.md)**
- **[ Arquitetura em Camadas e Padrão Provider (`docs/ARCHITECTURE.md`)](./docs/ARCHITECTURE.md)**
- **[ Manual de Autenticação AD, Mock e JWT (`docs/AUTHENTICATION.md`)](./docs/AUTHENTICATION.md)**
- **[ Tutorial de Criação de Novas Funcionalidades (`docs/GUIA_DESENVOLVIMENTO.md`)](./docs/GUIA_DESENVOLVIMENTO.md)**

---

**SETISD - Setor de TI e Saúde Digital | HC-UFPE (EBSERH)**
