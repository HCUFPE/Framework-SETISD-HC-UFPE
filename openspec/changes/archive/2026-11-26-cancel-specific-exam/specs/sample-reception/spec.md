# Spec Delta: sample-reception

## ADDED Requirements

### Requirement: Situação terminal dos grupos de exame
Cada grupo de exame da solicitação SHALL possuir uma situação de recepção independente: `AGUARDANDO_RECEBIMENTO`, `RECEBIDA`, `DEVOLVIDA` ou `CANCELADA`. Cancelar um grupo SHALL mantê-lo persistido e registrar no payload o motivo, autor e data/hora. Listagem e contagem de pendentes SHALL considerar somente grupos em `AGUARDANDO_RECEBIMENTO`, preservando os grupos irmãos.

#### Scenario: Solicitação parcialmente cancelada
- **WHEN** uma solicitação possui HP e IHQ pendentes e o IHQ é cancelado
- **THEN** a fila continua exibindo a solicitação apenas com HP
- **AND** HP permanece disponível para recebimento

#### Scenario: Solicitação totalmente cancelada
- **WHEN** todos os grupos de uma solicitação foram cancelados
- **THEN** `ler_solicitacao` retorna classificação `CANCELADA` com motivo, autor e data/hora
- **AND** não classifica a solicitação como `NAO_ENCONTRADA`

#### Scenario: Leitura com grupos em estados distintos
- **WHEN** uma solicitação contém grupos cancelados e ao menos um grupo aguardando recebimento
- **THEN** a leitura retorna a conferência dos grupos pendentes
- **AND** grupos cancelados não aparecem como pendentes

#### Scenario: Bipagem de amostra pertencente a grupo cancelado
- **WHEN** o código de barras de 10 dígitos identifica uma amostra de grupo cancelado enquanto outro grupo da solicitação aguarda recebimento
- **THEN** a leitura retorna o grupo pendente restante
- **AND** a conferência informa que o grupo da amostra bipada foi cancelado

### Requirement: Ação de cancelamento na conferência
Na etapa de conferência, a interface SHALL oferecer “Cancelar exame” para cada grupo pendente somente a usuários com `CASOS_CANCELAR`. A confirmação SHALL exigir motivo não vazio. Após sucesso, a interface SHALL atualizar a conferência e a contagem de pendentes sem afetar os grupos restantes. Se todos os grupos forem cancelados, SHALL retornar ao passo inicial e informar a conclusão.

#### Scenario: Cancelar um grupo e receber outro
- **WHEN** o usuário cancela IHQ e confirma o recebimento do HP da mesma solicitação
- **THEN** somente HP é recebido e IHQ permanece cancelado

#### Scenario: Todos os exames cancelados na conferência
- **WHEN** o usuário cancela o último grupo pendente da solicitação
- **THEN** a conferência retorna ao passo inicial com feedback de cancelamento concluído

#### Scenario: Sem permissão na interface
- **WHEN** o usuário não possui `CASOS_CANCELAR`
- **THEN** a ação “Cancelar exame” não é apresentada
- **AND** a API continua protegida independentemente da interface

### Requirement: Leitura de solicitação cancelada
Quando todos os grupos da solicitação estiverem cancelados, a leitura SHALL apresentar a classificação `CANCELADA` e os metadados disponíveis do cancelamento, sem oferecer recebimento desses grupos.

#### Scenario: Leitura após cancelamento total
- **WHEN** o usuário lê uma solicitação cujos grupos foram todos cancelados
- **THEN** recebe estado `CANCELADA`, motivo, autor e data/hora, sem falso aviso de solicitação inexistente
