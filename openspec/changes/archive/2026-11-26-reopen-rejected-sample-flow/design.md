# Design

## Context

Ver [proposal.md](./proposal.md) para a motivação e o comportamento esperado, e os deltas em `specs/` para os contratos. Hoje a atualização da devolução altera sua situação e resolve a não conformidade; as solicitações rejeitadas e casos devolvidos precisam ser sincronizados com essa transição. O fluxo usa `AsyncSession` compartilhada entre provider e controller e não exige migração estrutural.

## Goals / Non-Goals

**Goals:**
- Aplicar as guardas de estado e sincronizar as entidades relacionadas antes de confirmar a operação.
- Preservar ocorrências, timestamps, autoria e natureza original da rejeição para histórico e SLA.
- Reutilizar a auditoria e os históricos de caso existentes, incluindo autor autenticado e IP de origem.

**Non-Goals:**
- Alterar o schema físico, criar migração ou permitir reabertura de registros cancelados/encerrados.
- Criar uma nova solicitação AGHU ou substituir os dados da ocorrência original.

## Decisions

1. **Validar e mutar na mesma sessão transacional.** A operação de situação carrega a devolução, as solicitações indicadas em `solicitacaoIds` e, quando aplicável, o caso; valida todos os estados antes de escrever. A atualização da devolução, das solicitações/caso, da não conformidade, do evento de histórico e do `AuditLog` é confirmada em conjunto. Erro de validação retorna HTTP 409 antes de mutações; erro durante persistência ou auditoria provoca rollback completo. Evitar helpers de auditoria que confirmem a transação antes das demais gravações.

2. **Reabrir apenas os vínculos ainda pertencentes à devolução.** No caminho sem caso, atualizar somente solicitações listadas em `solicitacaoIds` que estejam `DEVOLVIDA` e cujo `devolucaoId` corresponda à devolução atual. O contrato de reabertura exige que nenhum grupo vinculado esteja cancelado ou recebido; divergência de vínculo/estado interrompe a operação, sem limpar vínculo de outra ocorrência.

3. **Persistir o estado anterior do caso no payload da ocorrência.** Ao registrar uma não conformidade em caso, salvar `statusCasoAnterior` no payload da não conformidade/devolução antes de mover o caso para `DEVOLVIDO`. Reabrir com esse valor validado como estado ativo; para registros legados sem o campo, usar `RECEBIDO`. Não inferir o estado anterior pelo estado atual do caso, que estará `DEVOLVIDO`.

4. **Associar cada caso sem reescrever a ocorrência.** Depois da confirmação de entrada ou vinculação IHQ, localizar a ocorrência pré-recepção pelo `solicitacaoId` e associá-la ao novo `casoNumero`. Como uma devolução pode cobrir vários grupos e o vínculo relacional atual é singular, acrescentar `casoNumeros` ao payload da ocorrência para consulta em todos os casos, sem alterar os dados originais e preservando o primeiro vínculo físico. Preservar os horários originais e a natureza "Rejeição na recepção" em `rejeicaoNaRecepcao`. Registrar `FLUXO_REABERTO` em cada caso associado, referenciando a devolução.

5. **Expor o contexto pela resposta existente.** Reutilizar os dados e componentes de recepção, devoluções e detalhe do caso; a tela confirma a reabertura e oferece o atalho correspondente ao tipo de fluxo. O aviso de rejeição anterior deve usar a ocorrência associada e não alterar o conteúdo original. Não criar endpoint ou dependência frontend adicional se as respostas atuais puderem ser enriquecidas.

## Risks / Trade-offs

- **Ocorrências antigas podem não possuir `statusCasoAnterior`.** Restaurar em `RECEBIDO` mantém compatibilidade, mas pode não recuperar uma etapa técnica anterior; registrar esse fallback no evento de reabertura.
- **Solicitação pode ter múltiplos grupos e devoluções parciais.** Filtrar pelo conjunto de IDs e `devolucaoId` evita reabrir grupos alheios; validar discrepâncias evita uma reabertura parcial silenciosa.
- **Vinculação histórica pode ocorrer em mais de uma rota de entrada.** Implementar a mesma operação idempotente em `confirmar_entrada` e `vincular_ihq`, verificando associação existente para não duplicar eventos.
- **Auditoria transacional pode conflitar com helpers que fazem commit.** Separar a montagem do registro de auditoria da confirmação da sessão e testar rollback quando uma etapa falhar.

## Migration Plan

Não há migração estrutural. Novas ocorrências de caso passam a guardar o estado anterior no payload; registros existentes usam o fallback definido. A publicação pode ser revertida pelo deploy anterior, sem conversão de dados.
