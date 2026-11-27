# Spec Delta

## ADDED Requirements

### Requirement: Solicitação regularizada retorna à recepção
Uma solicitação reaberta após rejeição SHALL aparecer como pendente e exibir o contexto da rejeição anterior durante a nova conferência.

#### Scenario: Solicitação reaparece na fila
- **WHEN** grupos devolvidos na recepção são regularizados e reabertos
- **THEN** os grupos elegíveis aparecem em `GET /api/ap/solicitacoes/pendentes` e a leitura da solicitação os classifica como `PENDENTE`

#### Scenario: Metadados da devolução na leitura individual
- **WHEN** o usuário consulta uma solicitação reaberta por código de 7 dígitos, código com hífen ou etiqueta de 10 dígitos
- **THEN** a resposta inclui os metadados da devolução regularizada vinculada ao grupo, permitindo exibir o aviso de ocorrência anterior na conferência

#### Scenario: Metadados da devolução na fila pendente
- **WHEN** o usuário abre uma solicitação reaberta pela listagem de pendentes
- **THEN** os dados do grupo incluem os mesmos metadados da devolução regularizada retornados pela leitura individual

#### Scenario: Conferência informa rejeição anterior
- **WHEN** a equipe abre para conferência um grupo cuja rejeição anterior foi regularizada
- **THEN** a interface exibe um aviso informativo sobre a devolução anterior sem substituir ou alterar os dados originais da ocorrência

#### Scenario: Novo recebimento associa ocorrência anterior
- **WHEN** o grupo reaberto é recebido por confirmação de entrada ou vinculação IHQ
- **THEN** os registros anteriores de não conformidade e devolução são associados ao caso criado para esse grupo, sem modificar os horários da rejeição ou da regularização
