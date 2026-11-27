# case-detail Specification

## Purpose

Reúne em uma única tela tudo o que se sabe sobre um caso de anatomia patológica: dados do AGHU, recepção, etapas, materiais, não conformidades e histórico imutável. Também concentra as ações que a recepção pode executar sobre o caso.

## Requirements

### Requirement: Cabeçalho do caso
O detalhe SHALL exibir:
- o número interno, com ação de copiar;
- o selo de status;
- o selo URGENTE, quando aplicável, sem motivo;
- tipo de exame, paciente com prontuário, material e data de entrada.

#### Scenario: Caso urgente
- **WHEN** o usuário abre um caso urgente
- **THEN** o cabeçalho mostra o selo URGENTE, sem dica de motivo

### Requirement: Caso inexistente
Ao acessar o endereço de um número interno que não existe, o sistema SHALL exibir "Caso não encontrado" com a ação de voltar à Consulta de casos.

#### Scenario: Endereço inválido
- **WHEN** o usuário acessa `/casos/HP-9999/26` e esse caso não existe
- **THEN** a tela informa que o caso não foi encontrado e oferece voltar à consulta

### Requirement: Fluxo de etapas por tipo
O sistema SHALL adotar as seguintes etapas por tipo de exame:
- HP: Recepção, Macroscopia, Processamento técnico, Microscopia, Aprovação e Arquivo;
- CG: Recepção, Processamento técnico, Microscopia, Aprovação e Arquivo;
- CCV: Recepção, Processamento técnico, Triagem citotécnica, Microscopia, Aprovação e Arquivo;
- CO: Recepção, Congelação, Microscopia, Aprovação e Arquivo.

#### Scenario: Fluxo de um caso CCV
- **WHEN** o usuário abre um caso CCV
- **THEN** o indicador lista Recepção, Processamento técnico, Triagem citotécnica, Microscopia, Aprovação e Arquivo

#### Scenario: Caso com IHQ vinculada
- **WHEN** o caso tem uma IHQ vinculada
- **THEN** a etapa IHQ aparece no indicador antes de Microscopia

### Requirement: Indicador do fluxo do caso
O detalhe SHALL exibir as etapas do fluxo do tipo do caso, marcando as concluídas, a atual e as futuras. O indicador SHALL caber na largura disponível, quebrando as etapas em linhas quando necessário, e não SHALL exibir barra de rolagem.

#### Scenario: Caso CG em processamento
- **WHEN** o usuário abre um caso CG com status "Em processamento técnico"
- **THEN** Recepção aparece como concluída, Processamento técnico como atual e as demais como futuras

#### Scenario: Caso interrompido
- **WHEN** o caso está devolvido ou cancelado
- **THEN** o indicador mostra a etapa em que o caso parou, marcada como interrompida

#### Scenario: Tela estreita
- **WHEN** o usuário abre o detalhe de um caso em uma janela estreita
- **THEN** as etapas do fluxo quebram em mais de uma linha e nenhuma barra de rolagem aparece no indicador

### Requirement: Faixa de bloqueio
Casos com status "Devolvido", "Cancelado", "Laudo concluído", "Em arquivamento" ou "Arquivado" SHALL exibir uma faixa explicando que o caso é somente leitura, com o motivo correspondente, e não SHALL oferecer as ações de não conformidade nem de cancelamento.

#### Scenario: Caso cancelado
- **WHEN** o usuário abre um caso cancelado
- **THEN** a faixa informa "Caso cancelado — fora das filas ativas. Consulta somente leitura." e as ações de alteração não aparecem

### Requirement: Abas do caso
O detalhe SHALL organizar as informações nas abas: Resumo, Solicitação AGHU, Recepção, Macroscopia, Processamento, IHQ, Microscopia, Laudo, Arquivo, Materiais, Não conformidades e Histórico. Uma aba sem informação SHALL exibir uma mensagem de que ainda não há registro para o caso.

#### Scenario: Aba sem registro
- **WHEN** o usuário abre a aba "Macroscopia" de um caso ainda "Recebido"
- **THEN** a aba informa que a macroscopia ainda não foi registrada

### Requirement: Aba Resumo
A aba Resumo SHALL exibir tipo, etapa atual, tempo na etapa atual, data de entrada, procedimento, quantidade de amostras, informações clínicas e as cinco movimentações mais recentes, com acesso ao histórico completo.

#### Scenario: Ver histórico completo
- **WHEN** o usuário clica em "Ver histórico completo" na aba Resumo
- **THEN** a aba Histórico é exibida

### Requirement: Abas Solicitação AGHU e Recepção
A aba Solicitação AGHU SHALL exibir, somente leitura e identificados como vindos do AGHU, os mesmos dados mostrados na conferência, inclusive a lista das amostras do caso com número, descrição do material e status no AGHU. A aba Recepção SHALL exibir:
- entrada e responsável;
- tipo de exame, quantidade de amostras, urgência (Sim ou Não), procedimento e observações;
- a conferência registrada, com as amostras conferidas e o resultado.

#### Scenario: Conferência na aba Recepção
- **WHEN** o usuário abre a aba Recepção de um caso recebido no sistema
- **THEN** a conferência aparece com as amostras conferidas, o resultado "Aceita", o responsável e a data e hora, sem itens de checkbox

#### Scenario: Amostras na aba Solicitação AGHU
- **WHEN** o usuário abre a aba Solicitação AGHU de um caso com as amostras 2 e 3
- **THEN** as duas amostras aparecem separadas, cada uma com número, descrição e status no AGHU

### Requirement: Abas das etapas posteriores
As abas Macroscopia, Processamento, IHQ, Microscopia, Laudo e Arquivo SHALL exibir, somente para leitura, os registros existentes do caso, com responsável e data e hora de cada um. A aba IHQ SHALL listar as IHQ vinculadas, com código, situação e solicitação do AGHU.

#### Scenario: IHQ vinculada pela recepção
- **WHEN** uma IHQ foi vinculada ao caso na recepção
- **THEN** a aba IHQ lista o código da IHQ, a situação "Solicitada", o nº da solicitação AGHU e a data de recebimento

### Requirement: Aba Materiais
A aba Materiais SHALL exibir a árvore de materiais do caso (amostra, bloco ou cell-block e lâmina), com código, rótulo, data e hora e responsável de cada item, e o total por tipo de item.

#### Scenario: Caso com blocos e lâminas
- **WHEN** o caso tem uma amostra com dois blocos e três lâminas
- **THEN** a árvore mostra os itens aninhados e o total "1 amostra · 2 blocos · 3 lâminas"

### Requirement: Abas Não conformidades e Histórico
A aba Não conformidades SHALL listar as não conformidades e devoluções do caso, com todos os dados registrados, e o cancelamento quando houver. A aba Histórico SHALL exibir todos os eventos do caso, do mais recente para o mais antigo, com ação, descrição, setor, usuário e data e hora, sem oferecer edição nem exclusão.

#### Scenario: Histórico imutável
- **WHEN** o usuário visualiza a aba Histórico
- **THEN** os eventos são exibidos sem nenhuma ação de editar ou excluir

### Requirement: Ações do caso ativo
Para casos ativos, o detalhe SHALL oferecer, nesta ordem, "Não conformidade", "Cancelar caso" e "Imprimir" (etiquetas das amostras ou ficha de trabalho). Para casos bloqueados, SHALL oferecer apenas "Imprimir". As ações SHALL ficar na mesma linha do número interno e dos selos, alinhadas à direita, e quebrar para a linha seguinte só quando não houver espaço. "Não conformidade" SHALL abrir o modal "Não conformidade e devolução". A impressão de etiquetas SHALL permitir escolher quais amostras imprimir quando o caso tiver mais de uma.

#### Scenario: Imprimir a partir do detalhe
- **WHEN** o usuário escolhe "Imprimir" e depois "Ficha de trabalho"
- **THEN** a pré-visualização da ficha de trabalho do caso é aberta

#### Scenario: Imprimir etiquetas escolhidas
- **WHEN** o usuário escolhe "Imprimir" e depois "Etiquetas" em um caso com 4 amostras
- **THEN** a pré-visualização permite marcar quais das 4 amostras imprimir

#### Scenario: Não conformidade no detalhe
- **WHEN** o usuário clica em "Não conformidade" em um caso ativo
- **THEN** o modal "Não conformidade e devolução" é aberto com o caso e a etapa atual identificados

#### Scenario: Posição das ações
- **WHEN** o usuário abre um caso ativo em tela larga
- **THEN** "Não conformidade", "Cancelar caso" e "Imprimir" aparecem nessa ordem, na linha do número interno e dos selos

### Requirement: Cancelamento do caso
O cancelamento SHALL exigir o motivo e uma confirmação explícita. Ao cancelar, o sistema SHALL:
- mudar o status do caso para "Cancelado";
- registrar o motivo, o usuário e a data e hora;
- gravar o evento no histórico e na auditoria;
- manter o caso, seus materiais e seu histórico disponíveis para consulta.

#### Scenario: Cancelamento sem motivo
- **WHEN** o usuário tenta confirmar o cancelamento com o motivo vazio
- **THEN** o cancelamento é recusado e o motivo é indicado como obrigatório

#### Scenario: Cancelamento confirmado
- **WHEN** o usuário informa o motivo e confirma o cancelamento
- **THEN** o caso passa a "Cancelado", exibe a faixa de bloqueio e continua aparecendo na Consulta de casos

### Requirement: Autorização de consulta e cancelamento existentes

A consulta de detalhe e a operação existente de cancelamento SHALL exigir permissões explícitas distintas conforme o catálogo vigente. O frontend SHALL refletir as permissões, e o backend SHALL aplicá-las em chamadas diretas.

#### Scenario: Cancelamento sem permissão

- **WHEN** usuário sem permissão de cancelamento tenta cancelar um caso diretamente
- **THEN** o backend responde 403 e mantém caso, histórico e materiais sem alteração

### Requirement: Histórico de reabertura no detalhe do caso
O detalhe do caso SHALL apresentar o evento de reabertura e as ocorrências anteriores de não conformidade e devolução sem ocultar nem substituir os eventos já registrados.

#### Scenario: Caso devolvido é reaberto
- **WHEN** uma devolução regularizada reabre um caso existente
- **THEN** a linha do tempo mantém os eventos anteriores e inclui `FLUXO_REABERTO` citando a devolução regularizada

#### Scenario: Caso criado após rejeição na recepção
- **WHEN** uma solicitação previamente rejeitada é recebida e gera um novo caso
- **THEN** o detalhe do caso exibe o contexto da devolução prévia e o evento `FLUXO_REABERTO` associado à solicitação

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
