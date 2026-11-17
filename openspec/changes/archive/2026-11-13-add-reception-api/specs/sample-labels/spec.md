# sample-labels Specification

## REMOVED Requirements

### Requirement: Registro da impressão
Cada impressão SHALL registrar um evento no histórico do caso ("Etiquetas impressas" ou "Ficha de trabalho impressa"), com o usuário e a data e hora.

#### Scenario: Reimpressão

- **WHEN** o usuário imprime a ficha de trabalho pela segunda vez
- **THEN** o histórico passa a ter dois eventos "Ficha de trabalho impressa"
