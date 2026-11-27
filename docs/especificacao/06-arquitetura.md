# Arquitetura e Segurança

## 1. Stack Técnica Obrigatória (`Framework-SETISD-HC-UFPE`)

| Camada | Tecnologia | Papel no Sistema |
| :--- | :--- | :--- |
| **Backend** | Python 3.12+, FastAPI, Uvicorn, Pydantic | API REST assíncrona (`async/await`), documentação Swagger (`/docs`) e servidor da SPA em produção. |
| **Banco Local (Escrita)** | SQLite (`data/app.db`) + SQLAlchemy 2.0 + Alembic | Persistência de importações do Forms, status da fila (24h), regras configuráveis, incompatibilidades, perfis RBAC, `refresh_tokens` e `audit_logs`. |
| **Banco Hospitalar (Leitura)** | PostgreSQL (AGHU) / CSV Oficial do Drive | Fonte de leitura desacoplada via **Padrão Provider + Strategy** (`STRATEGY = "csv"` em dev ↔ `"postgres"` em produção). |
| **Frontend** | Vue 3 (Composition API), TypeScript, Vite, Pinia, Tailwind CSS, Axios | SPA interna com auto-refresh de token JWT, componentes padronizados e versão **SemVer** no rodapé. |
| **Testes & Auditoria** | Pytest, Pytest-Asyncio, HTTPX, `audit_framework.py` | Validação automatizada de regras de negócio, segurança e 11 pilares SETISD. |
| **Deploy** | `systemd` (VM Linux nativa) ou `Podman` / `Docker` (`compose.yaml`) | Flexibilidade para implantação direta na VM do HC-UFPE. |

### Fluxo Unidirecional em Camadas
```text
Vue 3 (View / Pinia Store)
  → Router (src/routers/*.py — Default-Private)
  → Controller (src/controllers/*.py — Priorização, Higienização, Conflitos)
  → Provider (src/providers/interfaces + implementations — CSV ou Postgres)
  → SQL Template (src/providers/sql/exames/*.sql) / SQLite ORM (src/models/*.py)
```

---

## 2. Conformidade LGPD e Proteção de Dados Clínicos

* **Acesso Estritamente Interno:** A aplicação não é exposta à internet nem à rede de pacientes; apenas servidores autenticados na rede interna do HC-UFPE acessam os dados.
* **Minimização e Anonimização em Desenvolvimento:** Em ambiente de desenvolvimento/testes, utilizam-se exclusivamente dados anonimizados (CSV oficial do Drive), sem dados sensíveis reais.
* **Anti-Cache em Máquinas Compartilhadas:** Middleware HTTP injeta `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` e `Pragma: no-cache`, evitando retenção de dados clínicos em navegadores compartilhados na Central.
* **Rastreabilidade Total (`audit_logs`):** Todas as operações de escrita/alteração de status ou regras chamam `registrar_auditoria()` em `src/helpers/audit_helper.py`, gravando `usuario`, `categoria` (`SEGURANCA`, `NEGOCIO_CLINICO` ou `CONFIGURACAO`), `dados_anteriores`, `dados_novos` e `ip_origem`.

---

## 3. Segurança e Controle de Acessos (AD + RBAC)

1. **Autenticação (Etapa 1):** Active Directory / LDAP (`EBSERHNET`) em produção e provedor Mock (`admin`/`admin`) em desenvolvimento local.
2. **Autorização RBAC Local (Etapa 2):**
   - `ADMINISTRADOR`: acesso total, gestão de usuários (com pré-validação no AD), auditoria e regras.
   - `GESTOR_CENTRAL`: acesso à fila, dashboard de KPIs, auditoria e edição de regras/pesos/incompatibilidades.
   - `MARCADOR`: importação/higienização da planilha, operação da fila, filtros, busca ativa e controle de status/prazo 24h.
   - `CONSULTA`: acesso somente leitura à fila e indicadores.
3. **Sessão & Rotas:** JWT Access Token + Refresh Token em Cookie `HttpOnly`; todos os roteadores de domínio instanciados com `dependencies=[Depends(auth_handler.decode_token)]`.
4. **Governança de Segredos:** Variáveis validadas em `src/config.py`; `.env` fora do Git; apenas placeholders em `.env.example`.

---

## 4. Guardrails para IA (SDD e 11 Pilares Mandatórios)

Para manter 100% de conformidade com o `AGENTS.md` e o `Framework-SETISD-HC-UFPE`:

### Escopo Positivo (O que fazer)
- **Respeitar Camadas:** Nunca colocar SQL ou lógica de negócio dentro de `src/routers/`; usar SQL nativo em `src/providers/sql/` para AGHU e SQLAlchemy apenas para SQLite local.
- **Auditar Mutações:** Toda criação, edição ou exclusão lógica em rotas de negócio/configuração deve invocar `registrar_auditoria()`.
- **Testes Automatizados:** Criar testes `pytest` em `tests/` para cada novo controller/router e manter os testes existentes passando.
- **Executar Auditoria SETISD:** Validar conformidade dos 11 pilares ao finalizar cada entrega incremental.
- **Versionamento SemVer:** Manter a versão `vX.Y.Z` sincronizada entre backend (`src/version.py`), rodapé do frontend (`frontend/src/config/version.ts`) e Git Tags.

### Escopo Negativo (O que NÃO fazer — Anti-Patterns)
- **No AGHU Writes:** Proibido executar qualquer operação de escrita no PostgreSQL do AGHU.
- **No Hard Deletes:** Proibido `DELETE` físico em tabelas de negócio/configuração ou qualquer alteração em `audit_logs`; usar coluna `deleted_at`.
- **No Hardcoded Business Rules:** Proibido fixar pesos de prioridade, lista de incompatibilidades ou janelas de retorno somente em constantes imutáveis de código; sempre ler das tabelas configuráveis no SQLite (usando seed inicial).
- **No Secrets in Code:** Proibido salvar senhas, DSNs ou chaves JWT no código-fonte.
- **No Refactoring Unasked:** Não alterar os interceptadores Axios (`frontend/src/services/api.ts`), o middleware de Security Headers nem a estrutura de autenticação base sem instrução explícita no `SPEC.md`.
