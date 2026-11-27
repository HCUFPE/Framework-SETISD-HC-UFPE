# Spec Delta

## Purpose

Define como uma amostra rejeitada retorna ao fluxo após regularização, mantendo estados coerentes entre devolução, solicitação e caso, sem perder o histórico necessário à auditoria e ao SLA.

## ADDED Requirements

### Requirement: Reabertura controlada de solicitação rejeitada na recepção
O sistema MUST reabrir os grupos devolvidos da solicitação ao registrar `NOVA_AMOSTRA_RECEBIDA`, desde que todos os vínculos e estados permitam a transição.

#### Scenario: Solicitação pré-recepção retorna à fila
- **WHEN** a devolução ainda não possui caso e todos os grupos vinculados estão `DEVOLVIDA` com o mesmo `devolucaoId`
- **THEN** os grupos elegíveis passam para `AGUARDANDO_RECEBIMENTO`, têm `devolucaoId` removido e voltam à fila pendente

#### Scenario: Solicitação cancelada ou recebida bloqueia a reabertura
- **WHEN** qualquer solicitação vinculada está `CANCELADA` ou `RECEBIDA`
- **THEN** o sistema responde HTTP 409 e não altera nenhum registro da operação

### Requirement: Reabertura de caso devolvido
O sistema MUST reativar um caso devolvido regularizado sem apagar nem sobrescrever os registros anteriores da ocorrência.

#### Scenario: Caso devolvido retoma o estado ativo anterior
- **WHEN** a devolução pertence a um caso em `DEVOLVIDO` e a nova amostra é marcada como recebida
- **THEN** o caso retorna ao estado ativo salvo na ocorrência, ou a `RECEBIDO` quando o registro legado não possuir esse estado, e recebe um evento imutável `FLUXO_REABERTO`

#### Scenario: Caso fora do estado devolvido não pode ser reaberto
- **WHEN** a devolução aponta para um caso cujo estado não é `DEVOLVIDO`
- **THEN** o sistema responde HTTP 409 sem alterar a devolução, o caso ou as solicitações vinculadas

### Requirement: Associação histórica após novo recebimento
O sistema MUST associar ao novo caso a não conformidade e a devolução originadas antes da recepção, preservando os dados e horários originais da ocorrência.

#### Scenario: Nova entrada mantém o histórico da rejeição
- **WHEN** uma solicitação reaberta é recebida por confirmação de entrada ou vinculação IHQ
- **THEN** a não conformidade e a devolução daquela solicitação ficam associadas ao novo caso e o histórico registra `FLUXO_REABERTO` citando a devolução regularizada sem alterar datas originais

### Requirement: Bloqueio de transições terminais e regressivas
O sistema MUST recusar transições de reabertura incompatíveis com estados terminais ou com o avanço posterior da solicitação.

#### Scenario: Devolução encerrada ou caso cancelado
- **WHEN** a devolução está `ENCERRADA` ou o caso vinculado está `CANCELADO`
- **THEN** a atualização para `NOVA_AMOSTRA_RECEBIDA` responde HTTP 409 e mantém todos os estados inalterados

#### Scenario: Solicitação avança após regularização
- **WHEN** uma solicitação vinculada já foi recebida ou cancelada após a regularização
- **THEN** uma tentativa de voltar a devolução para `AGUARDANDO_NOVA_AMOSTRA` responde HTTP 409 e preserva o estado atual

### Requirement: Auditoria atômica da reabertura
O sistema MUST registrar em uma única transação a mudança de estados de devolução, solicitações e caso, com autoria autenticada e IP de origem.

#### Scenario: Auditoria e estados são persistidos juntos
- **WHEN** uma reabertura válida é concluída
- **THEN** os estados anteriores e novos de todos os registros afetados ficam auditados com usuário e IP, ou toda a operação é revertida se a auditoria falhar
