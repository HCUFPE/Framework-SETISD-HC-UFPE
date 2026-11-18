# sample-reception Specification

## Purpose

Permite que a recepção do Serviço de Anatomia Patológica receba uma amostra a partir da solicitação do AGHU: conferir o material físico, completar os dados e confirmar a entrada. A confirmação gera o número interno do caso ou vincula a IHQ ao caso de origem, sem redigitar os dados que já existem no AGHU.

## Requirements

### Requirement: Passos da recepção
A tela "Recepção de amostras" SHALL conduzir o recebimento em três passos: "Ler etiqueta AGHU", "Conferir" e "Etiquetas e ficha". O indicador de passos SHALL aparecer apenas a partir do passo "Conferir", mostrando os passos concluídos, o atual e o futuro. A tela inicial (passo "Ler etiqueta AGHU") não SHALL exibir o indicador.

#### Scenario: Início da recepção
- **WHEN** o usuário abre a tela "Recepção de amostras"
- **THEN** o passo "Ler etiqueta AGHU" é exibido sem o indicador de passos, e o campo de leitura recebe o foco

#### Scenario: Conferência iniciada
- **WHEN** o usuário inicia o recebimento de uma solicitação
- **THEN** o indicador de passos é exibido com "Ler etiqueta AGHU" concluído e "Conferir" como atual

### Requirement: Leitura da solicitação AGHU
No passo 1, o usuário SHALL informar o número da solicitação AGHU por leitor ou digitação, confirmando com Enter. Uma solicitação aguardando recebimento SHALL ser carregada e levar ao passo "Conferir".

#### Scenario: Solicitação pendente
- **WHEN** o usuário informa o número de uma solicitação aguardando recebimento e pressiona Enter
- **THEN** os dados da solicitação são carregados e o passo "Conferir" é exibido

#### Scenario: Campo vazio
- **WHEN** o usuário pressiona Enter com o campo vazio
- **THEN** nada é carregado e o sistema pede que informe o número da solicitação

### Requirement: Solicitação não recebível
O sistema SHALL recusar a leitura de uma solicitação que não está aguardando recebimento, com uma mensagem que diga o motivo e permaneça no passo 1.

#### Scenario: Solicitação já recebida
- **WHEN** o usuário lê uma solicitação já recebida como o caso HP-0007/26
- **THEN** o sistema informa "A solicitação <nº> já foi recebida como HP-0007/26." e oferece abrir esse caso

#### Scenario: Solicitação devolvida
- **WHEN** o usuário lê uma solicitação que foi devolvida por não conformidade
- **THEN** o sistema informa que a solicitação foi devolvida, com a data e o tipo da não conformidade

#### Scenario: Solicitação inexistente
- **WHEN** o usuário lê um número que não corresponde a nenhuma solicitação
- **THEN** o sistema informa "Nenhuma solicitação encontrada para <nº>. Confira a etiqueta ou digite o número." e lembra que material sem etiqueta do AGHU deve ser devolvido

### Requirement: Lista de solicitações pendentes
O passo 1 SHALL apresentar as solicitações do AGHU aguardando recebimento como uma fila de tarefas "Para receber", com a quantidade de pendentes. Cada item mostra tipo e nome do exame, nº da solicitação, material, origem e há quanto tempo aguarda, e tem a ação "Iniciar recebimento", equivalente à leitura do número. A fila SHALL listar primeiro as de Congelação e depois as demais, da mais antiga para a mais nova. Itens que aguardam há mais de 2 horas SHALL ser destacados.

#### Scenario: Ler pela lista
- **WHEN** o usuário clica em "Iniciar recebimento" em um item da fila
- **THEN** o resultado é o mesmo de ler o número dessa solicitação

#### Scenario: Espera longa
- **WHEN** uma solicitação aguarda recebimento há 3 horas
- **THEN** o item exibe "há 3 h" com destaque de atraso

#### Scenario: Lista vazia
- **WHEN** não há solicitações aguardando recebimento
- **THEN** a fila exibe "Nenhuma solicitação aguardando recebimento." com indicação de que não há tarefas pendentes

### Requirement: AGHU indisponível
Quando o serviço de solicitações do AGHU estiver indisponível, a recepção SHALL exibir um aviso, desabilitar a leitura e a lista de pendentes e manter disponível o registro de material sem etiqueta.

#### Scenario: Falha ao consultar o AGHU
- **WHEN** a consulta de solicitações falha por indisponibilidade
- **THEN** o sistema exibe "AGHU indisponível no momento. A recepção de novas amostras está bloqueada." e desabilita a leitura

### Requirement: Dados da solicitação somente leitura
O passo "Conferir" SHALL exibir, sem permitir edição e identificados como vindos do AGHU, os dados da solicitação e uma linha por amostra: número, tipo e exame do AGHU, descrição do material e status. Informações ausentes SHALL aparecer como "Não informado". O tipo do grupo SHALL ser determinado pelas amostras e não poderá ser alterado.

#### Scenario: Conferência de solicitação carregada
- **WHEN** o passo "Conferir" é exibido
- **THEN** os dados do AGHU aparecem bloqueados para edição, com uma linha por amostra e destaque para o material e as informações clínicas

### Requirement: Grupos de exame e recebimento parcial
As amostras SHALL ser agrupadas pela chave `<codigoSolicitacao>:<tipoExame>`. O passo "Conferir" SHALL permitir selecionar grupos inteiros para recebimento, todos selecionados por padrão. Grupos desmarcados permanecem pendentes; amostras de um mesmo grupo não podem ser recebidas parcialmente.

#### Scenario: Recebimento parcial por tipo
- **WHEN** uma solicitação possui grupos HP e CO e o usuário seleciona apenas CO
- **THEN** o grupo CO é recebido e HP permanece pendente na mesma solicitação

#### Scenario: Nenhum grupo selecionado
- **WHEN** o usuário desmarca todos os grupos e confirma
- **THEN** a confirmação é recusada e nenhum registro é persistido

### Requirement: Registro da conferência
O sistema SHALL registrar cada conferência com a chave do grupo, o código da solicitação, as amostras, o resultado, a observação, o usuário e a data e hora. O resultado SHALL ser "aceita" na confirmação da entrada e "rejeitada" quando terminar em não conformidade.

#### Scenario: Conferência aceita
- **WHEN** a entrada é confirmada
- **THEN** a conferência fica registrada como aceita, com as amostras do grupo, e aparece na aba "Recepção" do caso

#### Scenario: Conferência rejeitada
- **WHEN** o usuário registra uma não conformidade para um ou mais grupos selecionados
- **THEN** a conferência fica registrada como rejeitada para os grupos devolvidos

### Requirement: Ações do passo de conferência
O passo "Conferir" SHALL oferecer "Confirmar conferência", "Registrar não conformidade" e "Ler outra etiqueta". A confirmação SHALL avançar diretamente para "Etiquetas e ficha" sem uma etapa de complementação separada.

#### Scenario: Ler outra etiqueta
- **WHEN** o usuário clica em "Ler outra etiqueta"
- **THEN** o sistema volta ao passo 1 com o campo limpo e em foco, sem registrar conferência

### Requirement: Dados para confirmação
Para cada grupo principal selecionado, o passo "Conferir" SHALL exigir um procedimento padronizado. A urgência SHALL ser uma única escolha da solicitação, sem valor padrão e sem campo de motivo. A quantidade de amostras SHALL vir do grupo no AGHU; observações são opcionais.

#### Scenario: Quantidade obtida do AGHU
- **WHEN** um grupo contém três amostras
- **THEN** a conferência mostra as três amostras sem campo editável de quantidade

#### Scenario: Urgência não informada
- **WHEN** o usuário tenta confirmar sem escolher Sim ou Não em "Urgente?"
- **THEN** a confirmação é recusada e o campo é indicado como obrigatório

#### Scenario: Congelação selecionada
- **WHEN** o usuário seleciona um grupo CO
- **THEN** "Urgente?" passa a Sim e não é editável

#### Scenario: Urgência sem justificativa
- **WHEN** o usuário escolhe "Sim" para urgência e preenche os procedimentos
- **THEN** a confirmação não exige justificativa de urgência

### Requirement: Vínculo da IHQ ao caso de origem
Para o tipo IHQ, o fluxo ideal é o pedido já chegar vinculado ao caso de origem pelo AGHU. Como contingência, a recepção SHALL poder vincular manualmente o grupo a um caso já existente e o sistema não SHALL gerar um novo caso. Só são aceitos casos principais (HP, CG, CCV ou CO) que não estejam devolvidos nem cancelados. A busca é feita por número interno, prontuário ou nome.

#### Scenario: Busca do caso de origem
- **WHEN** o usuário seleciona IHQ e digita "HP-0003" no campo de caso de origem
- **THEN** o sistema lista os casos elegíveis correspondentes, com número, paciente, material e status

#### Scenario: Caso não elegível
- **WHEN** o caso pesquisado está devolvido ou cancelado
- **THEN** o caso não pode ser selecionado e o sistema informa o motivo

#### Scenario: Paciente divergente
- **WHEN** o caso escolhido é de um prontuário diferente do da solicitação IHQ
- **THEN** o sistema exibe um alerta de divergência e só permite confirmar após o usuário confirmar explicitamente o vínculo

### Requirement: Validação antes da confirmação
Ao tentar confirmar com campos obrigatórios faltando, o sistema SHALL recusar a confirmação, mostrar um resumo com a quantidade e a lista dos campos faltantes, com link para cada um, e destacar cada campo com a sua mensagem.

#### Scenario: Dois campos faltando
- **WHEN** o usuário confirma sem procedimento e sem "Urgente?"
- **THEN** o sistema exibe "Faltam 2 campos obrigatórios para confirmar" com links para os dois campos e não cria o caso

### Requirement: Confirmação da entrada do caso principal
Ao confirmar a entrada de um caso principal, o sistema SHALL, em uma única operação:
- criar o caso com status "Recebido";
- definir a próxima etapa pelo fluxo do tipo;
- registrar data e hora de entrada e o usuário autenticado como responsável;
- criar uma amostra por peça ou frasco;
- registrar a conferência e o evento no histórico;
- marcar a solicitação do AGHU como recebida.

#### Scenario: Entrada HP
- **WHEN** o usuário confirma a entrada de uma solicitação HP com quantidade 2
- **THEN** é criado um caso "Recebido" encaminhado para Macroscopia, com duas amostras, e a solicitação sai da lista de pendentes

#### Scenario: Próxima etapa por tipo
- **WHEN** a entrada é confirmada
- **THEN** o encaminhamento é Macroscopia para HP, Processamento técnico para CG e CCV, e Congelação para CO

#### Scenario: Atalho de teclado
- **WHEN** o usuário pressiona Ctrl+Enter no passo "Conferir"
- **THEN** o sistema executa a confirmação como se o botão fosse clicado

### Requirement: Número interno do caso
O número interno SHALL seguir o formato `<TIPO>-<NNNN>/<AA>`, com sequência de 4 dígitos própria de cada tipo e ano e o ano com 2 dígitos (ex.: `HP-0012/26`, `CCV-0004/26`), e SHALL ser único.

#### Scenario: Sequência por tipo
- **WHEN** o último caso HP de 2026 é `HP-0011/26` e o último CG é `CG-0005/26`
- **THEN** a próxima entrada HP gera `HP-0012/26` e a próxima CG gera `CG-0006/26`

### Requirement: Confirmação da IHQ
Ao confirmar uma IHQ, o sistema SHALL:
- registrar a IHQ no caso de origem com código próprio `IH-<NNNN>/<AA>` (sequência própria por ano), situação "Solicitada" e vínculo com a solicitação do AGHU;
- registrar o evento no histórico do caso de origem;
- marcar a solicitação como recebida;
- não criar um novo caso.

#### Scenario: IHQ vinculada
- **WHEN** o usuário confirma uma IHQ vinculada ao caso HP-0003/26
- **THEN** a IHQ aparece na aba "IHQ" do HP-0003/26 com o código gerado, e a Consulta de casos não ganha nenhum caso novo

### Requirement: Tela de resultado
O passo "Etiquetas e ficha" SHALL exibir um bloco por caso ou IHQ gerado, com número, ação de copiar e ações pertinentes de impressão e abertura de detalhe. SHALL exibir uma vez o lembrete de registrar a solicitação no AGHU e avisar quais grupos continuam pendentes.

#### Scenario: Receber próxima
- **WHEN** o usuário clica em "Receber próxima amostra"
- **THEN** o sistema volta ao passo 1 com o campo limpo e em foco

#### Scenario: Copiar número
- **WHEN** o usuário clica em copiar
- **THEN** o número interno é copiado e o sistema confirma com uma mensagem

### Requirement: Alerta de congelação
Após a entrada de um caso de congelação (CO), o resultado SHALL exibir um alerta para acionar a equipe de plantão, com a ação "Registrar acionamento do plantão", que grava o evento no histórico uma única vez.

#### Scenario: Acionamento registrado
- **WHEN** o usuário clica em "Registrar acionamento do plantão"
- **THEN** o evento é gravado no histórico do caso e a ação passa a indicar que o plantão foi acionado, sem permitir novo registro

### Requirement: Autorização das operações existentes da Recepção

Operações protegidas da Recepção SHALL exigir a permissão explícita correspondente no backend. A interface SHALL refletir as permissões efetivas, mas sua ocultação de ações SHALL NOT substituir a autorização da API. O catálogo poderá evoluir junto com cada módulo; uma matriz global completa SHALL NOT ser requisito para concluir esta mudança.

#### Scenario: Operação autorizada

- **WHEN** identidade autenticada possui a permissão explícita para uma operação existente
- **THEN** o backend executa a operação e usa a identidade autenticada como autora

#### Scenario: Operação não autorizada por chamada direta

- **WHEN** identidade autenticada sem a permissão correspondente chama diretamente a operação da Recepção
- **THEN** o backend responde 403 sem executar a mutação

#### Scenario: Operação fora do catálogo vigente

- **WHEN** um perfil tenta executar uma operação sem concessão explícita no catálogo
- **THEN** o backend nega a operação por padrão
- **AND** o catálogo pode ser ampliado junto com o módulo que implementar essa operação

### Requirement: Impressão física no navegador

A pré-visualização e impressão SHALL ocorrer apenas no navegador. A seleção de etiquetas SHALL permitir imprimir apenas parte das amostras do caso. A impressão SHALL NOT chamar API, adicionar histórico ou gerar `AuditLog`.

#### Scenario: Impressão parcial de etiquetas

- **WHEN** o usuário seleciona algumas amostras e imprime etiquetas de um caso consultável
- **THEN** o navegador imprime apenas as etiquetas selecionadas sem criar registro no backend

### Requirement: Associação da IHQ ao caso de origem

Para receber um grupo IHQ cujo vínculo não veio do AGHU, a interface SHALL permitir que a recepção escolha manualmente um caso principal elegível como contingência. O fluxo ideal é usar o vínculo já fornecido pelo AGHU. O sistema SHALL validar a divergência de prontuário, exigir confirmação explícita quando houver divergência e persistir o vínculo e a conferência. A ação SHALL exigir a permissão `recepcao:receber`.

#### Scenario: Caso de origem com prontuário divergente

- **WHEN** o prontuário do caso escolhido diverge do prontuário da solicitação IHQ
- **THEN** a interface exige confirmação explícita antes de persistir o vínculo
