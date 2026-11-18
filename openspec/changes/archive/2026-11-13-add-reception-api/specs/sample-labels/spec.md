# sample-labels Specification

## ADDED Requirements

### Requirement: Impressão local
A pré-visualização, impressão e reimpressão SHALL ocorrer apenas no navegador usando `window.print()`, sem chamada de API, registro no histórico do caso ou `AuditLog`.

#### Scenario: Reimpressão local
- **WHEN** o usuário imprime a ficha de trabalho pela segunda vez
- **THEN** o navegador imprime a ficha novamente sem criar registro no backend

#### Scenario: Impressão parcial local de etiquetas
- **WHEN** o usuário imprime só as etiquetas das amostras 2 e 4
- **THEN** o navegador imprime apenas essas etiquetas sem criar registro no backend
