# AGENTS.md: Diretrizes de Arquitetura e IA (Framework-SETISD-HC-UFPE)

> **Instruções Obrigatórias para Agentes de IA (Gemini, Antigravity, Claude, ChatGPT, Cursor, Copilot)**
>
> Este documento orienta a geração e manutenção de código da aplicação **Python FastAPI + Vue 3 (Vite)** do **Hospital das Clínicas da UFPE (HC-UFPE / EBSERH)**. Ele DEVE ser seguido à risca para garantir padronização, segurança e compatibilidade funcional.

---

## 1. Regra de Entrada Obrigatória (Especificação de Requisitos)

Antes de gerar qualquer código ou implementar uma nova funcionalidade no sistema:
1. **Consulte a especificação do projeto em [`docs/especificacao/SPEC.md`](docs/especificacao/SPEC.md)**.
2. Siga os casos de uso, requisitos e modelo de dados descritos na pasta `docs/especificacao/`.

---

## 2. Pilha Tecnológica Padrão (TARGET)

| Camada | Tecnologia | Detalhes |
| :--- | :--- | :--- |
| **Backend** | Python 3.12+, FastAPI, Uvicorn | APIs REST assíncronas (`async/await`) |
| **Bancos de Dados** | PostgreSQL (AGHU) / SQLite (App Local) | Pools assíncronos em `src/resources/` |
| **ORM & Migrações** | SQLAlchemy 2.0+ & Alembic | Migrações em `alembic/` e modelos em `src/models/` |
| **Frontend** | Vue 3, TypeScript, Vite, Pinia, Tailwind | Servido pelo FastAPI (`/static/dist`) ou Vite Dev (`:5173`) |
| **Autenticação** | AD / LDAP (ldap3) + Mock | Tokens JWT Access + Refresh Cookies HttpOnly |
| **Testes** | Pytest, Pytest-Asyncio, HTTPX | Suíte automatizada na pasta `tests/` |
| **Conteinerização** | Podman / Docker | Build multi-estágio em `Dockerfile` e `compose.yaml` |

---

## 3. Arquitetura em Camadas e Fluxo de Dados

O fluxo de dados no backend é **estritamente unidirecional**:
$$\text{SQL Template} \longrightarrow \text{Resource} \longrightarrow \text{Provider} \longrightarrow \text{Controller} \longrightarrow \text{Router}$$

| Camada | Diretório | Responsabilidade |
| :--- | :--- | :--- |
| **SQL Templates** | `src/providers/sql/modulo/*.sql` | Código SQL nativo limpo (sem lógica de negócio em Python). |
| **Resource** | `src/resources/database.py` / `postgres.py` | Gerencia conexões e pools assíncronos (`AsyncEngine`, `AsyncSession`). |
| **Provider** | `src/providers/implementations/*.py` | Executa a query SQL e retorna listas de dicionários. |
| **Controller** | `src/controllers/*.py` | Lógica de negócio, validações de regras do hospital e formatação. |
| **Router** | `src/routers/*.py` | Endpoints HTTP FastAPI (`/api/*`), validação Pydantic e `Depends()`. |

---

## 4. Convenções de Código e Respostas de Erro

- **Padrões de Nomes:** Use `snake_case` para arquivos e variáveis em Python, e `camelCase` para TypeScript no Vue.
- **Tipagem & Async:** Use **`async/await`**, **`type hints`** do Python e **docstrings** em todas as funções.
- **Respostas de Erro:** Todos os erros lançados devem usar `HTTPException` e retornar mensagens no formato de texto padrão:
  ```json
  {
    "detail": "Mensagem descritiva do erro para a interface"
  }
  ```
- **Preservação do Frontend:** Preserve os interceptadores do Axios (`frontend/src/services/api.ts`) e a biblioteca de componentes reusáveis.
