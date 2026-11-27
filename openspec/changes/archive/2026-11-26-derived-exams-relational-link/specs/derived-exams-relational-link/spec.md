# Spec Delta

## Purpose

Define a relação rastreável entre um caso de origem e seus exames derivados, permitindo localizar a origem e acompanhar IHQs e Revisões relacionadas sem misturar seus ciclos operacionais.

## ADDED Requirements

### Requirement: Relação entre caso derivado e caso de origem
Um caso derivado SHALL manter uma referência consultável ao caso de origem, e o vínculo SHALL identificar se a derivação corresponde a Revisão ou a outro tipo suportado.

#### Scenario: Caso derivado com origem
- **WHEN** um caso de Revisão é criado com origem informada
- **THEN** a consulta do caso derivado identifica o número interno e o tipo do caso de origem
- **AND** a consulta do caso de origem inclui o caso de Revisão entre seus derivados

#### Scenario: IHQ vinculada ao caso de origem
- **WHEN** uma IHQ é recebida para um caso de origem
- **THEN** a IHQ continua registrada como complemento do caso e aparece entre seus exames derivados com código, tipo, situação e data
- **AND** a IHQ não é apresentada como um caso principal independente

### Requirement: Integridade do vínculo de origem
O sistema SHALL validar a existência e a elegibilidade do caso de origem antes de persistir uma derivação, impedindo autorreferência, ciclos e vínculo a caso cancelado ou devolvido.

#### Scenario: Origem inexistente ou inelegível
- **WHEN** o usuário tenta vincular uma derivação a caso inexistente, cancelado ou devolvido
- **THEN** o sistema recusa a operação sem persistir vínculo parcial

#### Scenario: Autovínculo ou ciclo
- **WHEN** o vínculo faria o caso apontar para si mesmo ou criaria ciclo entre casos
- **THEN** o sistema recusa a operação e mantém os vínculos existentes

### Requirement: Ciclo de vida independente da derivação
Cada exame derivado SHALL manter sua própria identificação e situação operacional, e sua conclusão, cancelamento ou devolução SHALL NOT alterar o estado do caso de origem.

#### Scenario: Derivado cancelado
- **WHEN** um exame derivado é cancelado
- **THEN** sua situação é atualizada e o caso de origem conserva seu estado e histórico

#### Scenario: Origem consultada após alteração do derivado
- **WHEN** um usuário consulta o caso de origem após cancelar ou devolver um derivado
- **THEN** a lista de derivados apresenta o estado atualizado sem ocultar a relação

### Requirement: Histórico e auditoria da relação
O sistema SHALL registrar a criação do vínculo no histórico dos casos envolvidos e na auditoria, preservando autoria, data e hora e a relação estabelecida.

#### Scenario: Vínculo registrado
- **WHEN** uma derivação é vinculada com sucesso
- **THEN** o histórico do caso de origem e, quando aplicável, o do derivado registram o evento relacionado
- **AND** a auditoria registra a mutação na mesma operação transacional

### Requirement: Consulta bidirecional de derivados
A consulta de um caso SHALL retornar o resumo do caso de origem quando houver e a lista unificada de exames derivados vinculados quando o caso consultado for a origem.

#### Scenario: Consulta do caso de origem
- **WHEN** um usuário autorizado consulta um caso com IHQs ou Revisões derivadas
- **THEN** a resposta inclui código interno, tipo, situação e data de cada derivado

#### Scenario: Consulta do caso derivado
- **WHEN** um usuário autorizado consulta um caso derivado
- **THEN** a resposta inclui o resumo do caso de origem com número interno, tipo, status e data de entrada


### Requirement: Origem obrigatória da IHQ com HP na mesma solicitação
Quando a solicitação AGHU de uma IHQ possuir grupo HP próprio, o sistema SHALL vinculá-la exclusivamente ao caso HP da mesma solicitação, seja ele recebido anteriormente ou na conferência atual. Se não houver grupo HP próprio, SHALL permitir a associação manual a um caso elegível.

#### Scenario: Rejeitar HP de outra solicitação
- **WHEN** uma IHQ cuja solicitação contém grupo HP é enviada com outro caso como origem
- **THEN** `ReceptionController` recusa a operação sem registrar a IHQ

#### Scenario: Aguardar o HP próprio
- **WHEN** o grupo HP da solicitação ainda aguarda recebimento
- **THEN** o sistema recusa receber a IHQ até o HP ser recebido junto ou antes
