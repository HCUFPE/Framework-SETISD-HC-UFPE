# Arquitetura e Segurança

## 1. Stack Técnica

| Camada | Tecnologia | Versão |
|---|---|---|
| Backend | FastAPI (Python) | 0.121.0 |
| ORM / Migrations | SQLAlchemy + Alembic | 2.0 / 1.17 |
| Banco (produção) | PostgreSQL | — |
| Banco (desenvolvimento) | SQLite (aiosqlite) | — |
| Autenticação LDAP | ldap3 | 2.9.1 |
| Token JWT | PyJWT | 2.10.1 |
| Frontend | Vue 3 + TypeScript | 3.3 |
| Build frontend | Vite | 5.2 |
| Estado frontend | Pinia | 3.0 |
| Rotas frontend | Vue Router | 4.2 |
| Validação frontend | Vee-validate + Zod | 4.15 / 3.25 |
| HTTP client | Axios | 1.13 |
| CSS | Tailwind CSS | 4.0 |
| Gerenciador de pacotes Python | uv | — |

---

## 2. Arquitetura em Camadas

O fluxo de uma requisição segue o padrão unidirecional:

```
Roteador → Controller → Provedor
```

### 2.1 Roteador (`src/routers/`)
Define endpoints da API, valida dados de entrada com Pydantic, gerencia injeção de dependências via `Depends`, declara a `STRATEGY` de fonte de dados e aplica autenticação JWT via `auth_handler.decode_token`.

### 2.2 Controller (`src/controllers/`)
Contém a lógica de negócio. Agnóstico à fonte de dados — opera exclusivamente pela interface do provedor. Orquestra operações e formata respostas.

### 2.3 Provedor (`src/providers/`)
Camada de acesso a dados. Cada domínio tem:
- **Interface** (`src/providers/interfaces/`): contrato que define os métodos disponíveis.
- **Implementações** (`src/providers/implementations/`): `CsvProvider` (desenvolvimento) e `PostgresProvider` (produção).
- **SQL** (`src/providers/sql/`): queries específicas do banco.

### 2.4 Seleção de Estratégia

A troca de fonte de dados é feita em um único ponto por roteador:

```python
# src/routers/paciente.py
STRATEGY = "csv"  # trocar para "postgres" ou "aghu" conforme ambiente

@router.get("")
async def listar_pacientes(
    provider: PacienteProviderInterface = Depends(get_paciente_provider(STRATEGY))
):
    return await paciente_controller.listar_pacientes(provider)
```

A fábrica `get_paciente_provider` em `src/dependencies.py` retorna a função de dependência correta. Pool de conexão com o banco só é inicializado se a estratégia `"postgres"` for selecionada.

---

## 3. Autenticação e Segurança

### 3.1 Fluxo de Autenticação

```
POST /api/login
  → ldap3 autentica contra AD do HC
  → Grupos do AD extraídos e incluídos no payload JWT
  → JWT emitido (15 min)
  → Se remember_me=true: refresh token persistido no banco, enviado como HttpOnly cookie

Requisições autenticadas:
  → Bearer JWT no header Authorization
  → auth_handler.decode_token valida e injeta user nas dependências

Renovação:
  POST /api/token/refresh
    → Verifica refresh token do cookie
    → Invalida token antigo (rotação)
    → Emite novo JWT + novo refresh token

POST /api/logout
  → Invalida refresh token no banco
  → Apaga cookie
```

### 3.2 RBAC

Grupos do AD mapeados para roles do sistema:

| Grupo AD | Role | Acesso |
|---|---|---|
| médico_hc | Médico HC | Fila, Briefing, Formulário, Caderneta |
| médico_satélite | Médico Satélite | Formulário, Encaminhamento |
| recepção | Recepção | Fila (transição de status) |
| gestão | Gestão | Dashboard Gerencial, Fila |

### 3.3 Guardrails de Segurança

**Obrigatório:**
- Segredos exclusivamente em variáveis de ambiente (`.env`). Proibido hardcode de chaves, senhas ou tokens no código.
- Cookie de refresh token: `httponly=True`, `samesite="lax"`, `secure=True` em produção.
- Soft delete obrigatório: coluna `deleted_at`. Proibido `DELETE` SQL em entidades de domínio.
- Auditoria: toda ação sensível gera log com `user_id`, timestamp e recurso acessado.

**Proibido:**
- Alterar arquivos de infraestrutura ou configuração global sem instrução explícita no `SPEC.md`.
- Criar dependências externas não documentadas neste arquivo.
- Burlar o sistema de RBAC por qualquer meio.
- Refatorar código existente sem instrução explícita.

---

## 4. Conformidade LGPD

- **Rastreabilidade de dados externos:** Campo `origemDescricao` obrigatório em `ConsultaExterna` — documenta como dados de terceiros foram obtidos.
- **Acesso auditável:** Logs de quem acessou, quando e qual dado do paciente.
- **Consentimento:** TCLE a ser implementado conforme definição com Joana Lidyanne.
- **Dados sensíveis:** Prontuário, diagnóstico, dados antropométricos — acesso restrito por RBAC.

---

## 5. Estrutura de Diretórios

```
atendimentos/
├── src/
│   ├── auth/           # auth_handler: LDAP, JWT, decode_token
│   ├── controllers/    # lógica de negócio
│   ├── models/         # SQLAlchemy models (RefreshToken, ...)
│   ├── providers/
│   │   ├── interfaces/         # contratos por domínio
│   │   ├── implementations/    # CsvProvider, PostgresProvider
│   │   └── sql/                # queries SQL
│   ├── resources/      # database.py (engine, sessions)
│   ├── routers/        # endpoints: auth, paciente, aih, bpa, admin, material
│   └── dependencies.py # fábricas de provedores
├── frontend/
│   ├── src/
│   │   ├── views/      # páginas Vue (Home, Login, Pacientes, Admin)
│   │   ├── components/ # componentes reutilizáveis
│   │   ├── stores/     # Pinia stores
│   │   ├── router/     # Vue Router
│   │   └── services/   # chamadas Axios à API
│   └── ...
├── alembic/            # migrations de banco de dados
├── data/               # arquivos CSV (ambiente de desenvolvimento)
├── docs/               # documentação do projeto
├── main.py             # entrypoint FastAPI
├── pyproject.toml      # dependências Python (uv)
└── start.sh            # script de inicialização
```

---

## 6. Guardrails para IA (SDD)

### Escopo Positivo (O que fazer)
- Seguir rigorosamente o Modelo de Dados definido em `04-modelo-dados.md`.
- Usar Pydantic v2 para validação de entrada em todos os endpoints.
- Criar `src/providers/interfaces/` antes da implementação concreta de qualquer novo domínio.
- Documentar funções complexas com docstring de uma linha.
- Tratamento de erros com blocos try/except e log padronizado.

### Escopo Negativo (O que NÃO fazer)
- Sem `DELETE` SQL: usar `deleted_at` para exclusão lógica.
- Sem segredos no código: usar `.env` e `python-dotenv`.
- Sem refatoração não solicitada: não alterar arquivos de infraestrutura sem instrução explícita no `SPEC.md`.
- Sem dependências externas não listadas no `pyproject.toml` sem aprovação.
- Sem bypass de autenticação ou RBAC por qualquer motivo.
