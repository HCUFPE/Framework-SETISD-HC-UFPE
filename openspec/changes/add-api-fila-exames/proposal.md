## Why

A Central precisa operar a fila pela interface: ver a fila priorizada com alertas, abrir o detalhe de um pedido, corrigir códigos de solicitação errados pela busca ativa no AGHU e controlar o ciclo de confirmação em 24h com trilha de auditoria. A TASK-010 do `SPEC.md` pede os endpoints `/api/exames/*` (RF004, RF005, RF006, RF008, CARE-RF008, CARE-UC004, CARE-UC005) que juntam o motor de priorização (TASK-008) e o detector de alertas (TASK-009). É também o contrato que a tela `FilaExames.vue` (TASK-013, Pedro) vai consumir.

## What Changes

- Novo router protegido `src/routers/exames.py` (`prefix="/api/exames"`, `dependencies=[Depends(auth_handler.decode_token)]`):
  - `GET /api/exames/fila` — fila priorizada com `scorePrioridade`, `motivosPrioridade` e `alertas`, com filtros por query (`codigo_exame`, `unidade`, `status_operacional`, `status_higienizacao`, `municipio`, `regiao`, `apenas_tfd`, `apenas_24h_vencidos`, `busca`) e paginação `limit`/`offset` com total no cabeçalho `X-Total-Count`.
  - `GET /api/exames/fila/{id}` — item + outros exames do prontuário (fila e AGHU) + alertas + orientações de preparo.
  - `PATCH /api/exames/fila/{id}/status` — máquina de estados `NA_FILA → AGUARDANDO_CONFIRMACAO_24H → CONFIRMADO_AGENDADO_AGHU | SEM_RESPOSTA_24H | CANCELADO`, prazo de 24h automático e auditoria `NEGOCIO_CLINICO`.
  - `PATCH /api/exames/fila/{id}/vincular-solicitacao` — vincula a solicitação correta encontrada no AGHU a um item `NAO_ENCONTRADA`/`DIVERGENCIA_EXAME`, com auditoria.
  - `GET /api/exames/aghu/buscar` — busca ativa somente-leitura no AGHU por `prontuario`, `codigo_solicitacao` ou `nome`.
- Respostas serializadas em camelCase conforme `IItemFila` / `IAlertaExame` de `05-interfaces.md` (mesmo padrão `alias_generator=to_camel` usado no dashboard do Arthur).
- Novo provider do SQLite local para a fila e as regras (interface + implementação), seguindo o fluxo Provider → Controller → Router.
- **Extensão do provider AGHU do Komata:** novo método `buscar_por_nome` na `ExameProviderInterface`, no `ExameCsvProvider` e no `ExamePostgresProvider` (com template SQL `buscar_por_nome.sql`).
- Nova variável `EXAME_PROVIDER_TYPE` (`CSV` | `POSTGRES`, padrão `CSV`) em `src/config.py` e `.env.example`.
- Testes `pytest` de API com SQLite temporário.

## Capabilities

### New Capabilities
- `api-fila-exames`: contrato HTTP da fila de exames — listagem priorizada e filtrável, detalhe com alertas, transições de status com prazo de 24h e auditoria, vinculação por busca ativa e busca no AGHU.

### Modified Capabilities
(nenhuma — `priorizacao-fila` e `alertas-exames` são consumidas sem mudança de requisito)

## Dependências

- **`add-motor-priorizacao` (TASK-008) e `add-detector-conflitos` (TASK-009):** devem ser implementadas antes.
- **TASK-001 a 005 (Komata) — pronta:** provider AGHU, models e seed.
- **TASK-007 (Eduardo) — não bloqueante:** a importação é quem povoa `acompanhamento_fila`; os testes inserem itens direto. Combinar com ele que itens com código errado entram como `NAO_ENCONTRADA` (é o que `vincular-solicitacao` corrige).
- **TASK-011 (Arthur) — já pronta:** os KPIs contam `status_operacional` e `prazo_confirmacao_em`; esta change grava exatamente esses valores.
- **TASK-013 (Pedro) — depende desta:** contrato `IItemFila` / `IAlertaExame`.

## Fora de escopo

- RBAC por perfil (`MARCADOR` × `CONSULTA`): o projeto ainda não tem tabela local de usuários/perfis; todas as rotas exigem autenticação, e a restrição por perfil fica para quando o RBAC local existir.
- Remarcação/faltas (transições a partir de `CONFIRMADO_AGENDADO_AGHU`).
- Escrita no AGHU (a efetivação continua manual na tela do AGHU).
- Importação do Forms (TASK-007) e CRUD de regras (TASK-006).

## Impact

- Novos arquivos: `src/routers/exames.py`, `src/controllers/fila_controller.py`, `src/providers/interfaces/fila_provider_interface.py`, `src/providers/implementations/fila_sqlite_provider.py`, `src/schemas/fila.py`, `src/providers/sql/exames/buscar_por_nome.sql`, `tests/test_api_fila_exames.py`, `tests/test_status_fila.py`.
- Alterados: `src/main.py` (registrar router), `src/dependencies.py` (fábrica do provider da fila), `src/config.py`, `.env.example`, `src/providers/interfaces/exame_provider_interface.py` e as duas implementações (método novo).
- Possível conflito simples de merge com a branch do Arthur em `src/main.py`, `src/dependencies.py` e `src/schemas/__init__.py` (inclusões em listas).
