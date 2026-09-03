# Framework-SETISD-HC-UFPE (Python/FastAPI + Vue.js)

Este projeto é um framework robusto e flexível para aplicações web modernas, construído com FastAPI no backend e Vue.js (Vite) no frontend. Ele foi projetado com uma arquitetura limpa e desacoplada, pronta para ser estendida e adaptada a diversas necessidades.

## Principais Características

- **Backend Moderno:** Construído com FastAPI, oferecendo alta performance, código assíncrono e documentação de API automática (Swagger/OpenAPI).
- **Frontend Reativo:** Utiliza Vue 3 com Vite para uma experiência de desenvolvimento rápida e uma interface de usuário reativa.
- **Arquitetura de Provedores:** Design flexível que permite trocar a fonte de dados de um domínio (ex: PostgreSQL, CSV) alterando uma única variável de configuração no arquivo do roteador, sem modificar o código de negócio.
- **Autenticação Híbrida:** Suporte nativo para autenticação via Active Directory (AD) em produção e um provedor "mock" para desenvolvimento offline (sem necessidade de credenciais de AD).
- **Estrutura Escalável:** Organização de projeto clara que separa responsabilidades (`routers`, `controllers`, `providers`), facilitando a manutenção e a adição de novas funcionalidades.

## Estrutura do Projeto

A estrutura do projeto é projetada para separar claramente as responsabilidades entre backend, frontend e documentação.

```
.
├── data/                 # Dados estáticos (ex: arquivos CSV)
├── docs/                 # Documentação detalhada do projeto
│   ├── ARCHITECTURE.md   # Explicação da arquitetura e padrões
│   ├── AUTHENTICATION.md # Detalhes sobre o sistema de autenticação
│   └── SETUP.md          # Guia de instalação e execução
├── frontend/             # Código-fonte da aplicação Vue.js
├── src/                  # Código-fonte do backend FastAPI
│   ├── auth/             # Lógica de autenticação (AD, Mock, JWT)
│   ├── controllers/      # Lógica de negócio e orquestração
│   ├── dependencies.py   # Fábrica de injeção de dependência
│   ├── models/           # Modelos de dados (SQLAlchemy)
│   ├── providers/        # Camada de acesso a dados (Postgres, CSV, etc.)
│   │   ├── implementations/
│   │   └── interfaces/
│   ├── resources/        # Configuração de recursos (ex: conexão com DB)
│   └── routers/          # Definição dos endpoints da API
├── .env.example          # Arquivo de exemplo para variáveis de ambiente
└── README.md             # Esta documentação
```

## Primeiros Passos

Para instalar e executar a aplicação, siga o guia de configuração detalhado:

- **[Guia de Instalação e Execução (SETUP.md)](./docs/SETUP.md)**

## Início Rápido (Quick Start)

Este projeto utiliza scripts automatizados para facilitar o ambiente:

1. **Configuração Inicial:**
   ```bash
   cp .env.example .env
   ```

2. **Modo Produção Local (Build & Run):**
   Gera o build do frontend e sobe o servidor FastAPI consolidado.
   ```bash
   ./start.sh
   ```

3. **Modo Desenvolvimento (Hot Reload):**
   Sobe o Backend e o Frontend (Vite) em paralelo com atualização instantânea.
   ```bash
   ./dev.sh
   ```

A aplicação estará disponível em `http://localhost:8000` (via start.sh) ou `http://localhost:5173` (via dev.sh).

## Aprofundamento

Para entender a fundo os conceitos e padrões utilizados neste framework, consulte a documentação específica:

- **[Arquitetura do Projeto (ARCHITECTURE.md)](./docs/ARCHITECTURE.md)**
- **[Sistema de Autenticação (AUTHENTICATION.md)](./docs/AUTHENTICATION.md)**
