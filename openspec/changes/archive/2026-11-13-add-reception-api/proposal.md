# Proposal

## Why

O módulo de Recepção já possui contratos estáveis de serviços, mas suas regras e seu estado oficial vivem em mocks em memória no navegador. Isso impede persistência compartilhada e deixa mutações sem enforcement de autorização no servidor. A mudança transfere essas operações existentes para a API FastAPI e mantém o Vue responsável pelas telas, componentes e navegação.

## What Changes

- Criar endpoints, modelos e persistência para as operações existentes de solicitações, casos, recebimentos, não conformidades, devoluções e acionamento de plantão; a impressão física permanece no navegador, sem registro de evento.
- Preservar os contratos de serviço consumidos pelas stores e views, substituindo gradualmente as implementações mock por chamadas HTTP.
- Usar a identidade autenticada e o catálogo de permissões definidos em add-sector-access-profiles, sem criar usuários, sessões ou RBAC paralelos.
- Aplicar autorização no backend em todas as consultas e mutações, negando por padrão operações sem permissão explícita ou ainda pendentes de validação SAP/HC.
- Registrar mutações no mecanismo de auditoria existente com autor autenticado, estado anterior e novo e IP de origem.
- Disponibilizar solicitações fictícias por um provedor de desenvolvimento/testes no backend, sem conexão real ao AGHU e sem permitir uso do mock em produção.

## Capabilities

### New Capabilities
- reception-api: API, persistência, autorização e adaptação HTTP para as operações já existentes da Recepção.

### Modified Capabilities

## Impact

- Backend: novos modelos SQLAlchemy, migração Alembic, interfaces e provedores, controllers e router AP; reutilização do banco APP_DB, das dependências de autenticação/autorização e do helper AuditLog existentes.
- Frontend: novas implementações HTTP sob os contratos de frontend/src/services/ap/types.ts e seleção delas em frontend/src/services/ap/index.ts; telas, navegação e stores permanecem no Vue.
- Dependência: add-sector-access-profiles deve fornecer a identidade normalizada e o catálogo de permissões consumidos pelas rotas. Esta mudança concretiza parte das tarefas ainda abertas daquele change, sem alterar seu catálogo.
- Fora de escopo: integração real com AGHU, AD/LDAP, SSO, OIDC, SAML, novas operações ou módulos de outros setores, gestão de usuários/perfis e mudanças nas regras de negócio existentes.
