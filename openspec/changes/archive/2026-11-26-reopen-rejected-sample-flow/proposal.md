## Why

No fluxo do Serviço de Anatomia Patológica (SAP/HC-UFPE), quando uma amostra é rejeitada na recepção ou devolvida por não conformidade (por exemplo, falta de carimbo/assinatura, identificação ilegível ou divergência de frasco), ela retorna à unidade de origem com status `AGUARDANDO_NOVA_AMOSTRA`. Após a regularização pela unidade solicitante, o material retorna ao laboratório sob a **mesma solicitação do AGHU** para seguir o fluxo normal.

Atualmente, o endpoint `PATCH /api/ap/devolucoes/{devolucao_id}/situacao` (`ReceptionController.atualizar_situacao_devolucao`) apenas altera `ApDevolucao.situacao` para `NOVA_AMOSTRA_RECEBIDA` e marca `ApNaoConformidade.status` como `RESOLVIDA`, **mas mantém `ApSolicitacao.situacao_recepcao` travada em `"DEVOLVIDA"` e `ApCaso.status` travado em `"DEVOLVIDO"`**. Como consequência, ao bipar ou consultar a solicitação regularizada, o sistema continua classificando o item como `"DEVOLVIDA"` e bloqueia o recebimento ou a continuidade do caso.

Para corrigir esse fluxo com segurança clínica e rastreabilidade:
1. A reabertura deve obedecer estritamente às regras de transição de estado de `ApSolicitacao`, `ApDevolucao` e `ApCaso`, impedindo que exames cancelados (`CANCELADA` / `CANCELADO`) ou devoluções definitivamente encerradas (`ENCERRADA`) sejam reabertos.
2. Todos os registros anteriores da rejeição (motivo, autor, datas de devolução e regularização) devem permanecer **imutáveis** no histórico e na trilha de auditoria para cálculo fiel de SLA e rastreabilidade completa do ciclo de vida da amostra.

## What Changes

- **Matriz formal de transição de estados e bloqueios (`ApSolicitacao`, `ApDevolucao` e `ApCaso`):**
  - Ao atualizar uma devolução para `situacao = "NOVA_AMOSTRA_RECEBIDA"` via `PATCH /api/ap/devolucoes/{devolucao_id}/situacao` (protegido por `Permissao.DEVOLUCOES_ALTERAR_SITUACAO`):
    - **Bloqueio de estados terminais (HTTP 409):** recusa a reabertura se `ApDevolucao.situacao` já estiver `"ENCERRADA"`, se qualquer grupo `ApSolicitacao` vinculado estiver em `"CANCELADA"` ou `"RECEBIDA"`, ou se o `ApCaso` vinculado estiver em `"CANCELADO"` (ou em qualquer status diferente de `"DEVOLVIDO"`).
    - **Bloqueio de retrocesso após reabertura (HTTP 409):** impede reverter `NOVA_AMOSTRA_RECEBIDA` de volta para `AGUARDANDO_NOVA_AMOSTRA` caso a solicitação já tenha sido recebida ou cancelada posteriormente.
- **Reabertura de solicitação rejeitada na recepção (`devolucao.caso_numero is None`):**
  - Todos os grupos `ApSolicitacao` listados em `devolucao.solicitacaoIds` que estejam em `situacaoRecepcao == "DEVOLVIDA"` (e vinculados àquela `devolucao_id`) retornam para `situacaoRecepcao = "AGUARDANDO_RECEBIMENTO"` com `devolucaoId = null`.
  - A solicitação volta imediatamente para a fila `GET /api/ap/solicitacoes/pendentes` e passa a responder como `"PENDENTE"` na leitura (`GET /api/ap/solicitacoes/{codigo}`), habilitando a conferência e confirmação de entrada normais.
- **Vinculação histórica automática no recebimento pós-regularização (preservação de SLA):**
  - Quando um grupo `ApSolicitacao` reaberto é recebido em `confirmar_entrada` (ou `vincular_ihq`), o backend vincula automaticamente os registros históricos de `ApNaoConformidade` e `ApDevolucao` daquele `solicitacaoId` ao novo `casoNumero` e registra um evento imutável `FLUXO_REABERTO` em `ApHistoricoCaso` citando a devolução regularizada.
  - Os timestamps originais da rejeição (`registradoEm` / `devolvidaEm`) e da regularização permanecem intactos para cálculo de SLA entre rejeição, regularização e entrada efetiva no SAP.
- **Reabertura de caso já existente devolvido (`devolucao.caso_numero is not None`):**
  - Quando a devolução regularizada pertence a um `ApCaso` existente em status `"DEVOLVIDO"`, o caso retorna ao status ativo (`"RECEBIDO"` ou ao status anterior à devolução registrado no payload da ocorrência) e recebe um evento imutável `FLUXO_REABERTO` em `ApHistoricoCaso`, mantendo os eventos anteriores (`NAO_CONFORMIDADE` e `DEVOLUCAO`) preservados na linha do tempo.
- **Auditoria transacional (`AuditLog`):**
  - A operação registra na mesma transação do banco os estados anteriores e novos de `ApDevolucao`, `ApSolicitacao` e `ApCaso`, autoria derivada do token JWT e `ip_origem`.
- **Feedback e atalhos no frontend (`RejeicoesDevolucoes.vue`, `PassoConferencia.vue` e `DetalheCaso.vue`):**
  - Na tela de Devoluções (`RejeicoesDevolucoes.vue`), ao marcar `"Nova amostra recebida"`, exibe confirmação de que o fluxo foi reaberto e oferece atalho direto para abrir a solicitação na Recepção (quando rejeitada antes da entrada) ou abrir o caso reaberto (quando já possuía número interno).
  - Na Conferência (`PassoConferencia.vue`) e no Detalhe do Caso (`DetalheCaso.vue`), exibe alerta informativo de que o item possui histórico de devolução regularizada, mantendo visíveis as ocorrências anteriores.

## Capabilities

### New Capabilities
- `rejected-sample-reopening`: reabertura controlada do fluxo de amostras rejeitadas (`ApSolicitacao` e `ApCaso`) após regularização (`NOVA_AMOSTRA_RECEBIDA`), com guarda estrita contra reabertura de itens cancelados ou encerrados e preservação integral do histórico para auditoria e SLA.

### Modified Capabilities
- `nonconformity-return`: acoplamento da transição `NOVA_AMOSTRA_RECEBIDA` em `PATCH /api/ap/devolucoes/{devolucao_id}/situacao` à reabertura dos grupos de solicitação ou do caso devolvido, além do vínculo automático de devoluções pré-recepção ao caso gerado posteriormente.
- `sample-reception`: reingresso de solicitações regularizadas na fila pendente e exibição do contexto de rejeição prévia durante a nova conferência.
- `case-detail`: exibição do evento de reabertura de fluxo e das não conformidades/devoluções ocorridas antes do recebimento na linha do tempo e nas abas do caso.

## Impact

- **Backend:**
  - `src/providers/interfaces/reception_provider_interface.py` e `src/providers/implementations/reception_sqlite_provider.py`: validação das regras de transição de estado em `atualizar_situacao_devolucao` (reabertura atômica de `ApSolicitacao` ou `ApCaso` com bloqueio para `CANCELADA`/`CANCELADO`/`ENCERRADA`) e método auxiliar para vincular `ApNaoConformidade` e `ApDevolucao` prévias ao `caso_numero` gerado após regularização.
  - `src/controllers/reception_controller.py`: orquestração da reabertura, gravação do evento `FLUXO_REABERTO` no histórico do caso, vínculo histórico em `confirmar_entrada` / `vincular_ihq` e enriquecimento do log em `AuditLog`.
  - `tests/test_reception_api.py`: suíte de testes cobrindo rejeição na recepção → regularização (`NOVA_AMOSTRA_RECEBIDA`) → novo recebimento com preservação de histórico/SLA; devolução de caso → regularização → reabertura de caso; e bloqueio (HTTP 409) ao tentar reabrir solicitação `CANCELADA`, caso `CANCELADO` ou devolução `ENCERRADA`.
- **Frontend:**
  - `frontend/src/views/ap/RejeicoesDevolucoes.vue`: feedback visual de reabertura e link de navegação rápida para receber a solicitação regularizada ou acessar o caso reaberto.
  - `frontend/src/components/ap/recepcao/PassoConferencia.vue` e `frontend/src/views/ap/DetalheCaso.vue`: aviso contextual de regularização prévia e exibição completa do histórico imutável de ocorrências.
- **Dados / Banco:** Nenhuma alteração estrutural de schema ou nova migração Alembic necessária — os modelos `ApSolicitacao`, `ApDevolucao`, `ApNaoConformidade`, `ApCaso` e `ApHistoricoCaso` já comportam os campos e metadados necessários.