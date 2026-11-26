## Why

Durante a visita técnica ao Serviço de Anatomia Patológica (SAP/HC-UFPE) em 11/11, identificou-se uma lacuna operacional recorrente no recebimento de solicitações multi-exame do AGHU (como combinações de `HP + IHQ` ou `CO + HP`): frequentemente um dos exames solicitados não procede ou é dispensado clinicamente/administrativamente na recepção (por exemplo, pedido precipitado de imuno-histoquímica antes da análise morfológica), enquanto os demais exames da mesma solicitação precisam seguir normalmente na esteira.

Atualmente, o sistema oferece apenas duas saídas destrutivas ou inadequadas para esse cenário:
1. **Devolução por não conformidade (`POST /api/ap/nao-conformidades`):** destinada à rejeição física de material por falha de coleta/identificação, marcando o grupo como `DEVOLVIDA` e gerando fluxo de devolução à unidade de origem — o que não se aplica quando o material físico permanece no laboratório para outro exame da mesma solicitação.
2. **Cancelamento de caso (`POST /api/ap/casos/cancelamento`):** atua exclusivamente sobre um `ApCaso` já recebido e cancela o caso inteiro, não permitindo cancelar isoladamente um grupo de exame pendente (`<codigoSolicitacao>:<TIPO>`) antes da geração do caso.

Além disso, consolidar formalmente os estados terminais por grupo de exame em `ApSolicitacao` (`RECEBIDA`, `DEVOLVIDA` e `CANCELADA`) é pré-requisito arquitetural para o fluxo subsequente de reabertura após regularização, evitando que exames administrativamente cancelados sejam confundidos com amostras devolvidas por não conformidade ou tratados como `NAO_ENCONTRADA` na leitura.

## What Changes

- **Novo estado terminal `CANCELADA` no ciclo de vida do grupo de exame (`ApSolicitacao`):**
  - Cada grupo `<codigoSolicitacao>:<TIPO>` passa a admitir `situacaoRecepcao = "CANCELADA"` além de `"AGUARDANDO_RECEBIMENTO"`, `"RECEBIDA"` e `"DEVOLVIDA"`.
  - O cancelamento é estritamente lógico (sem exclusão física do registro) e persiste metadados de cancelamento (`motivo`, `canceladoPor`, `canceladoEm`) no payload da solicitação local.
- **Endpoint dedicado para cancelamento granular por exame (`POST /api/ap/solicitacoes/cancelamento`):**
  - Recebe `solicitacaoId` (`<codigoSolicitacao>:<TIPO>`) e `motivo` obrigatório (não vazio).
  - Exige permissão `Permissao.CASOS_CANCELAR` (mesma governança de RBAC do cancelamento de caso) e deriva o responsável exclusivamente das claims assinadas do token JWT.
  - Valida que o grupo existe e está em `AGUARDANDO_RECEBIMENTO` (retornando HTTP 404 se inexistente e HTTP 409 se já estiver `RECEBIDA`, `DEVOLVIDA` ou `CANCELADA`).
  - Altera apenas o grupo alvo para `CANCELADA`, preservando intactos os demais grupos da mesma solicitação AGHU (`HP`, `CO`, `CG`, `CCV`, `IHQ`).
- **Consolidação dos estados terminais na leitura e na fila (`ReceptionController`):**
  - `listar_solicitacoes_pendentes` e `contar_solicitacoes_pendentes` continuam considerando apenas grupos em `AGUARDANDO_RECEBIMENTO`; se uma solicitação tinha `HP` + `IHQ` e o `IHQ` é cancelado, ela permanece na fila apenas com o `HP`.
  - `ler_solicitacao` mantém a precedência de grupos pendentes → recebidos → devolvidos e passa a retornar classificação explícita `"CANCELADA"` (com motivo, autor e data/hora) quando todos os grupos da solicitação tiverem sido cancelados, evitando falso retorno de `"NAO_ENCONTRADA"`.
- **Trilha de auditoria imutável (`AuditLog`):**
  - Toda operação de cancelamento por exame registra evento na mesma transação do banco (`categoria = "NEGOCIO_CLINICO"`, `acao = "SOLICITACAO_EXAME_CANCELADA"`, `recurso = "solicitacao_exame:<codigo>:<TIPO>"`), gravando estado anterior, estado novo, motivo e `ip_origem`.
- **Interface de cancelamento por exame na Recepção (`PassoConferencia.vue`):**
  - Na etapa de conferência da solicitação, usuários com permissão `CASOS_CANCELAR` visualizam a ação "Cancelar exame" em cada grupo de exame pendente (`HP`, `IHQ`, `CO`, etc.).
  - Ao acionar o cancelamento de um grupo específico, um modal de confirmação exige o preenchimento do motivo obrigatório; após confirmar, apenas aquele grupo é removido da conferência atual (ou marcado como cancelado), permitindo seguir imediatamente com o recebimento dos exames restantes da mesma solicitação.
  - Caso todos os exames da solicitação sejam cancelados, o fluxo retorna ao passo inicial com feedback de conclusão.

## Capabilities

### New Capabilities
- `specific-exam-cancellation`: cancelamento granular de um grupo de exame específico (`<codigoSolicitacao>:<TIPO>`) antes do recebimento, com motivo obrigatório, controle de acesso via `CASOS_CANCELAR`, preservação dos exames irmãos da mesma solicitação e auditoria imutável.

### Modified Capabilities
- `sample-reception`: consolidação dos estados terminais por grupo de exame (`RECEBIDA`, `DEVOLVIDA`, `CANCELADA`), tratamento explícito de solicitações totalmente canceladas em `ler_solicitacao` e ação de cancelamento individual por exame no painel de conferência.

## Impact

- **Backend:**
  - `src/controllers/reception_controller.py`: novo método `cancelar_exame_solicitacao`, validação de estado terminal e atualização de `ler_solicitacao` para reconhecer `"CANCELADA"`.
  - `src/routers/reception.py` e `src/schemas/reception.py`: novo schema `CancelarExameSolicitacaoInput` e rota `POST /api/ap/solicitacoes/cancelamento` protegida por `Permissao.CASOS_CANCELAR`.
  - `tests/test_reception_api.py`: novos testes cobrindo cancelamento parcial (ex.: cancelar `IHQ` e receber `HP` da mesma solicitação), cancelamento total retornando `"CANCELADA"`, bloqueio de duplo cancelamento/exame já recebido (HTTP 409), validação de permissão (HTTP 403) e registro em `AuditLog`.
- **Frontend:**
  - `frontend/src/types/ap.ts`: inclusão de `"CANCELADA"` em `SituacaoRecepcao` e `LeituraSolicitacao`, além dos tipos de entrada e metadados de cancelamento por exame.
  - `frontend/src/services/ap/` e `frontend/src/stores/recepcao.ts`: integração com o endpoint de cancelamento por exame e atualização reativa dos grupos em conferência e da contagem de pendentes.
  - `frontend/src/components/ap/recepcao/PassoConferencia.vue` e `PassoLeitura.vue`: botão/modal de cancelamento individual por grupo de exame (condicionado à permissão `CASOS_CANCELAR`) e exibição do estado `"CANCELADA"` na leitura.
- **Dados / Banco:** Nenhuma alteração estrutural de tabela necessária — `ApSolicitacao` já armazena `situacao_recepcao` como string e os metadados de cancelamento no campo JSON `payload`.