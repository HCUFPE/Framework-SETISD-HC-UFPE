# Resources — Infraestrutura de Banco de Dados

Gerenciamento das conexões com os bancos de dados. Esta camada é a única que conhece os detalhes de configuração e inicialização dos pools de conexão.

---

## `database.py` — Banco da aplicação (App DB)

O App DB é o banco de dados que o sistema controla — onde ficam exames, frascos, cassetes, pacientes locais, etc.

**`DatabaseManager`** encapsula o engine SQLAlchemy assíncrono e o sessionmaker:

- Cria o engine a partir de uma DSN
- Mantém um pool de conexões
- Fornece `get_session()` como generator (abre e fecha a sessão automaticamente)

**`Base`** é a classe base de todos os modelos ORM. Os modelos precisam ser importados antes de `Base.metadata.create_all()` ser chamado — por isso `main.py` importa `src.models` no início.

**Dependencies do FastAPI:**

```python
get_app_db_session(request: Request) -> AsyncSession
```

Acessa `request.app.state.app_db` (inicializado no lifespan do FastAPI) e devolve uma sessão pronta para uso. Em caso de erro, faz rollback automaticamente.

---

## `postgres.py` — Banco externo AGHU

Wrapper para o banco PostgreSQL do AGHU (sistema do hospital, somente leitura).

Inicializa um `DatabaseManager` separado usando a DSN `POSTGRES_DSN` do `.env`. O engine é criado na importação do módulo.

```python
get_postgres_session() -> AsyncSession
```

Dependency análoga à do App DB, mas aponta para o banco AGHU.

---

## Dois bancos, dois worlds

| | App DB | AGHU (PostgreSQL) |
|---|---|---|
| **Quem controla** | Este sistema | Hospital (AGHU) |
| **Acesso** | Leitura e escrita | Somente leitura |
| **ORM** | SQLAlchemy (models/) | SQL direto (providers/sql/) |
| **Sessão** | `get_app_db_session` | `get_postgres_session` |
| **DSN** | `SQLITE_DSN` | `POSTGRES_DSN` |
| **Obrigatório** | Sim | Não (app funciona sem ele) |

---

## Inicialização (lifespan)

Os dois bancos são inicializados no startup do FastAPI em `main.py`:

```python
app.state.app_db = DatabaseManager(SQLITE_DSN)   # obrigatório
app.state.aghu_db = DatabaseManager(POSTGRES_DSN) # opcional, pula se DSN ausente
```

Ao desligar, os pools são fechados corretamente para liberar as conexões.
