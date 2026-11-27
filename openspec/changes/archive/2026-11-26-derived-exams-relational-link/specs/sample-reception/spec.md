# Spec Delta

## ADDED Requirements

### Requirement: Vínculo de Revisão ao caso de origem na recepção
Quando uma Revisão que gera caso próprio for recebida, a recepção SHALL permitir associá-la ao caso principal de origem, mantendo o fluxo de recebimento e o identificador próprios da Revisão.

#### Scenario: Revisão e caso principal na mesma solicitação
- **WHEN** uma solicitação recebida contém uma Revisão e um caso principal elegível
- **THEN** o caso principal é pré-selecionado como origem da Revisão
- **AND** o usuário pode confirmar ou escolher outro caso elegível

#### Scenario: Revisão solicitada posteriormente
- **WHEN** uma Revisão chega sem caso principal na mesma solicitação
- **THEN** o usuário pode pesquisar e selecionar manualmente um caso de origem elegível por número interno, prontuário ou nome

#### Scenario: Prontuário divergente na Revisão
- **WHEN** o caso de origem selecionado para a Revisão possui prontuário diferente do prontuário da solicitação
- **THEN** o sistema exibe alerta de divergência e só permite confirmar após confirmação explícita do usuário

#### Scenario: Revisão vinculada recebida
- **WHEN** a recepção confirma uma Revisão vinculada
- **THEN** o sistema cria o registro próprio da Revisão, persiste o vínculo com a origem e registra o evento de recebimento
- **AND** o caso de origem mantém seu status e sua identificação


### Requirement: Associação da IHQ conforme os grupos da solicitação
Quando uma solicitação AGHU de IHQ possuir grupo HP próprio, a recepção SHALL vincular a IHQ exclusivamente ao HP da mesma solicitação. A seleção manual SHALL ficar disponível somente quando não houver grupo HP próprio.

#### Scenario: HP e IHQ pendentes juntos
- **WHEN** HP e IHQ da mesma solicitação estão pendentes e ambos são marcados para receber
- **THEN** a IHQ é associada automaticamente ao HP criado na conferência, sem seletor de origem

#### Scenario: HP desmarcado e IHQ marcado
- **WHEN** HP e IHQ estão pendentes, mas somente IHQ está marcada
- **THEN** a confirmação da IHQ é bloqueada com orientação para receber o HP junto ou antes

#### Scenario: HP recebido anteriormente
- **WHEN** o HP da mesma solicitação já foi recebido e a IHQ continua pendente
- **THEN** a tela mostra apenas o número do HP associado, sem radio buttons, busca ou opção para trocar

#### Scenario: IHQ avulsa
- **WHEN** uma solicitação IHQ não possui grupo HP próprio
- **THEN** a recepção permite buscar e selecionar manualmente um histopatológico existente
- **AND** o backend aceita somente caso elegível e preserva a confirmação de divergência de prontuário
