## Context

- Golden sample `paciente` usa `get_paciente_provider(STRATEGY)`; o Komata já criou `get_exame_provider(strategy)` com `ExameCsvProvider` (`data/exames_aghu_mock.csv`) e `ExamePostgresProvider`.
- O Arthur, para o dashboard, criou um padrão de provider do SQLite local (`DashboardSqliteProvider` recebendo `AsyncSession`) e schemas Pydantic em `src/schemas/` com `alias_generator=to_camel`. Seguimos o mesmo para manter o projeto coerente.
- `registrar_auditoria()` faz `commit` sozinho; o token (`auth_handler.decode_token`) traz o usuário em `sub`.
- `src/main.py` cria as tabelas no startup com `Base.metadata.create_all` no SQLite de `SQLITE_DSN`/`APP_DB_URL`, o que permite testes com banco temporário.
- O `tests/conftest.py` do `master` usa `data/app.db` real; a branch do Arthur muda isso. Para não conflitar, os fixtures desta change ficam nos próprios arquivos de teste.

## Goals / Non-Goals

**Goals:**
- Router fino; regra de negócio no controller; acesso a dados só via providers.
- Contrato estável para o Pedro (`IItemFila`, `IAlertaExame`).

**Non-Goals:**
- RBAC por perfil, cache, websockets/atualização em tempo real.

## Decisions

1. **Camadas e arquivos**
   - `src/providers/interfaces/fila_provider_interface.py` + `src/providers/implementations/fila_sqlite_provider.py`: `listar_itens_ativos()`, `obter_item(id)`, `listar_por_prontuario(prontuario)`, `existe_item_ativo(prontuario, codigo_exame, excluir_id)`, `atualizar_item(item, campos)`, `listar_regras_prioridade()`, `listar_regras_exames()`, `listar_incompatibilidades()` — retornam dicts (regras já filtradas por `ativo`/`deleted_at`).
   - `src/controllers/fila_controller.py`: orquestra — carrega itens + regras, enriquece com AGHU (`listar_exames()` uma vez, indexado por `(codigo_solicitacao, codigo_exame)`), monta `outros_exames` por prontuário, chama `priorizar_fila`, `detectar_alertas`, `filtrar_fila`, pagina; aplica a máquina de estados e chama `registrar_auditoria`.
   - `src/schemas/fila.py`: `ItemFila`, `AlertaExame`, `OutroExame`, `ItemFilaDetalhe`, `AtualizarStatusRequest`, `VincularSolicitacaoRequest`, enums `RegiaoGeografica`, `StatusOperacional`, `StatusHigienizacao` (o handler global do framework converte erro de validação em `400`).
   - `src/routers/exames.py`: endpoints, `Depends` do provider da fila, do provider AGHU, do usuário (`decode_token`) e `Request` para o IP.
   - Alternativa: SQLAlchemy direto no controller. Rejeitada — quebra a regra de camadas do `AGENTS.md` e o auditor verifica camadas.

2. **Máquina de estados como tabela de dados no controller** (`TRANSICOES_PERMITIDAS: dict[str, set[str]]`). Não é regra configurável pela gestão (é o fluxo validado em 06/11), então fica em código, como os enums.

3. **Prazo 24h**: `agora = datetime.now(timezone.utc).replace(tzinfo=None)` (mesmo padrão UTC sem fuso dos KPIs); `prazo = agora + timedelta(hours=24)`. `agora` é injetável (parâmetro do controller) para os testes verificarem o cálculo exato.

4. **Auditoria**: `dados_anteriores`/`dados_novos` contêm só os campos alterados (`status_operacional`, `contato_iniciado_em`, `prazo_confirmacao_em`, `data_agendada_aghu`, `preparo_orientado`, `observacoes` ou, no vínculo, `codigo_solicitacao`, `codigo_exame`, `prontuario`, `status_higienizacao`). A atualização do item e o log são gravados na mesma sessão; `registrar_auditoria` faz o commit de ambos.

5. **Busca por nome no AGHU**: novo método `buscar_por_nome(nome)` na interface do Komata. CSV: filtro "contém" sem acento/maiúsculas. Postgres: `buscar_por_nome.sql` com `pac.nome ILIKE :nome` (bind seguro, `LIMIT 200`). Alternativa: filtrar `listar_exames()` no controller — rejeitada por trazer o AGHU inteiro em produção.

6. **Estratégia do provider AGHU** vem de `settings.EXAME_PROVIDER_TYPE` (padrão `CSV`), em vez de constante no router, seguindo a governança de configuração (`src/config.py` + `.env.example`).

7. **Paginação** por `limit`/`offset` + `X-Total-Count`, mantendo o corpo como lista simples (`IItemFila[]`), compatível com o contrato TypeScript existente. Sem `limit`, retorna tudo (fila da Central é de centenas de itens).

8. **Data de referência para "retorno próximo"**: data local `America/Recife` (`zoneinfo`) derivada de `agora`.

9. **Testes**: fixture local cria `TestClient` com `SQLITE_DSN` em `tmp_path`, faz login `admin/admin` com `MockAuthProvider`, roda `seed_regras_iniciais` e insere itens via sessão síncrona no mesmo arquivo. Provider AGHU sobrescrito com `app.dependency_overrides` apontando para um CSV de teste quando o cenário exigir dados específicos.

## Risks / Trade-offs

- [Conflito de merge com a branch do Arthur em `main.py`, `dependencies.py`, `schemas/__init__.py`] → mudanças só de adição; resolver na hora do merge.
- [Alterar a interface do provider AGHU do Komata] → método novo, sem mudar os existentes; os testes do provider CSV continuam passando.
- [Listagem recalcula score/alertas a cada requisição] → custo O(n) em memória para centenas de itens, aceitável; garante que mudança de peso reflita na hora.
- [Sem RBAC por perfil, qualquer usuário autenticado altera status] → documentado como fora de escopo; o router aceita adicionar `Depends(verificar_perfil(...))` depois sem mudar o contrato.

## Migration Plan

Sem migração de banco (tabelas já criadas pela TASK-005). Deploy: definir `EXAME_PROVIDER_TYPE=POSTGRES` em produção. Rollback: remover o `include_router`.
