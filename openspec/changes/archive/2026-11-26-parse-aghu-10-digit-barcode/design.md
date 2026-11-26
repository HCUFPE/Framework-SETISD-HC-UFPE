# Design: Leitura de código de barras de 10 dígitos do AGHU

## Context

Veja `proposal.md` (Why) para a motivação de negócio. Atualmente, `ReceptionController.ler_solicitacao` em `src/controllers/reception_controller.py` normaliza a entrada e remove apenas sufixos `:<TIPO>` ou `-<amostra>` numérico antes de consultar `provider.listar_exames_da_solicitacao(codigo_solicitacao)`. Quando a etiqueta do frasco do AGHU é bipada diretamente (10 dígitos contínuos: 7 dígitos da solicitação + 3 dígitos da amostra), a busca falha com `NAO_ENCONTRADA`. No frontend, `useRecepcaoStore.iniciarConferencia` (`frontend/src/stores/recepcao.ts`) recebe todos os grupos pendentes e `PassoConferencia.vue` marca todos com `receber = true` por padrão, sem destacar ou filtrar pela amostra bipada.

Conforme `data/dicionario_dados.md`, o script SQL de extração do AGHU e o mapeamento em `src/controllers/solicitacao_controller.py`, os registros extraídos do AGHU chegam com uma linha por amostra contendo o código da solicitação como inteiro de **7 dígitos** (`codigoSolicitacao`, ex.: `7712340`) e o número da amostra como inteiro **sem zeros à esquerda** (`numeroAmostra`, ex.: `1`, `2`, `10`). Na etiqueta física impressa pelo AGHU, o código de barras concatena esses dois valores formatando a amostra em **3 dígitos com zeros à esquerda** (`7712340001`), totalizando **10 dígitos contínuos**.

## Goals / Non-Goals

**Goals:**
- Decompor de forma determinística códigos numéricos contínuos de 10 dígitos em `codigo_solicitacao` (`[:7]`) e `numero_amostra` (`[7:]`), mantendo retrocompatibilidade total com `<solicitação>`, `<solicitação>-<amostra>` e `<solicitação>:<tipo>`.
- Resolver o grupo de exame dono da amostra bipada com comparação tolerante a zeros à esquerda (`"001"` == `"1"`).
- Enriquecer o retorno de `GET /api/ap/solicitacoes/{codigo}` de forma retrocompatível (mantendo `exames` com todos os pendentes) com metadados da amostra bipada (`amostraBipada`, `grupoSelecionadoId`, `examesFiltrados` e status caso a amostra bipada já tenha sido recebida/devolvida).
- Pré-selecionar e destacar o grupo correspondente na conferência (`PassoConferencia.vue` / `DadosSolicitacao.vue`), mantendo opção explícita para exibir/marcar os demais grupos pendentes da solicitação.

**Non-Goals:**
- Alterar o schema do banco de dados ou criar migrações Alembic.
- Modificar o formato das etiquetas internas geradas pelo próprio SAP (`sample-labels`).
- Alterar o contrato de `POST /api/ap/recebimentos` (continua recebendo por `solicitacaoId` = `<codigo>:<tipo>`).

## Decisions

### 1. Extração de código e amostra no backend (`_extrair_codigo_e_amostra`)
- **Decisão:** Extrair uma função pura `_extrair_codigo_e_amostra(codigo: str) -> tuple[str, str | None]` em `src/controllers/reception_controller.py` com a seguinte precedência:
  1. Normalizar (`strip().upper()`).
  2. Se contiver `:`, separar em `codigo_solicitacao = leitura.split(":", 1)[0]` e `amostra = None` (formato de chave de grupo).
  3. Senão, se `rsplit("-", 1)` produzir sufixo numérico (`partes[1].isdigit()`), usar `codigo_solicitacao = partes[0]` e `amostra = partes[1]`.
  4. Senão, se `leitura.isdigit() and len(leitura) == 10`, fatiar `codigo_solicitacao = leitura[:7]` e `amostra = leitura[7:]`.
  5. Caso contrário, manter `codigo_solicitacao = leitura` e `amostra = None`.
- **Alternativas consideradas:** Fazer o parsing apenas no frontend. Rejeitado porque chamadas diretas à API (`GET /api/ap/solicitacoes/{codigo}`) e testes de API devem suportar o código de 10 dígitos nativamente e manter a regra de negócio centralizada no backend.

### 2. Comparação tolerante a zeros à esquerda e resolução da amostra
- **Decisão:** Normalizar o número da amostra para comparação via `_normalizar_numero_amostra(valor)` (`str(int(valor))` quando `valor.isdigit()`, senão `valor.strip().upper()`). Ao localizar a amostra nos grupos da solicitação:
  - Se encontrada em um grupo `AGUARDANDO_RECEBIMENTO`, retornar `grupoSelecionadoId = grupo["id"]` e `examesFiltrados = [grupo]`.
  - Se encontrada em um grupo já `RECEBIDA` ou `DEVOLVIDA` enquanto outros grupos seguem `AGUARDANDO_RECEBIMENTO`, manter `tipo = "PENDENTE"` (para não bloquear o recebimento dos demais) e incluir `amostraBipadaSituacao` com os detalhes do grupo já tratado (`grupoId`, `tipoExame`, `situacaoRecepcao`, `casoNumero`, `ihqCodigo`, `devolucaoId`).
  - Se todos os grupos da solicitação já estiverem `RECEBIDA` ou `DEVOLVIDA`, seguir o fluxo existente (`RECEBIDA` / `DEVOLVIDA`), incluindo `amostraBipada` quando presente.
- **Alternativas consideradas:** Bloquear a leitura retornando `RECEBIDA` ou `DEVOLVIDA` quando a amostra bipada já foi tratada mesmo havendo outros grupos pendentes. Rejeitado porque impediria o recepcionista de aproveitar a leitura para receber os demais frascos pendentes da solicitação.

### 3. Filtro e pré-seleção na interface de conferência
- **Decisão:** Estender `LeituraSolicitacao` em `frontend/src/types/ap.ts` com os campos opcionais `amostraBipada?: string | null`, `grupoSelecionadoId?: string | null`, `examesFiltrados?: SolicitacaoAghu[]` e `amostraBipadaSituacao?: ...`.
  - Em `useRecepcaoStore`, armazenar `amostraBipada`, `grupoSelecionadoId` e `amostraBipadaSituacao` (limpos em `reiniciar()` e quando a conferência é aberta pela fila de pendentes).
  - Em `PassoConferencia.vue`, quando `grupoSelecionadoId` estiver definido em solicitação com múltiplos grupos pendentes, inicializar apenas esse grupo com `receber = true` (demais com `false`), exibir apenas o grupo filtrado por padrão com um botão explícito `"Mostrar todos os exames pendentes (N)"` para expandir/marcar os demais quando necessário, e destacar a amostra bipada na tabela de `DadosSolicitacao.vue`.
  - Quando `amostraBipadaSituacao` indicar que a amostra bipada já foi recebida ou devolvida, exibir um `Alert` informativo no topo da conferência.

## Risks / Trade-offs

- **[Colisão com código de solicitação de 10 dígitos sem sufixo]** → Mitigado pelo padrão do AGHU no HC-UFPE onde solicitações têm 7 dígitos e códigos de barra de etiqueta têm exatamente 10 dígitos (`7 + 3`). Códigos com tamanho diferente de 10 dígitos não sofrem fatiamento.
- **[Recepcionista bipar um frasco e querer receber todos os grupos da solicitação de uma vez]** → Mitigado pelo botão explícito `"Mostrar todos os exames pendentes"` em `PassoConferencia.vue`, permitindo exibir e marcar os demais grupos com um clique.
