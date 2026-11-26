# Spec Delta: specific-exam-cancellation

## ADDED Requirements

### Requirement: Cancelamento de grupo de exame pendente
O sistema SHALL permitir cancelar logicamente um único grupo de exame da solicitação AGHU, identificado por `<codigoSolicitacao>:<TIPO>`, sem remover o registro e sem alterar os grupos irmãos. O cancelamento SHALL exigir motivo não vazio, permissão `CASOS_CANCELAR` e identidade autenticada; autor e IP SHALL ser obtidos de fontes confiáveis do servidor.

#### Scenario: Cancelar um grupo de solicitação mista
- **WHEN** uma solicitação possui os grupos HP e IHQ em `AGUARDANDO_RECEBIMENTO` e um usuário com `CASOS_CANCELAR` cancela o IHQ com motivo
- **THEN** o grupo IHQ passa a `CANCELADA` com motivo, autor e data/hora
- **AND** o grupo HP permanece `AGUARDANDO_RECEBIMENTO` e pode ser recebido normalmente

#### Scenario: Motivo obrigatório
- **WHEN** o corpo da requisição tem motivo ausente, vazio ou composto apenas por espaços
- **THEN** o servidor rejeita a requisição como inválida e não altera dados nem registra cancelamento

#### Scenario: Grupo inexistente
- **WHEN** o usuário autorizado solicita o cancelamento de uma chave de grupo inexistente
- **THEN** o servidor responde 404 e não altera dados

#### Scenario: Grupo em estado terminal
- **WHEN** o grupo alvo já está `RECEBIDA`, `DEVOLVIDA` ou `CANCELADA`
- **THEN** o servidor responde 409 e preserva o estado e os metadados existentes

#### Scenario: Sem permissão
- **WHEN** identidade autenticada sem `CASOS_CANCELAR` chama diretamente o endpoint
- **THEN** o servidor responde 403 e não altera dados nem grava auditoria de sucesso

### Requirement: Auditoria do cancelamento de exame
Cada cancelamento bem-sucedido SHALL registrar na mesma transação do banco um `AuditLog` imutável com categoria `NEGOCIO_CLINICO`, ação `SOLICITACAO_EXAME_CANCELADA`, recurso `solicitacao_exame:<codigo>:<TIPO>`, identidade autenticada, IP de origem, estado anterior, estado novo e motivo. Falha ao registrar auditoria SHALL impedir a confirmação da mutação.

#### Scenario: Auditoria gravada junto da mutação
- **WHEN** um grupo pendente é cancelado com sucesso
- **THEN** o estado `CANCELADA` e o evento de auditoria são persistidos atomicamente com os dados anterior e novo e o IP da requisição

#### Scenario: Falha de auditoria
- **WHEN** ocorre falha ao gravar o `AuditLog` durante o cancelamento
- **THEN** a transação é revertida e o grupo continua pendente
