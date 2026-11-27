## Why

Hoje a prioridade da fila depende da memória da atendente olhando a planilha (risco de falha humana em regras como Oncologia ou hemodiálise). A TASK-008 do `SPEC.md` pede um motor **determinístico, explicável e configurável** (RF005, RF006, RNF006, CARE-RF005, CARE-UC003) que ordene a fila a partir dos pesos da tabela `regras_prioridade` e permita o filtro geográfico de urgência sem mexer na prioridade clínica.

## What Changes

- Novo motor de priorização que, para cada item de `acompanhamento_fila`, calcula `score_prioridade` e a lista `motivos_prioridade` (ex.: `"Oncologia +100"`, `"Retorno em até 15 dias +20"`) lendo **apenas** as regras ativas e não excluídas de `regras_prioridade`.
- Ordenação determinística da fila: score decrescente → data de solicitação crescente → id crescente.
- Funções de filtro operacional (exame, unidade, status, município, região `CAPITAL | RMR | INTERIOR | NAO_INFORMADO`, apenas TFD, busca por prontuário/solicitação/nome) aplicadas **depois** do cálculo do score, garantindo que o filtro nunca altere a pontuação.
- Testes `pytest` unitários cobrindo os três critérios de avaliação do CARE-RF005.
- Não expõe endpoint: a API (`GET /api/exames/fila`) é entregue na change `add-api-fila-exames` (TASK-010), que consome este motor.

## Capabilities

### New Capabilities
- `priorizacao-fila`: cálculo determinístico e explicável do score de prioridade clínica a partir de regras configuráveis, ordenação da fila e filtros operacionais/geográficos que preservam o score.

### Modified Capabilities
(nenhuma — não há specs existentes em `openspec/specs/`)

## Dependências

- **TASK-004/005 (Komata) — pronta** na branch base `feat/fase-1-fundacao-aghu`: models `AcompanhamentoFila`, `RegraPrioridade` e seed com os pesos padrão.
- **TASK-006 (Eduardo) — não bloqueante:** o CRUD `PUT /api/regras/prioridades/{id}` ainda não existe; o teste "alterar peso muda a ordem" altera o registro direto no SQLite. Quando o CRUD existir, o mesmo comportamento vale porque o motor relê as regras a cada chamada.
- **Consumida por:** TASK-010 (`add-api-fila-exames`) e, indiretamente, TASK-013 (Pedro, tela da fila).

## Fora de escopo

- CRUD/telas de edição de pesos (TASK-006 / TASK-015).
- Endpoint HTTP da fila (TASK-010).
- Priorização por idade real do paciente: o AGHU/CSV atual não traz `data_nascimento`; vulneráveis são identificados por especialidade/unidade solicitante ou `grupo_prioritario_manual`.
- Qualquer escrita no AGHU.

## Impact

- Novo código em `src/controllers/priorizacao_controller.py` (lógica pura) e testes em `tests/test_priorizacao.py`.
- Leitura de `regras_prioridade` via provider do SQLite local (definido em `add-api-fila-exames`; nesta change o motor recebe as regras como parâmetro).
- Sem novas dependências, sem migração.
