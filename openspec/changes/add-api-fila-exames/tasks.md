## 1. Configuração e provider AGHU

- [ ] 1.1 Adicionar `EXAME_PROVIDER_TYPE` (padrão `CSV`) em `src/config.py` e `.env.example` e verificar que `settings.EXAME_PROVIDER_TYPE` resolve para `CSV` sem `.env`
- [ ] 1.2 Adicionar `buscar_por_nome` em `ExameProviderInterface`, `ExameCsvProvider` e `ExamePostgresProvider` (+ `src/providers/sql/exames/buscar_por_nome.sql` com bind seguro) e verificar com teste do provider CSV (busca parcial sem acento/maiúsculas, vazio para menos de 3 caracteres)

## 2. Provider do SQLite local

- [ ] 2.1 Criar `FilaProviderInterface` e `FilaSqliteProvider` (itens ativos, item por id, itens por prontuário, existência de duplicata, atualização, regras de prioridade/exames/incompatibilidades ativas) e registrar a dependência em `src/dependencies.py`; verificar com teste que regras inativas/excluídas não são retornadas

## 3. Controller da fila

- [ ] 3.1 Criar `src/controllers/fila_controller.py` com montagem da fila (enriquecimento AGHU, `outros_exames`, `priorizar_fila`, `detectar_alertas`, filtros padrão de status, `filtrar_fila`, `apenas_24h_vencidos`, paginação) e verificar via testes de API da seção 5
- [ ] 3.2 Implementar detalhe do item (fila + AGHU do prontuário, alertas com AGHU, `orientacoes_preparo`, `404`) e verificar via testes da seção 5
- [ ] 3.3 Implementar máquina de estados (`TRANSICOES_PERMITIDAS`, prazo +24h, limpeza ao voltar para `NA_FILA`, exigência de data na confirmação, bloqueio para higienização ≠ `VALIDA`) com auditoria `ALTERAR_STATUS_FILA` e verificar via `tests/test_status_fila.py`
- [ ] 3.4 Implementar vinculação de solicitação (valida no AGHU, `400`/`404`/`409`, atualiza para `VALIDA`) com auditoria `VINCULAR_SOLICITACAO` e verificar via testes da seção 5

## 4. Schemas e router

- [ ] 4.1 Criar `src/schemas/fila.py` (camelCase, enums para `422`) e verificar que a serialização de um item gera as chaves do `IItemFila`
- [ ] 4.2 Criar `src/routers/exames.py` com `dependencies=[Depends(auth_handler.decode_token)]`, os 5 endpoints e `X-Total-Count`; registrar em `src/main.py` e verificar que `/docs` lista as rotas e que chamada sem token retorna `401`

## 5. Testes de API

- [ ] 5.1 Criar fixtures locais (SQLite temporário, login mock, seed de regras, inserção de itens) em `tests/test_api_fila_exames.py` e verificar que rodam isoladas do `data/app.db`
- [ ] 5.2 Testar listagem: ordem Oncologia × rotina, campos camelCase, itens finalizados fora por padrão, filtro `regiao` preservando score, `apenas_24h_vencidos`, paginação com `X-Total-Count`, `422` para região inválida, `401` sem token
- [ ] 5.3 Testar detalhe: `outrosExames` com origem `AGHU`, alerta de incompatibilidade vindo do AGHU, `404`
- [ ] 5.4 Testar status em `tests/test_status_fila.py`: início do aguardo com prazo exato de +24h, confirmação com data, confirmação sem data (`400`), transição inválida (`400`), retorno a `NA_FILA` limpando prazos, alerta `PRAZO_24H_VENCIDO`, registro em `audit_logs` com usuário/IP/antes/depois e ausência de log em rejeição
- [ ] 5.5 Testar vinculação (`200` com auditoria, `404`, `409`, `400` para item `VALIDA`) e busca ativa (prontuário, nome, sem parâmetros `400`, sem resultados lista vazia)

## 6. Verificação final

- [ ] 6.1 Rodar `.venv/bin/python -m pytest -q` e confirmar todos os testes passando (existentes + 3 changes)
- [ ] 6.2 Rodar `python audit_framework.py .` e confirmar 100% nos 11 pilares
- [ ] 6.3 Subir o backend (`./dev.sh` ou uvicorn) e verificar manualmente no Swagger `/docs` o fluxo: login → `GET /fila` → iniciar 24h → confirmar com data → conferir `GET /api/admin/audit-logs` (se a branch do Arthur já estiver integrada) ou a tabela `audit_logs`
