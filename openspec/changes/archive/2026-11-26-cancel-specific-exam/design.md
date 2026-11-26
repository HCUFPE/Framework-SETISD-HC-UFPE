# Design: Cancelamento de exame específico

## Context

A recepção agrupa amostras da solicitação AGHU por `<codigoSolicitacao>:<tipoExame>`. Os grupos pendentes podem ser recebidos ou devolvidos, e a fila considera apenas os grupos aguardando recebimento. O cancelamento existente de caso ocorre depois da geração do caso e não representa a decisão de não processar um grupo ainda pendente. Esta mudança adiciona um estado terminal administrativo ao grupo, mantendo o registro local para leitura e auditoria.

## Goals / Non-Goals

**Goals:**
- Cancelar exatamente um grupo pendente identificado por `solicitacaoId`, com motivo obrigatório e permissão `CASOS_CANCELAR`.
- Persistir a mudança e o `AuditLog` na mesma transação, atribuindo o autor às claims JWT e o IP à requisição.
- Preservar os demais grupos AGHU, atualizar a fila e comunicar solicitações totalmente canceladas.
- Expor a ação na conferência para usuários autorizados e informar o estado cancelado na leitura.

**Non-Goals:**
- Exclusão física de `ApSolicitacao`, alteração estrutural de tabela ou migração.
- Cancelamento de grupo já recebido/devolvido ou reabertura de grupo cancelado.
- Cancelar o caso inteiro, devolver material por não conformidade ou modificar dados no AGHU.

## Decisions

### 1. Estado e metadados no registro local
- **Decisão:** Atualizar somente `situacao_recepcao` do grupo alvo para `CANCELADA` e armazenar `motivo`, `canceladoPor` e `canceladoEm` no JSON `payload` de `ApSolicitacao`. Manter o registro para consultas e trilha de auditoria.
- **Validação:** Resolver a chave `<codigoSolicitacao>:<TIPO>` de forma exata; inexistente retorna 404. Apenas `AGUARDANDO_RECEBIMENTO` é cancelável; estados terminais retornam 409.

### 2. Endpoint e governança
- **Decisão:** Criar `POST /api/ap/solicitacoes/cancelamento` com `solicitacaoId` e `motivo` não vazio. Proteger a operação por `Permissao.CASOS_CANCELAR`; o usuário não é aceito no corpo, sendo derivado da identidade autenticada.
- **Auditoria:** Registrar `NEGOCIO_CLINICO`, `SOLICITACAO_EXAME_CANCELADA` e recurso `solicitacao_exame:<codigo>:<TIPO>`, incluindo estado anterior/novo, motivo e IP. A mutação e o log pertencem à mesma transação; erro de auditoria aborta a operação.

### 3. Leitura e fila
- **Decisão:** Listagem e contagem continuam selecionando somente `AGUARDANDO_RECEBIMENTO`. A leitura preserva a precedência de pendentes, recebidos e devolvidos; quando todos os grupos estiverem cancelados, retorna classificação `CANCELADA` e metadados de cancelamento, não `NAO_ENCONTRADA`.
- **Solicitação mista:** Cancelar um grupo não altera os irmãos. Um grupo pendente restante continua recebível e mantém a solicitação na fila.

### 4. Interface
- **Decisão:** Mostrar “Cancelar exame” por grupo pendente em `PassoConferencia.vue` somente para quem possui `CASOS_CANCELAR`. O diálogo exige motivo e confirma a ação. Após sucesso, atualizar grupos e contagem; quando não houver exame pendente, retornar à leitura inicial com feedback. Exibir estado/metadados cancelados em `PassoLeitura.vue`.
- **Segurança:** A visibilidade da ação é apenas apresentação; a API sempre valida a permissão.

## Risks / Trade-offs

- **Payload legado ou com estrutura inesperada** → Atualizar somente os campos necessários, preservando as demais chaves do payload.
- **Concorrência entre recebimento e cancelamento** → Revalidar o estado dentro da transação antes de persistir; estado que deixou de ser pendente resulta em conflito sem auditoria de sucesso.
- **Estado CANCELADA convivendo com leitura mista** → Tratar cancelamento como terminal por grupo e classificar toda a solicitação como cancelada apenas quando não houver grupo pendente, recebido ou devolvido.
