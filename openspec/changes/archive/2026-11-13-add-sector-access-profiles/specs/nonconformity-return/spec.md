# nonconformity-return Specification

## ADDED Requirements

### Requirement: Autorização de registro e atualização existentes

O registro de não conformidade/devolução e a atualização de situação SHALL exigir permissões explícitas do catálogo vigente. O backend SHALL aplicar as verificações tanto na criação quanto na atualização.

#### Scenario: Atualização direta sem permissão

- **WHEN** usuário sem permissão chama diretamente a operação de atualização da situação
- **THEN** o backend responde 403 e não altera a situação nem registra mutação

#### Scenario: Atualização por Recepção ou Administração

- **WHEN** Recepcionista SAP ou Coordenação/Administrador atualiza diretamente a situação de uma devolução
- **THEN** o backend autoriza a operação, persiste a situação e registra autoria autenticada e auditoria
- **AND** outros perfis continuam sujeitos à negação por padrão
