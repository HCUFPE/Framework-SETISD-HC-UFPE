# Backend — Sistema de Anatomia Patológica

API REST em **FastAPI** para rastreabilidade de amostras histopatológicas, cobrindo o fluxo Triagem → Macroscopia → Processamento Técnico → Microscopia.

---

## Stack

| Componente | Tecnologia |
|---|---|
| Framework | FastAPI 0.121.0 + Starlette 0.49.3 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrações | Alembic |
| Banco (dev) | SQLite via `aiosqlite` |
| Banco (prod) | PostgreSQL via `asyncpg` |
| Autenticação | JWT + LDAP/AD (`ldap3`) |

---

## Estrutura de pastas

```
backend/
├── src/                    # Código-fonte principal
│   ├── main.py             # Entrypoint FastAPI (lifespan, routers)
│   ├── auth/               # JWT + AD + RBAC por perfil
│   ├── controllers/        # Regras de negócio por etapa do fluxo
│   ├── helpers/            # Geração de identificadores (PATH-AAAA-XXXXXX, QR)
│   ├── models/             # Modelos SQLAlchemy (App DB)
│   ├── providers/          # Repositórios ORM e providers AGHU (read-only)
│   ├── resources/          # Conexões de banco (App DB + AGHU)
│   ├── routers/            # Endpoints FastAPI
│   ├── schemas/            # Pydantic request/response
│   └── services/           # Máquina de estados + histórico
├── alembic/                # Migrações do banco
│   └── versions/           # Scripts de migração (um por fase)
├── data/                   # CSVs de referência e dados de desenvolvimento
├── .env.example            # Variáveis de ambiente necessárias
├── requirements.txt        # Dependências Python
├── seed_dados.py           # Popula o banco com 10 exames para testes
├── testar_api.py           # Smoke test básico
└── testar_fase2.py         # Verificação end-to-end da Fase 2
```

---

## Setup rápido

```bash
cd backend

# 1. Criar e ativar ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar arquivo de ambiente
cp .env.example .env
# Edite o .env se necessário (padrão já funciona em dev)

# 4. Criar o banco e aplicar todas as migrações
python -m alembic upgrade head

# 5. Subir o servidor
python -m uvicorn src.main:app --reload --port 8000
# Ou:  bash start.sh
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

Credenciais de desenvolvimento: `admin` / `admin`

---

## Populando o banco com dados de teste

```bash
# Com o servidor rodando:
python seed_dados.py

# Em porta diferente:
python seed_dados.py --url http://localhost:8001
```

Cria 10 exames distribuídos em todas as etapas do fluxo (Na Triagem, Aguardando Macroscopia, Em Processamento, Aguardando Microscopia etc.).

---

## Variáveis de ambiente

| Variável | Descrição | Padrão dev |
|---|---|---|
| `SQLITE_DSN` | DSN do banco da aplicação | `sqlite+aiosqlite:///app.db` |
| `POSTGRES_DSN` | DSN do AGHU (somente leitura, opcional) | — |
| `JWT_SECRET` | Chave de assinatura JWT (≥ 32 chars) | ver `.env.example` |
| `JWT_EXP_HOURS` | Validade do access token em horas | `24` |
| `REFRESH_TOKEN_EXP_DAYS` | Validade do refresh token | `30` |
| `AD_URL` | URL do Active Directory (opcional) | — |
| `AD_BASEDN` | Base DN do AD | — |
| `PACIENTE_PROVIDER_TYPE` | `CSV` ou `POSTGRES` | `CSV` |

> Sem `AD_URL`: usa MockAuthProvider (`admin`/`admin`).

---

## Migrações

```bash
# Aplicar todas as migrações (dev e produção)
python -m alembic upgrade head

# Gerar nova migração após alterar modelos
python -m alembic revision --autogenerate -m "descricao"

# Ver histórico
python -m alembic history
```

---

## Fases implementadas

| Fase | Status | Endpoints |
|---|---|---|
| Triagem | ✅ | `POST /api/exames`, etiquetas, encaminhamento |
| Macroscopia | ✅ | Fila, busca, iniciar, registrar, cassetes A/B/C |
| Processamento Técnico | ✅ | Lotes, blocos de parafina, lâminas |
| Microscopia | 🔜 Fase 3 | — |
| Integração AGHU | 🔜 Fase 4 | — |
| Hardware (QR/impressora) | ⏳ Aguardando equipamento | — |

---

## Decisões arquiteturais relevantes

- **QR Code hardware-agnóstico**: a string `qr_code` é gerada e armazenada agora; quando a impressora Zebra/Argox chegar, ela apenas renderiza essa string. Nenhuma mudança no backend.
- **Dois bancos separados**: App DB (CRUD total, ORM) e AGHU (somente leitura, SQL direto). Ver `src/resources/database.py`.
- **RBAC permissivo**: `MODO_PERMISSIVO=True` em `src/auth/perfis.py` libera usuários autenticados até o HC definir os grupos do AD.
- **Histórico append-only**: toda transição de status grava em `historico_movimentacao`, nunca deletar.
