# AGENTS.md: Diretrizes de Arquitetura e IA (Framework-SETISD-HC-UFPE)

> **Instruções Obrigatórias para Agentes de IA (Gemini, Antigravity, Claude, ChatGPT, Cursor, Copilot)**
>
> Este documento orienta a geração e manutenção de código da aplicação **Python FastAPI + Vue 3 (Vite)** do **Hospital das Clínicas da UFPE (HC-UFPE / EBSERH)**. Ele DEVE ser seguido à risca para garantir padronização, segurança e compatibilidade funcional.

---

## 1. Regra de Entrada Obrigatória & Verificação de Conformidade

Antes de gerar qualquer código ou implementar uma nova funcionalidade no sistema:
1. **Consulte a especificação do projeto em [`docs/especificacao/SPEC.md`](docs/especificacao/SPEC.md)**.
2. Siga os casos de uso, requisitos e modelo de dados descritos na pasta `docs/especificacao/`.
3. **Validação Automática de Conformidade:** Ao concluir qualquer implementação ou refatoração, o agente de IA **DEVE obrigatoriamente executar o auditor de conformidade arquitertural** rodando o comando:
   ```bash
   python audit_framework.py .
   ```
   *(O agente deve garantir que a Taxa de Conformidade do projeto seja mantida em **100% (EXCELENTE)**).*

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
| **Deploy & Execução** | Systemd (Nativo Linux) ou Podman / Docker | Serviço systemd em VM ou contêiner via `compose.yaml` |

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
│   └── admin.py
├── controllers/
│   └── paciente_controller.py
├── providers/
│   ├── interfaces/
│   │   └── paciente_provider_interface.py
│   ├── implementations/
│   │   ├── paciente_postgres_provider.py
│   │   └── paciente_csv_provider.py
│   └── sql/
│       └── paciente/
├── resources/
│   ├── database.py
│   └── postgres.py
├── models/
│   ├── base.py
│   └── refresh_token.py
├── helpers/
│   └── sql_helper.py
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
| **Provider** | `src/providers/implementations/*.py` | Executa a query SQL ou lê dados de mock/CSV e retorna listas de dicionários. |
| **Controller** | `src/controllers/*.py` | Lógica de negócio, validações de regras hospitalares e formatação. |
| **Router** | `src/routers/*.py` | Endpoints HTTP FastAPI (`/api/*`), validação Pydantic e injeção de dependências (`Depends()`). |

---

## 5. Exemplo de Referência ("Golden Sample") e Domínios de Aplicação

O Framework fornece um módulo de referência completo de ponta a ponta: o módulo de **Pacientes** (`paciente.py`, `paciente_controller.py`, `paciente_provider_interface.py`, etc.). Ele serve como guia arquitetural para qualquer novo domínio que a aplicação venha a implementar.

### Exemplos de Aplicações e Módulos que Podem Ser Construídos sobre o Framework:
Ao criar um novo sistema no hospital, utilize o padrão do módulo `paciente` para estruturar os domínios específicos da sua aplicação:
- **Faturamento SUS:** Módulos de AIH, BPA e arquivos magnéticos SUS.
- **Inventário / Farmácia:** Módulos de Estoque, Lotes e Dispensação de Medicamentos.
- **Internação e Leitos:** Módulos de Censo diário, Gestão de Leitos e Painel de UTI/Clínica.
- **Prontuário e Atendimento:** Módulos de Evolução Clínica, Agendamento e Recepção.

---

## 6. Helpers e Funções Utilitárias

O framework inclui utilitários essenciais e permite a inclusão de helpers específicos conforme a necessidade do sistema:

| Arquivo | Função / Propósito | Status no Framework |
| :--- | :--- | :--- |
| `sql_helper.py` | `read_sql_file()`, `create_query()` — carrega queries e substitui parâmetros (`#param`). | **Nativo do Framework** |
| `string_helper.py` | Formatação e validação de CPF, CNS, limpeza de acentos (se necessário pelo sistema). | Opcional (definido por aplicação) |
| `csv_helper.py` | Exportação de relatórios para CSV/TSV (se necessário pelo sistema). | Opcional (definido por aplicação) |
| `sigtap_helper.py` | Consultas e cálculos de regras de procedimentos da tabela SIGTAP. | Opcional (definido por aplicação) |

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
2. **Etapa 2 (Autorização no Banco Local `data/app.db` com Pré-Validação AD):** 
   - **Validação no AD (`GET /api/admin/ad-user-search/{username}`):** Ao cadastrar um novo usuário em **Configurações**, a chefia/gestão clica em **"Consultar AD"**. O backend consulta o Active Directory (ou Mock em desenvolvimento) para garantir a existência do usuário e preencher automaticamente seu **Nome Completo**, **E-mail** e **Lotação / Setor**.
   - **Autorização Local:** Mesmo com a senha do AD correta, o acesso só é concedido se o login do AD estiver previamente cadastrado e ativo na tabela local do sistema.

---

### Exemplos de Perfis de Acesso (Exemplificativos / Customizáveis por Sistema):
Cada sistema definirá seus próprios perfis no banco local de acordo com suas regras de negócio. Abaixo estão exemplos comuns:
- `ADMINISTRADOR`: Acesso total ao sistema, configurações e gestão de usuários/perfis.
- `MEDICO`: Acesso a evolução clínica, prescrição e altas.
- `ENFERMAGEM`: Acesso ao censo diário de leitos, checagem e sinais vitais.
- `FARMACEUTICO`: Acesso a dispensação de medicamentos e estoque.
- `GESTOR_UNIDADE`: Acesso a relatórios estratégicos, indicadores e dashboards.
- `CONSULTA`: Acesso estritamente somente-leitura (Read-Only) para consulta.

---

### Regra de Proteção de Rotas por Padrão (Default-Private Router Pattern)

Para garantir que nenhuma rota de dados hospitalares fique exposta publicamente sem autenticação por esquecimento:
- **Proteção no Nível do Roteador (`APIRouter`):** Todo novo arquivo em `src/routers/` que manipule dados restritos/clínicos DEVE ser instanciado declarando a dependência de autenticação diretamente no `APIRouter`:
  ```python
  router = APIRouter(
      prefix="/api/modulo",
      tags=["Modulo"],
      dependencies=[Depends(auth_handler.decode_token)]
  )
  ```
- **Exceções Públicas:** Apenas rotas explicitamente de acesso livre (como `POST /api/login` em `auth.py` e `GET /api/health` em `health.py`) podem omitir essa dependência.

---

### Middleware Obrigatório de Cabeçalhos de Segurança HTTP (Security Headers)

Todo sistema construído sobre este Framework DEVE registrar o `@app.middleware("http")` no `src/main.py` para injetar automaticamente cabeçalhos de proteção em todas as respostas HTTP:
- **`X-Content-Type-Options: nosniff`**: Previne que navegadores interpretem arquivos com tipos MIME incorretos.
- **`X-Frame-Options: DENY`**: Protege a aplicação contra ataques de Clickjacking (impede inclusão em `<iframe>`).
- **`X-XSS-Protection: 1; mode=block`**: Ativa proteção contra ataques de Cross-Site Scripting (XSS).
- **`Cache-Control: no-store, no-cache, must-revalidate, max-age=0`**: Impede que dados clínicos/hospitalares fiquem salvos em cache de computadores públicos ou compartilhados dos setores.
- **`Pragma: no-cache`**: Garante compatibilidade de não-armazenamento em cache para clientes HTTP legados.

---

## 9. Padrão de Configurações e Segredos (Env Vars & Secrets)

Todo sistema desenvolvido no framework DEVE obrigatoriamente seguir a governança de segredos:
- **`Proibição de Hardcode`:** Nenhuma senha, DSN de banco, chave JWT ou credencial do AD pode ser escrita diretamente no código.
- **`.env.example` Gabarito:** Manter o `.env.example` atualizado apenas com variáveis e valores de exemplo fictícios/placeholders (sem senhas reais).
- **Validação Centralizada (`src/config.py`):** As variáveis devem ser carregadas e validadas na inicialização do servidor por um módulo centralizado (`src/config.py`). Se o ambiente for `ENV=production` e a chave `JWT_SECRET` for o valor padrão, o sistema deve disparar um aviso crítico no console.
- **Isolamento no Git:** O arquivo `.env` contendo as chaves reais NUNCA deve ser comitado no Git (mantido no `.gitignore`).

---

## 10. Padronização de Auditoria e Trilha de Mudanças (Audit Trail & Logging)

Todo sistema desenvolvido sobre este framework DEVE obrigatoriamente registrar auditoria em ações de mutação:
- **Tabela Unificada `audit_logs`:** Manter a estrutura de banco de dados (`src/models/audit_log.py`) para armazenar logs de auditoria imutáveis.
- **Invocação via Helper (`src/helpers/audit_helper.py`):** Operações de criação, alteração ou exclusão de dados clínicos ou de privilégios de acesso DEVEM invocar `registrar_auditoria()` salvando obrigatoriamente o estado anterior (`dados_anteriores`) e novo (`dados_novos`) em formato JSON.
- **Categorização Mandatória:** Todo registro deve ser classificado em `SEGURANCA`, `NEGOCIO_CLINICO` ou `CONFIGURACAO`.




