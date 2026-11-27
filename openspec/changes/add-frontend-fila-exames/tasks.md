## 1. Tipos e camada de dados (TASK-012)

- [x] 1.1 Criar `frontend/src/types/exames.ts` (contratos da seção 4 de `05-interfaces.md`, detalhe, requests, filtros snake_case, linha do AGHU snake_case, `TRANSICOES_PERMITIDAS`, `HIGIENIZACAO_VINCULAVEL`)
- [x] 1.2 Criar `frontend/src/services/requisicao.ts` (`mensagemErro`, `executar`)
- [x] 1.3 Criar `frontend/src/stores/exames.ts` (fila paginada com `X-Total-Count`, detalhe, status, busca AGHU, vínculo)
- [x] 1.4 Criar `frontend/src/stores/regras.ts` (CRUD de `/api/regras/*` com as suposições do `design.md`)
- [x] 1.5 Criar `frontend/src/stores/dashboard.ts` (`GET /api/dashboard/kpis` conforme a branch da TASK-011)

## 2. Tela da fila (TASK-013)

- [x] 2.1 Adicionar slot opcional por célula no `DataTable.vue` e prop opcional de largura no `Modal.vue`, sem mudar o comportamento padrão
- [x] 2.2 Criar `frontend/src/views/FilaExames.vue`: tabela na ordem da API, score com tooltip, badges de alertas `ALTA`/`MEDIA`, status e prazo de 24h
- [x] 2.3 Filtros (exame, unidade, status, higienização, município, região, TFD, 24h vencidos, busca) e paginação `limit`/`offset`
- [x] 2.4 Modal de detalhe (outros exames, todos os alertas, motivos, orientações de preparo)
- [x] 2.5 Modal de status (transições permitidas, data/hora obrigatória na confirmação, preparo orientado, observações, bloqueio para higienização ≠ `VALIDA`)
- [x] 2.6 Modal de busca ativa (prontuário, solicitação ou nome com 3+ letras) e vinculação, só para `NAO_ENCONTRADA`/`DIVERGENCIA_EXAME`
- [x] 2.7 Rota `/fila` com `requiresAuth` e link no menu lateral

## 3. Verificação

- [x] 3.1 Rodar `npm run build` em `frontend/` sem erros
- [x] 3.2 Popular o SQLite local com `python -m src.resources.seed_exames` e um script temporário (fora do repositório) com itens baseados em `data/exames_aghu_mock.csv` cobrindo status, alertas e higienizações
- [x] 3.3 Validar no navegador (login `admin`/`admin`): ordem, tooltip, badges, filtros, paginação, detalhe, transições (incluindo horário da confirmação), busca ativa e vínculo
- [x] 3.4 Apagar o script temporário e confirmar que `data/app.db` não aparece no `git status`
- [x] 3.5 Rodar `uv run python -m pytest -q` e confirmar todos os testes passando
- [x] 3.6 Rodar `python audit_framework.py .` e confirmar 100% nos 11 pilares
