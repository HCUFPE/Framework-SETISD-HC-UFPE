## Context

- Backend da fila (TASK-010) no `master`: `src/routers/exames.py`, `src/schemas/fila.py` e `src/controllers/fila_controller.py`. Respostas da fila em camelCase (`alias_generator=to_camel`); query params em snake_case; `GET /api/exames/aghu/buscar` devolve as linhas do provider AGHU em snake_case (`prontuario`, `nome`, `codigo_solicitacao`, `codigo_exame`, `nome_exame`, `data_solicitacao`, `unidade_solicitante`...).
- Datas: o SQLite guarda UTC sem fuso e o Pydantic serializa sem `Z` (`contatoIniciadoEm`, `prazoConfirmacaoEm`, `dataAgendadaAghu`, `outrosExames[].dataAgendada`). `dataSolicitacao` vem do AGHU (hora local, sem fuso) ou cai para `created_at`; `dataRetornoMedico` é uma data (`YYYY-MM-DD`).
- Sem filtro de status, a API só devolve itens `VALIDA` em `NA_FILA`, `AGUARDANDO_CONFIRMACAO_24H` ou `SEM_RESPOSTA_24H`. Itens `NAO_ENCONTRADA`/`DIVERGENCIA_EXAME` só aparecem filtrando pela higienização.
- Frontend: Vue 3 + Pinia (setup stores, como `auth.ts`), Axios com interceptadores em `services/api.ts` (não alterar), toasts com `vue-toastification`, componentes base `DataTable`, `Modal`, `Card`, `Button`.

## Goals / Non-Goals

**Goals:**
- Tipos e stores reutilizáveis pelas próximas telas (TASK-015/016).
- Tela da fila que só oferece ações que o backend aceita (sem erro 400 previsível).

**Non-Goals:**
- Reordenar, recalcular score ou alertas no frontend.
- Cache, atualização em tempo real (websocket) ou testes unitários de frontend.

## Decisions

1. **Arquivos por camada (frontend)**
   - Tipos: `frontend/src/types/exames.ts`.
   - Serviço: `frontend/src/services/requisicao.ts` (`mensagemErro()` lê `response.data.detail`; `executar()` liga/desliga o loading, limpa e preenche o erro e devolve `null` em falha). O `api.ts` fica intacto.
   - Stores: `frontend/src/stores/exames.ts`, `regras.ts`, `dashboard.ts`. Ações devolvem o dado (ou `true`) em sucesso e `null` em falha; o erro fica no estado da store para a view exibir. Cada área da store de exames tem seu par loading/erro (fila, detalhe, ação, busca AGHU) para um modal não sujar a tabela.
   - View: `frontend/src/views/FilaExames.vue`; rota `/fila` com `meta.requiresAuth`.
   - Alternativa: chamar `api` direto na view (como `Pacientes.vue`). Rejeitada — a TASK-012 pede stores e as telas seguintes reaproveitam.

2. **Ordem da fila**: a tabela mostra `itens` exatamente como a API devolve; a posição exibida é `offset + índice + 1`.

3. **Paginação**: `limit`/`offset` como query params e total lido de `X-Total-Count` (o Axios expõe em minúsculas). Mudar filtro volta para a página 1.

4. **Datas**
   - Campos UTC sem fuso: o frontend acrescenta `Z` antes de criar o `Date` (se já houver `Z` ou offset, usa como veio) e exibe no fuso do navegador (`pt-BR`).
   - `dataRetornoMedico` e `dataSolicitacao`: exibidas como data (`dd/mm/aaaa`) a partir da string, sem conversão de fuso (evita o dia anterior por causa do UTC).
   - Envio de `dataAgendadaAghu`: o `datetime-local` é interpretado no fuso do navegador e enviado com `toISOString()` (ISO com `Z`). O backend converte para UTC e devolve sem `Z`; a regra acima mostra o mesmo horário digitado.
   - Prazo de 24h: a tela recalcula "vencido" contra o relógio a cada minuto, além do alerta `PRAZO_24H_VENCIDO` da API.

5. **Transições de status**: `TRANSICOES_PERMITIDAS` em `types/exames.ts` espelha `fila_controller.TRANSICOES_PERMITIDAS`. O modal lista só os destinos do status atual; `CONFIRMADO_AGENDADO_AGHU` exige data/hora; itens com higienização diferente de `VALIDA` não abrem o formulário. O backend continua sendo a validação final e o `detail` de erro é exibido.
   - Alternativa: endpoint de transições no backend. Rejeitada — fora do escopo (não alterar backend); a duplicação fica documentada no código.

6. **Busca ativa**: só para `NAO_ENCONTRADA`/`DIVERGENCIA_EXAME` (`HIGIENIZACAO_VINCULAVEL`). Um campo por vez (prontuário, solicitação ou nome); nome exige 3 letras no frontend (mesma regra do backend). Cada resultado tem "Vincular", que chama `PATCH /fila/{id}/vincular-solicitacao` com `codigoSolicitacao` e `codigoExame` da linha.

7. **Alertas**: tabela mostra só `ALTA` e `MEDIA`; o detalhe mostra todos, incluindo `INFO`. Motivos do score em tooltip nativo (`title`) na tabela e em lista no detalhe.

8. **Componentes base**: `DataTable.vue` ganha slot opcional `cell-<coluna>` (padrão: o texto atual); `Modal.vue` ganha prop `largura` (padrão `max-w-lg`). Nenhuma tela existente muda.

9. **Suposições da store `regras.ts`** (TASK-006 ainda não existe):
   - Rotas `/api/regras/prioridades`, `/api/regras/exames`, `/api/regras/incompatibilidades` com `GET` (lista), `POST` (cria), `PUT /{id}` (atualiza) e `DELETE /{id}` (soft delete).
   - Corpo e resposta em camelCase nos formatos `IRegraPrioridade`, `IRegraExame`, `IIncompatibilidadeExame`; `POST`/`PUT` recebem o objeto sem `id` e devolvem o objeto salvo.
   - `GET` devolve lista simples sem paginação, com itens ativos e inativos (sem os excluídos); `DELETE` pode devolver `204` ou o objeto — a store só remove o item da lista local.
   - Erros `{"detail": ...}`; `403` para perfis sem permissão.

10. **Store `dashboard.ts`** segue o backend da branch do Arthur: `GET /api/dashboard/kpis` com `data_inicio`, `data_fim` (ISO 8601) e `codigo_exame` opcionais; resposta com os nove campos de `IKpiDashboard`; exige o grupo `GLO-SEC-HCPE-SETISD` (`403` para os demais).

## Risks / Trade-offs

- [`TRANSICOES_PERMITIDAS` duplicada] → se o fluxo mudar no backend, a tela pode esconder ou oferecer transição errada; o backend ainda rejeita com `400` e a mensagem aparece no modal.
- [Contrato de `/api/regras` suposto] → ajustar a store quando a TASK-006 for entregue.
- [`X-Total-Count` em outra origem] → hoje o frontend é servido na mesma origem (FastAPI ou proxy do Vite). Se for servido em outra origem, o backend precisa de `expose_headers`.
- [Fuso do navegador] → exibição e digitação usam o mesmo fuso, então ficam coerentes entre si; em máquinas fora de `America/Recife` os horários aparecem no fuso local.

## Migration Plan

Sem migração. Deploy: `npm run build` gera `src/static/dist`, servido pelo FastAPI. Rollback: remover a rota `/fila` e o link do menu.
