## Why

A Central de Marcação precisa operar a fila pela interface web: ver a fila priorizada com o motivo do score, enxergar os alertas de conflito/preparo/retorno e o prazo de 24h, filtrar por região para vagas de última hora, abrir o detalhe do pedido, mudar o status e corrigir solicitações com código errado pela busca ativa no AGHU. A Fase 3 do `SPEC.md` pede isso em duas tasks do Pedro:

- **TASK-012:** tipos TypeScript (`frontend/src/types/exames.ts`) e stores Pinia (`exames.ts`, `regras.ts`, `dashboard.ts`).
- **TASK-013:** tela `FilaExames.vue` (fila priorizada, badges de alertas/24h, filtro geográfico, busca ativa e modal de status).

Requisitos atendidos: RF004, RF005, RF006, RF007 (exibição), RF008, CARE-RF005, CARE-RF008, CARE-UC003, CARE-UC004 e CARE-UC005.

## What Changes

- `frontend/src/types/exames.ts` com os contratos da seção 4 de `05-interfaces.md` (`IItemFila`, `IAlertaExame`, `IRegraPrioridade`, `IRegraExame`, `IIncompatibilidadeExame`, `IKpiDashboard`), os tipos do detalhe vindos de `src/schemas/fila.py` (`IOutroExame`, `IItemFilaDetalhe`), os corpos de request, os filtros (query params em snake_case) e a linha da busca no AGHU (resposta em snake_case).
- Stores Pinia (setup store, mesmo estilo de `auth.ts`) usando o `api.ts` existente, com estado de carregamento e mensagem de erro extraída de `{"detail": ...}`:
  - `exames.ts`: fila paginada (`limit`/`offset` + `X-Total-Count`), detalhe, mudança de status, busca no AGHU e vinculação.
  - `regras.ts`: CRUD de prioridades, regras por exame e incompatibilidades (`/api/regras/*`, ainda não implementado no backend — ver suposições no `design.md`).
  - `dashboard.ts`: KPIs de `GET /api/dashboard/kpis` (backend na branch `feat/task-011-dashboard-auditoria`).
- `frontend/src/services/requisicao.ts`: helper único de loading/erro usado pelas três stores.
- `frontend/src/views/FilaExames.vue`: fila na ordem da API, filtros, paginação, badges, modal de detalhe, modal de status e modal de busca ativa.
- Rota `/fila` (`requiresAuth`) e um link no menu lateral do `DefaultLayout.vue`.
- Extensões não destrutivas em componentes base: slot opcional por célula no `DataTable.vue` (o padrão continua sendo o texto da coluna) e prop opcional de largura no `Modal.vue` (padrão `max-w-lg`).

## Capabilities

### New Capabilities
- `frontend-fila-exames`: tela da fila de exames e camada de dados do frontend (tipos e stores) que consome `/api/exames`, `/api/regras` e `/api/dashboard`.

### Modified Capabilities
(nenhuma — o contrato `api-fila-exames` é consumido sem mudança)

## Dependências

- **TASK-010 (Gabriel) — pronta no `master`:** endpoints `/api/exames/*` e `TRANSICOES_PERMITIDAS`.
- **TASK-011 (Arthur) — branch `feat/task-011-dashboard-auditoria`, não mergeada:** `GET /api/dashboard/kpis`. Até o merge, a store recebe `404` e expõe o erro.
- **TASK-006 (Eduardo) — não iniciada:** `/api/regras/*`. A store segue o contrato de `05-interfaces.md`; ajustar se o backend divergir.
- **TASK-007 (Eduardo) — não iniciada:** a importação do Forms é quem povoa a fila. Até lá, a validação manual usa dados de teste inseridos no SQLite local (script temporário, fora do repositório).
- **TASK-015 (Murilo) e TASK-016 (Arthur):** consomem `regras.ts` e `dashboard.ts`; a TASK-016 reorganiza a navegação (aqui só entra o link mínimo da fila).

## Fora de escopo

- Telas de regras (TASK-015), dashboard (TASK-016) e importação (TASK-014).
- Reorganização do menu e das rotas além de `/fila` (TASK-016).
- Qualquer mudança no backend, nos interceptadores do Axios ou na autenticação.
- Ordenação da fila no frontend (a ordem é a da API) e dados mockados no frontend.
- Testes automatizados de frontend (o projeto não tem runner de testes no `frontend/`); a validação é `npm run build` (vue-tsc) e o fluxo manual no navegador.

## Impact

- Novos: `frontend/src/types/exames.ts`, `frontend/src/services/requisicao.ts`, `frontend/src/stores/exames.ts`, `frontend/src/stores/regras.ts`, `frontend/src/stores/dashboard.ts`, `frontend/src/views/FilaExames.vue`.
- Alterados: `frontend/src/router/index.ts` (rota `/fila`), `frontend/src/layouts/DefaultLayout.vue` (link), `frontend/src/components/DataTable.vue` (slot opcional), `frontend/src/components/Modal.vue` (prop opcional).
- Possível conflito simples com a TASK-016 em `router/index.ts` e `DefaultLayout.vue` (só adições).
