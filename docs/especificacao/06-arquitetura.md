# Arquitetura e Segurança — SAE-HC

## 1. Stack Técnica
- **Backend (base, sem alterações nesta entrega):** Python 3.12+, FastAPI, SQLAlchemy 2.0, PostgreSQL (AGHU) e SQLite local (`data/app.db`), Alembic.
- **Frontend:** Vue 3 (Composition API + TypeScript), Vite, Pinia, Vue Router, Tailwind CSS via `@tailwindcss/vite`, Heroicons e vue-toastification.
- **Componentes reutilizáveis do framework:** `Card`, `Button`, `Modal`, `DataTable`, `ProfileDropdown`, `LoadingIndicator`; interceptadores de Axios em `frontend/src/services/api.ts` devem ser preservados.
- **Nenhuma dependência externa nova** é adicionada nesta entrega. Gráficos do painel são desenhados com SVG/CSS.

## 2. Arquitetura em Camadas
O fluxo do backend permanece unidirecional: **SQL Template → Resource → Provider → Controller → Router**. Nenhum router de domínio é criado enquanto as telas usam mocks. Quando a Fase 4 começar, cada router novo deve declarar `dependencies=[Depends(auth_handler.decode_token)]`, com exceção apenas de `/api/login` e `/api/health`.

No frontend, o fluxo é **View → Store (Pinia) → Service → Adaptador (mock ou `api.ts`)**:
- `frontend/src/types/sae.ts`: contratos TypeScript compartilhados.
- `frontend/src/mocks/fixtures.ts`: mapeia o fixture AGHUX para `Solicitacao` e mantém o estado mutável em memória.
- `frontend/src/mocks/dadosAghux.json`: fixture estático gerado a partir do CSV de apoio (576 itens → 493 solicitações).
- `scripts/importar_dados_aghux.py`: importador em Python stdlib (`csv`, `json`, `datetime`), sem novas dependências; o CSV usa aspas em dois níveis e é decodificado com `csv.reader` duas vezes.
- `frontend/src/config/tempo.ts`: data de referência do export (`2026-09-28T16:05:34.227`) usada como "agora" nos mocks para prazos, filtros e tempo na fila.
- `frontend/src/services/sae.ts`: expõe as mesmas funções para mocks ou API real; aplica filtros, ordenação e paginação de 20 em 20.
- `frontend/src/stores/*.ts`: estado, carregamento e erro consumidos pelas views.

### Adaptador de mocks
- Variável: `VITE_USE_MOCKS` em `frontend/.env.example`. Padrão: `true` (mocks ativos); `false` direciona as chamadas para o backend.
- O adaptador simula latência, ordenação pela pontuação dos critérios ativos, paginação de 20 em 20, persistência em memória das alterações de critérios/equipe e registro de eventos no histórico.
- Dados de origem: as solicitações vêm do export do AGHUX em `Documentos de Apoio/`; nomes já vêm anonimizados e o export não contém CPF/CNS. A pasta de documentos de apoio não é versionada nem necessária em tempo de execução — o fixture JSON gerado é suficiente.
- Trocar para o backend não exige alterar views ou stores — apenas a variável e, na Fase 4, a implementação dos endpoints de `05-interfaces.md`.

## 3. Conformidade LGPD e Privacidade
- CPF/CNS criptografados com AES-256 no backend (Fase 4); no frontend de mocks, nenhum CPF/CNS é exibido ou inventado, pois o export de apoio não contém esses campos.
- Coleta mínima de dados; painel de conferência é o único local com dados completos simulados.
- Trilha de auditoria imutável em `audit_logs` (`usuario`, `categoria`, `acao`, `recurso`, `dados_anteriores`, `dados_novos`, `ip_origem`), com categorias `SEGURANCA`, `NEGOCIO_CLINICO`, `CONFIGURACAO`.

## 4. Acessos (RBAC híbrido)
1. **Autenticação:** AD/LDAP Ebserh (Mock em desenvolvimento) valida identidade e senha corporativas.
2. **Autorização:** `USUARIO_PERFIL` no banco local define `AREA_GESTORA`, `OPERADOR`, `CHEFIA`, `COORDENACAO` ou `ADMIN_TI`; usuário inativo não entra mesmo com senha correta do AD.
3. O frontend usa `meta.roles` nas rotas e filtra o menu, mas a autoridade é sempre validada no backend.

## 5. Guardrails para IA (SDD)

### Escopo Positivo (o que fazer)
- Documentar funções complexas com JSDoc/TSDoc.
- Tratar erros com mensagens padronizadas (`{"detail": "..."}` no backend) e estados de erro explícitos no frontend.
- Criar testes para cada nova funcionalidade de backend (`pytest`); validar o frontend com `npm run build` e checklist manual nesta entrega.
- Executar o auditor arquitetural ao final: `python -c "import audit_framework as a; a.ENDC=''; a.FrameworkAuditor('.').run()"` (o arquivo `audit_framework.py` não é alterado nesta entrega).

### Escopo Negativo (o que NÃO fazer - Anti-Patterns)
- **No Hard Deletes:** proibido `DELETE` físico; usar `deleted_at`.
- **No Secrets in Code:** nenhuma credencial ou chave no código; usar `.env`/`frontend/.env.example`.
- **No Refactoring Unasked:** não alterar infraestrutura ou configuração global sem instrução explícita no `SPEC.md`.
- **No New Dependencies:** não instalar bibliotecas não listadas neste documento.
- **No Manual Reprioritization:** operador nunca altera posição na fila; Área Gestora só com justificativa e auditoria.
