# Spec Delta

## ADDED Requirements

### Requirement: Histórico de reabertura no detalhe do caso
O detalhe do caso SHALL apresentar o evento de reabertura e as ocorrências anteriores de não conformidade e devolução sem ocultar nem substituir os eventos já registrados.

#### Scenario: Caso devolvido é reaberto
- **WHEN** uma devolução regularizada reabre um caso existente
- **THEN** a linha do tempo mantém os eventos anteriores e inclui `FLUXO_REABERTO` citando a devolução regularizada

#### Scenario: Caso criado após rejeição na recepção
- **WHEN** uma solicitação previamente rejeitada é recebida e gera um novo caso
- **THEN** o detalhe do caso exibe o contexto da devolução prévia e o evento `FLUXO_REABERTO` associado à solicitação
