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

## 3. Estrutura Recomendada de Diretórios

```text
src/
├── main.py
├── dependencies.py
├── auth/
│   └── auth.py
├── routers/
│   ├── health.py
│   ├── paciente.py
│   ├── auth.py
│   ├── admin.py
│   ├── aih.py
│   ├── bpa.py
│   └── material.py
├── controllers/
│   ├── paciente_controller.py
│   ├── aih_controller.py
│   ├── bpa_controller.py
│   └── material_controller.py
├── providers/
│   ├── interfaces/
│   ├── implementations/
│   └── sql/
│       ├── bpa/
│       └── material/
├── resources/
│   ├── database.py
│   └── postgres.py
├── models/
│   ├── base.py
│   └── refresh_token.py
├── helpers/
│   ├── csv_helper.py
│   ├── string_helper.py
│   ├── sql_helper.py
│   └── sigtap_helper.py
└── static/
    └── dist/   ← (build do Vue 3)
```

---

## 4. Arquitetura em Camadas e Fluxo de Dados

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

## 5. Domínios de Negócio e Escopo Hospitalar

| Domínio | Controllers / Providers | Função Principal |
| :--- | :--- | :--- |
| **Faturamento SUS** | `aih_controller.py`, `bpa_controller.py` | Geração de AIH, BPA e arquivos magnéticos SUS. |
| **Inventário / Estoque** | `material_controller.py`, `material_estoque_controller.py` | Dados de estoque e insumos do AGHU. |
| **Internação / Leitos** | `internacao_controller.py`, `leito_controller.py` | Censo diário, gestão de leitos e relatórios UTI/Clínica. |
| **Medicamentos** | `medicamentos_controller.py`, `antimicrobianos_controller.py` | Controle de dispensação e uso controlado. |
| **BI / Dashboard** | `metabase_controller.py` | Integrações com Metabase e relatórios gerenciais. |
| **Prontuário / Atendimento** | `prontuario_controller.py`, `atendimento_controller.py` | Histórico clínico de pacientes e atendimentos. |

---

## 6. Helpers e Funções Utilitárias

| Arquivo | Função | Propósito |
| :--- | :--- | :--- |
| `sql_helper.py` | `create_query()` | Substitui placeholders SQL (`#startDate`, `#cod_prontuario`). |
| `string_helper.py` | `remove_accents()`, `pad_start()`, `validate_cpf()` | Formatação e validações de documentos de saúde. |
| `csv_helper.py` | `convert_to_csv()`, `convert_to_tsv()` | Conversão JSON ➔ CSV/TSV para exportação. |
| `sigtap_helper.py` | Lookup SIGTAP | Validação e enriquecimento de procedimentos SUS. |

---

## 7. Convenções de Código e Respostas de Erro

- **Padrões de Nomes:** Use `snake_case` para arquivos e variáveis em Python, e `camelCase` para TypeScript no Vue.
- **Tipagem & Async:** Use **`async/await`**, **`type hints`** do Python e **docstrings** em todas as funções.
- **Respostas de Erro:** Todos os erros lançados devem usar `HTTPException` e retornar mensagens no formato de texto padrão:
  ```json
  {
    "detail": "Mensagem descritiva do erro para a interface"
  }
  ```
- **Preservação do Frontend:** Preserve os interceptadores do Axios (`frontend/src/services/api.ts`) e a biblioteca de componentes reusáveis.

---

## 8. Arquitetura de Segurança: Autenticação AD + RBAC Local da Aplicação

Todo sistema desenvolvido no framework DEVE seguir o modelo **Híbrido de Segurança**:

### Fluxo de Verificação em 2 Etapas:
1. **Etapa 1 (Autenticação no Active Directory - AD):** Valida a identidade e a senha corporativa do usuário na rede Ebserh (`EBSERHNET`). Se o funcionário for desligado do hospital, a TI desativa a conta no AD e o acesso cessa automaticamente em todos os sistemas.
2. **Etapa 2 (Autorização no Banco Local `data/app.db`):** O sistema verifica se o login do AD está previamente cadastrado e ativo na tabela local do sistema. Mesmo com senha do AD correta, o acesso só é concedido se a chefia do setor tiver vinculado o usuário no sistema.

### Exemplos de Perfis de Acesso (Exemplificativos / Customizáveis por Sistema):
Cada sistema definirá seus próprios perfis no banco local de acordo com suas regras de negócio. Abaixo estão exemplos comuns:
- `ADMINISTRADOR`: Acesso total ao sistema, configurações e gestão de usuários/perfis.
- `MEDICO`: Acesso a evolução clínica, prescrição e altas.
- `ENFERMAGEM`: Acesso ao censo diário de leitos, checagem e sinais vitais.
- `FARMACEUTICO`: Acesso a dispensação de medicamentos e estoque.
- `GESTOR_UNIDADE`: Acesso a relatórios estratégicos, indicadores e dashboards.
- `CONSULTA`: Acesso estritamente somente-leitura (Read-Only) para auditoria SUS ou BI.

