# Spec Delta

## ADDED Requirements

### Requirement: Navegação entre caso de origem e exames derivados
O detalhe SHALL exibir a origem do caso derivado e, no caso de origem, uma lista consolidada de IHQs e casos de Revisão vinculados, com acesso direto aos registros que possuam detalhe próprio.

#### Scenario: Detalhe de caso derivado
- **WHEN** o usuário abre um caso de Revisão com origem vinculada
- **THEN** o detalhe exibe um resumo navegável do caso de origem com número interno, tipo, status e data de entrada

#### Scenario: Detalhe de caso de origem
- **WHEN** o usuário abre um caso com IHQs ou Revisões vinculadas
- **THEN** o detalhe exibe a seção "Exames Derivados" com código interno, tipo, situação e data
- **AND** cada caso derivado com detalhe próprio oferece navegação direta para seu registro

#### Scenario: Caso sem derivados
- **WHEN** o usuário abre um caso sem IHQs nem casos derivados vinculados
- **THEN** o detalhe informa que ainda não há exames derivados registrados
