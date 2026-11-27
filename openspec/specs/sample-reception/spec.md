# sample-reception Specification

## Purpose

Permite que a recepção do Serviço de Anatomia Patológica receba uma amostra a partir da solicitação do AGHU: conferir o material físico, completar os dados e confirmar a entrada. A confirmação gera o número interno do caso ou vincula a IHQ ao caso de origem, sem redigitar os dados que já existem no AGHU.

## Requirements

### Requirement: Passos da recepção
A tela "Recepção de amostras" SHALL conduzir o recebimento em três passos: "Ler etiqueta AGHU", "Conferir" e "Etiquetas e ficha". O indicador de passos SHALL aparecer apenas a partir do passo "Conferir", mostrando os passos concluídos, o atual e os futuros. A tela inicial (passo "Ler etiqueta AGHU") não SHALL exibir o indicador.

#### Scenario: Início da recepção
- **WHEN** o usuário abre a tela "Recepção de amostras"
- **THEN** o passo "Ler etiqueta AGHU" é exibido sem o indicador de passos, e o campo de leitura recebe o foco

#### Scenario: Conferência iniciada
- **WHEN** o usuário inicia o recebimento de uma solicitação
- **THEN** o indicador de passos é exibido com "Ler etiqueta AGHU" concluído e "Conferir" como atual, seguido apenas de "Etiquetas e ficha"

### Requirement: Leitura da solicitação AGHU
No passo 1, o usuário SHALL informar o código da solicitação AGHU por leitor ou digitação, confirmando com Enter. O código pode vir apenas com o número da solicitação, no formato `<solicitação>-<amostra>`, no formato `<solicitação>:<tipo>` ou como código de barras contínuo de 10 dígitos do AGHU (`<7 dígitos da solicitação><3 dígitos da amostra>`); em todos os casos, uma solicitação com tipos de exame aguardando recebimento SHALL abrir o passo "Conferir" com os tipos pendentes dela.

#### Scenario: Solicitação pendente
- **WHEN** o usuário informa o código de uma solicitação com amostras aguardando recebimento e pressiona Enter
- **THEN** os dados da solicitação e todas as amostras pendentes são carregados no passo "Conferir"

#### Scenario: Leitura com código de barras de 10 dígitos do AGHU
- **WHEN** o usuário lê `"7712340001"`
- **THEN** o sistema extrai a solicitação `"7712340"` e a amostra `"001"` e abre a conferência da solicitação `"7712340"` destacando a amostra bipada

#### Scenario: Leitura com número da amostra
- **WHEN** o usuário lê `"1200001-3"`
- **THEN** o sistema abre a conferência da solicitação `1200001` destacando a amostra `"3"`

#### Scenario: Campo vazio
- **WHEN** o usuário pressiona Enter com o campo vazio
- **THEN** nada é carregado e o sistema pede que informe o número da solicitação

### Requirement: Solicitação não recebível
O sistema SHALL recusar a leitura de uma solicitação que não tem exame aguardando recebimento, com uma mensagem que diga o motivo e permaneça no passo 1.

#### Scenario: Solicitação já recebida
- **WHEN** o usuário lê uma solicitação cujos exames já foram todos recebidos, um deles como o caso HP-0007/26
- **THEN** o sistema informa que a solicitação já foi recebida, lista os casos gerados e oferece abrir cada um

#### Scenario: Solicitação devolvida
- **WHEN** o usuário lê uma solicitação que foi devolvida por não conformidade
- **THEN** o sistema informa que a solicitação foi devolvida, com a data e o tipo da não conformidade

#### Scenario: Solicitação inexistente
- **WHEN** o usuário lê um número que não corresponde a nenhuma solicitação
- **THEN** o sistema informa "Nenhuma solicitação encontrada para <nº>. Confira a etiqueta ou digite o número." e lembra que material sem etiqueta do AGHU deve ser devolvido

### Requirement: Lista de solicitações pendentes
O passo 1 SHALL apresentar as solicitações do AGHU com amostras aguardando recebimento como uma fila de tarefas, um item por solicitação, cujo título é o selo "<N> solicitação(ões) para receber". Cada item mostra o nº da solicitação, os tipos de exame pendentes, a quantidade de amostras, o paciente, o material, a origem, a data da solicitação e há quantos dias aguarda, e tem a ação "Iniciar recebimento", que abre a conferência da solicitação. A fila SHALL listar primeiro as solicitações com Congelação e depois as demais, da mais antiga para a mais nova. Itens que aguardam há 1 dia ou mais SHALL ser destacados. A fila SHALL ser paginada em 10 solicitações por página, com "Exibindo <início>–<fim> de <total>", "Anterior" e "Próxima", quando houver mais de 10.

#### Scenario: Fila paginada
- **WHEN** há 200 solicitações aguardando recebimento
- **THEN** a fila mostra as 10 primeiras, informa "Exibindo 1–10 de 200" e "Página 1 de 20", com "Anterior" desabilitado

#### Scenario: Ler pela lista
- **WHEN** o usuário clica em "Iniciar recebimento" em um item da fila
- **THEN** o passo "Conferir" é aberto com todas as amostras pendentes da solicitação

#### Scenario: Solicitação com dois tipos
- **WHEN** a solicitação 1200001 tem os grupos CO e HP pendentes, com 3 amostras no total
- **THEN** a fila mostra um único item para 1200001, com os selos CO e HP e "3 amostras"

#### Scenario: Total de solicitações no título
- **WHEN** há 9 solicitações com amostras aguardando recebimento
- **THEN** o título da fila é o selo "9 solicitações para receber"

#### Scenario: Espera longa
- **WHEN** uma solicitação foi feita há 3 dias
- **THEN** o item exibe "há 3 dias" com destaque de atraso

#### Scenario: Solicitado hoje
- **WHEN** uma solicitação foi feita hoje
- **THEN** o item exibe "hoje", sem destaque de atraso

#### Scenario: Lista vazia
- **WHEN** não há solicitações aguardando recebimento
- **THEN** a fila exibe "Nenhuma solicitação aguardando recebimento." com indicação de que não há tarefas pendentes

### Requirement: AGHU indisponível
Quando o serviço de solicitações do AGHU estiver indisponível, a recepção SHALL exibir um aviso, desabilitar a leitura e a lista de pendentes e manter disponível o registro de material sem etiqueta.

#### Scenario: Falha ao consultar o AGHU
- **WHEN** a consulta de solicitações falha por indisponibilidade
- **THEN** o sistema exibe "AGHU indisponível no momento. A recepção de novas amostras está bloqueada." e desabilita a leitura

### Requirement: Dados da solicitação somente leitura
O passo "Conferir" SHALL exibir, sem permitir edição e identificados como vindos do AGHU, os seguintes dados: nº da solicitação, prontuário, nome completo do paciente, data de nascimento com idade, origem, unidade solicitante, especialidade, data da solicitação e informações clínicas, além da tabela de amostras com o exame de cada uma. Os campos seguem o dicionário de dados do AGHU.

#### Scenario: Conferência de solicitação carregada
- **WHEN** o passo "Conferir" é exibido
- **THEN** os dados do AGHU aparecem bloqueados para edição, com destaque para as amostras e as informações clínicas, e sem campos de sexo nem de médico solicitante

### Requirement: Grupos de exame e recebimento parcial
As amostras SHALL ser agrupadas pela chave `<codigoSolicitacao>:<tipoExame>`. O passo "Conferir" SHALL exibir todos os grupos pendentes da solicitação e permitir selecionar grupos inteiros para recebimento, todos selecionados por padrão quando a leitura não especificar amostra. Quando a leitura identificar uma amostra específica pertencente a um grupo pendente em solicitação com múltiplos grupos, o passo "Conferir" SHALL exibir todos os grupos pendentes por padrão, pré-marcando e destacando apenas o grupo correspondente à amostra bipada e mantendo os demais visíveis e desmarcados para seleção direta. Grupos desmarcados permanecem pendentes; amostras de um mesmo grupo não podem ser recebidas parcialmente.

#### Scenario: Recebimento parcial por tipo
- **WHEN** uma solicitação possui grupos HP e CO e o usuário seleciona apenas CO
- **THEN** o grupo CO é recebido e HP permanece pendente na mesma solicitação

#### Scenario: Solicitação mista bipada por etiqueta de 10 dígitos
- **WHEN** a solicitação `7712340` possui grupos `CO` (amostra `1`) e `HP` (amostra `2`) pendentes e o usuário bipa `"7712340002"`
- **THEN** a conferência exibe ambos os grupos pendentes (`CO` e `HP`), com apenas o grupo `HP` pré-marcado e destacado pela amostra bipada e o grupo `CO` visível e desmarcado para seleção direta

#### Scenario: Nenhum grupo selecionado
- **WHEN** o usuário desmarca todos os grupos e confirma
- **THEN** a confirmação é recusada e nenhum registro é persistido

### Requirement: Registro da conferência
O sistema SHALL registrar cada conferência com o exame e as amostras conferidas, o resultado, a observação, o usuário e a data e hora. O resultado SHALL ser "aceita" na confirmação da entrada e "rejeitada" quando terminar em não conformidade.

#### Scenario: Conferência aceita
- **WHEN** a entrada é confirmada
- **THEN** a conferência fica registrada como aceita, com as amostras conferidas, e aparece na aba "Recepção" do caso

#### Scenario: Conferência rejeitada
- **WHEN** o usuário registra uma não conformidade na conferência
- **THEN** a conferência fica registrada como rejeitada, vinculada à não conformidade

### Requirement: Ações do passo de conferência
O passo "Conferir" SHALL exibir, sem checkboxes de conferência, os campos de entrada e as ações "Confirmar conferência" e "Registrar não conformidade". "Confirmar conferência" valida os campos e confirma a entrada (gera o caso ou vincula a IHQ), indo direto para "Etiquetas e ficha". "Registrar não conformidade" abre o modal "Não conformidade e devolução". SHALL oferecer também "Ler outra etiqueta", que descarta a conferência e volta ao passo 1.

#### Scenario: Confirmar conferência
- **WHEN** o usuário preenche os campos obrigatórios e clica em "Confirmar conferência"
- **THEN** a entrada é confirmada e o sistema vai para "Etiquetas e ficha"

#### Scenario: Sem checkboxes
- **WHEN** o passo "Conferir" é exibido
- **THEN** não há checkboxes de conferência

#### Scenario: Ler outra etiqueta
- **WHEN** o usuário clica em "Ler outra etiqueta"
- **THEN** o sistema volta ao passo 1 com o campo limpo e em foco, sem registrar conferência

### Requirement: Dados para confirmação
A urgência SHALL ser da solicitação, não de cada tipo de exame: quando houver tipo principal (HP, CG, CCV, CO) marcado para receber, o painel de conferência SHALL exibir um único "Urgente?" (Sim ou Não, sem valor padrão), aplicado a todos os casos gerados na conferência, sem campo de motivo. Para cada tipo principal marcado, SHALL exigir o procedimento (lista padronizada com busca). A quantidade de amostras SHALL ser a do tipo no AGHU, sem campo editável. Observações são opcionais e valem para todos os registros da conferência. Quando um tipo Congelação (CO) estiver marcado, "Urgente?" SHALL ficar em Sim e não ser editável.

#### Scenario: Quantidade obtida do AGHU
- **WHEN** o grupo HP tem 3 amostras
- **THEN** o bloco HP indica "amostras 1, 2, 3", sem campo editável de quantidade

#### Scenario: Urgência única da solicitação
- **WHEN** a solicitação tem os grupos HP e IHQ e o usuário marca "Urgente?" como Sim
- **THEN** há um só campo "Urgente?" no painel, sem campo de motivo, e o caso HP gerado fica urgente

#### Scenario: Urgência sem justificativa
- **WHEN** o usuário marca "Urgente?" como Sim e preenche os procedimentos
- **THEN** a confirmação é aceita sem pedir motivo, pois não há campo de motivo da urgência

#### Scenario: Urgência não informada
- **WHEN** o usuário tenta confirmar sem escolher Sim ou Não em "Urgente?"
- **THEN** a confirmação é recusada e o campo é indicado como obrigatório

#### Scenario: Congelação selecionada
- **WHEN** a solicitação tem os grupos CO e HP marcados para receber
- **THEN** "Urgente?" aparece em Sim, sem opção de alterar, e os dois casos gerados ficam urgentes

#### Scenario: Troca de Congelação para outro tipo
- **WHEN** o usuário desmarca o grupo CO e mantém só o HP
- **THEN** "Urgente?" volta a ser editável e sem valor escolhido

#### Scenario: Só IHQ
- **WHEN** a conferência tem apenas o grupo IHQ marcado
- **THEN** o campo "Urgente?" não é exibido, pois a IHQ não gera caso novo

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
Ao tentar confirmar a conferência com campos obrigatórios faltando, o sistema SHALL recusar a confirmação, mostrar um resumo com a quantidade e a lista dos campos faltantes, com link para cada um, e destacar cada campo com a sua mensagem.

#### Scenario: Dois campos faltando
- **WHEN** o usuário clica em "Confirmar conferência" sem procedimento e sem "Urgente?"
- **THEN** o sistema exibe "Faltam 2 campos obrigatórios para confirmar" com links para os dois campos e não cria o caso

### Requirement: Confirmação da entrada do caso principal
Ao confirmar a conferência, o sistema SHALL, para cada tipo principal marcado:
- criar um caso com status "Recebido";
- definir a próxima etapa pelo fluxo do tipo;
- registrar data e hora de entrada e o usuário autenticado como responsável;
- criar uma amostra do caso para cada amostra do tipo no AGHU, com o número e a descrição do material dela;
- registrar a conferência e o evento no histórico;
- marcar o grupo como recebido, mantendo pendentes os tipos não marcados.

#### Scenario: Entrada HP
- **WHEN** o usuário confirma a conferência de uma solicitação com o grupo HP das amostras 2 e 3
- **THEN** é criado um caso "Recebido" encaminhado para Macroscopia, com duas amostras identificadas como 2 e 3

#### Scenario: Dois tipos na mesma confirmação
- **WHEN** o usuário confirma a conferência com os grupos CO e HP marcados
- **THEN** são criados dois casos, um CO e um HP, cada um com as suas amostras

#### Scenario: Próxima etapa por tipo
- **WHEN** a entrada é confirmada
- **THEN** o encaminhamento é Macroscopia para HP, Processamento técnico para CG e CCV, e Congelação para CO

#### Scenario: Atalho de teclado
- **WHEN** o usuário pressiona Ctrl+Enter no passo "Conferir"
- **THEN** o sistema executa a confirmação como se "Confirmar conferência" fosse clicado

### Requirement: Número interno do caso
O número interno SHALL seguir o formato `<TIPO>-<NNNN>/<AA>`, com sequência de 4 dígitos própria de cada tipo e ano e o ano com 2 dígitos (ex.: `HP-0012/26`, `CCV-0004/26`), e SHALL ser único.

#### Scenario: Sequência por tipo
- **WHEN** o último caso HP de 2026 é `HP-0011/26` e o último CG é `CG-0005/26`
- **THEN** a próxima entrada HP gera `HP-0012/26` e a próxima CG gera `CG-0006/26`

### Requirement: Confirmação da IHQ
Para o grupo IHQ marcado, o painel SHALL pedir o caso de origem. Quando a mesma conferência recebe um tipo principal, o padrão SHALL ser vincular a IHQ ao caso principal gerado nesta conferência (HP, se houver), com a opção de escolher um caso já existente. Ao confirmar, o sistema SHALL:
- registrar a IHQ no caso de origem com código próprio `IH-<NNNN>/<AA>`, situação "Solicitada" e vínculo com a solicitação do AGHU e com as amostras do grupo;
- registrar o evento no histórico do caso de origem;
- marcar o grupo IHQ como recebido;
- não criar um novo caso.

#### Scenario: IHQ vinculada
- **WHEN** o usuário confirma uma IHQ vinculada ao caso existente HP-0003/26
- **THEN** a IHQ aparece na aba "IHQ" do HP-0003/26 com o código gerado, e a Consulta de casos não ganha nenhum caso novo

#### Scenario: IHQ e HP na mesma conferência
- **WHEN** a solicitação tem os grupos HP (amostras 1 a 3) e IHQ (amostra 4) e o usuário confirma os dois com a opção padrão
- **THEN** é criado o caso HP e a IHQ é vinculada a esse caso recém-criado

#### Scenario: Sugestão do caso da mesma solicitação
- **WHEN** a solicitação da IHQ também tem um tipo HP já recebido antes como HP-0010/26
- **THEN** o campo de caso de origem sugere o HP-0010/26, que o usuário pode aceitar ou trocar

### Requirement: Tela de resultado
O passo "Etiquetas e ficha" SHALL exibir um bloco por registro gerado na conferência (caso ou IHQ), cada um com:
- o número gerado, com botão de copiar;
- a etapa para a qual o caso foi encaminhado e o selo URGENTE, quando for o caso;
- as ações "Imprimir etiqueta(s)", "Imprimir ficha de trabalho" e "Abrir detalhe do caso".

A tela SHALL exibir também, uma única vez, o lembrete "Registrar o recebimento no AGHU (solicitação <nº>)", o aviso dos tipos da solicitação que ficaram para depois, quando houver, e a ação "Receber próxima amostra".

#### Scenario: Receber próxima
- **WHEN** o usuário clica em "Receber próxima amostra"
- **THEN** o sistema volta ao passo 1 com o campo limpo e em foco

#### Scenario: Copiar número
- **WHEN** o usuário clica em copiar
- **THEN** o número interno é copiado e o sistema confirma com uma mensagem

#### Scenario: Dois registros gerados
- **WHEN** a conferência gera o caso HP-0012/26 e a IHQ IH-0004/26
- **THEN** a tela mostra dois blocos, cada um com o próprio número e as próprias ações de impressão

#### Scenario: Outros exames pendentes
- **WHEN** a Congelação da solicitação 1200001 é recebida e o grupo HP fica para depois
- **THEN** o resultado avisa que a solicitação 1200001 ainda tem o grupo HP aguardando recebimento

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

### Requirement: Recebimento por tipo de exame da solicitação
A conferência SHALL ser feita por solicitação do AGHU, com todas as amostras pendentes dela. Dentro da solicitação, as amostras SHALL ser agrupadas pelo tipo de exame do SAP (HP, CG, CCV, CO, IHQ), definido pela sigla de cada amostra. Cada tipo é recebido, devolvido e cancelado como uma unidade: todas as amostras do tipo juntas, gerando um único caso (ou um único vínculo de IHQ) e, portanto, um único laudo.

#### Scenario: Cinco amostras do mesmo tipo
- **WHEN** a solicitação tem 5 amostras de exames histopatológicos (ex.: MBIOP e MPCIR)
- **THEN** as 5 amostras formam um só grupo HP, recebido de uma vez em um único caso

#### Scenario: Solicitação com Congelação e peça
- **WHEN** a solicitação 1200001 tem a amostra 1 com exame CONGE e as amostras 2 e 3 com exame APECR
- **THEN** a conferência abre a solicitação inteira, com o grupo CO (amostra 1) e o grupo HP (amostras 2 e 3)

### Requirement: Recebimento parcial da solicitação
Quando a solicitação tem mais de um tipo de exame pendente, a conferência SHALL permitir marcar quais tipos são recebidos agora, todos marcados por padrão. Os tipos desmarcados continuam pendentes na mesma solicitação. Dentro de um tipo não há recebimento parcial: ou todas as amostras do tipo são recebidas, ou nenhuma.

#### Scenario: Congelação recebida antes da peça
- **WHEN** o usuário desmarca o grupo HP da solicitação 1200001 e confirma só o grupo CO
- **THEN** é gerado o caso de Congelação, e a fila "Para receber" continua mostrando a solicitação 1200001, agora só com o grupo HP

#### Scenario: Todos os tipos recebidos
- **WHEN** o último tipo pendente da solicitação é recebido
- **THEN** a solicitação deixa de aparecer na fila "Para receber"

#### Scenario: Nenhum tipo marcado
- **WHEN** o usuário desmarca todos os tipos e clica em "Confirmar conferência"
- **THEN** a confirmação é recusada com o aviso "Marque ao menos um tipo de exame para receber agora."

### Requirement: Amostras na conferência
O passo "Conferir" SHALL listar as amostras pendentes da solicitação em uma tabela, uma linha por amostra em ordem de número, com as colunas "Amostra" (ex.: "Amostra 2"), "Exame" (tipo do SAP, sigla e nome do exame do AGHU daquela amostra), "Descrição do material" e "Status no AGHU", e o total de amostras no título. Uma amostra sem descrição SHALL exibir "Não informado".

#### Scenario: Solicitação com HP e IHQ
- **WHEN** a solicitação tem as amostras 1 a 3 com exame MBIOP e a amostra 4 com exame IMUHI
- **THEN** a tabela mostra 4 linhas, as três primeiras com "HP · MBIOP" e a quarta com "IHQ · IMUHI", e o total "4 amostras"

#### Scenario: Tipos já tratados
- **WHEN** um tipo da solicitação já foi recebido ou devolvido antes
- **THEN** suas amostras não aparecem na tabela, e a conferência informa que esse tipo já foi recebido (com o caso) ou devolvido

### Requirement: Tipo de exame
O tipo de exame de cada grupo (Histopatológico HP, Citologia geral CG, Citologia cérvico-vaginal CCV, Congelação CO ou Imuno-histoquímica IHQ) SHALL ser definido pelas siglas dos exames do AGHU e exibido no passo "Conferir" sem opção de alterar.

#### Scenario: Tipo sugerido
- **WHEN** as amostras da solicitação são do exame APECR
- **THEN** o passo "Conferir" exibe o bloco "HP · Histopatológico", sem campo para trocar o tipo

### Requirement: Feedback quando a amostra bipada já foi tratada
Quando a bipagem identificar uma amostra específica cujo grupo de exame já foi recebido ou devolvido, enquanto outros grupos da mesma solicitação permanecem aguardando recebimento, o sistema SHALL sinalizar claramente a situação da amostra bipada sem impedir o recebimento dos demais grupos pendentes.

#### Scenario: Amostra bipada já recebida com outro grupo pendente
- **WHEN** o grupo `CO` (amostra `1`) da solicitação já foi recebido e o grupo `HP` (amostra `2`) segue pendente, e o usuário bipa `"7712340001"`
- **THEN** a conferência abre com o grupo `HP` pendente e exibe aviso informando que a amostra bipada (`1`, grupo `CO`) já foi recebida

#### Scenario: Amostra bipada já devolvida com outro grupo pendente
- **WHEN** o grupo `CO` (amostra `1`) da solicitação já foi devolvido e o grupo `HP` (amostra `2`) segue pendente, e o usuário bipa `"7712340001"`
- **THEN** a conferência abre com o grupo `HP` pendente e exibe aviso informando que a amostra bipada (`1`, grupo `CO`) já foi devolvida

### Requirement: Situação terminal dos grupos de exame
Cada grupo de exame da solicitação SHALL possuir uma situação de recepção independente: `AGUARDANDO_RECEBIMENTO`, `RECEBIDA`, `DEVOLVIDA` ou `CANCELADA`. Cancelar um grupo SHALL mantê-lo persistido e registrar no payload o motivo, autor e data/hora. Listagem e contagem de pendentes SHALL considerar somente grupos em `AGUARDANDO_RECEBIMENTO`, preservando os grupos irmãos.

#### Scenario: Solicitação parcialmente cancelada
- **WHEN** uma solicitação possui HP e IHQ pendentes e o IHQ é cancelado
- **THEN** a fila continua exibindo a solicitação apenas com HP
- **AND** HP permanece disponível para recebimento

#### Scenario: Solicitação totalmente cancelada
- **WHEN** todos os grupos de uma solicitação foram cancelados
- **THEN** `ler_solicitacao` retorna classificação `CANCELADA` com motivo, autor e data/hora
- **AND** não classifica a solicitação como `NAO_ENCONTRADA`

#### Scenario: Leitura com grupos em estados distintos
- **WHEN** uma solicitação contém grupos cancelados e ao menos um grupo aguardando recebimento
- **THEN** a leitura retorna a conferência dos grupos pendentes
- **AND** grupos cancelados não aparecem como pendentes

#### Scenario: Bipagem de amostra pertencente a grupo cancelado
- **WHEN** o código de barras de 10 dígitos identifica uma amostra de grupo cancelado enquanto outro grupo da solicitação aguarda recebimento
- **THEN** a leitura retorna o grupo pendente restante
- **AND** a conferência informa que o grupo da amostra bipada foi cancelado

### Requirement: Ação de cancelamento na conferência
Na etapa de conferência, a interface SHALL oferecer “Cancelar exame” para cada grupo pendente somente a usuários com `CASOS_CANCELAR`. A confirmação SHALL exigir motivo não vazio. Após sucesso, a interface SHALL atualizar a conferência e a contagem de pendentes sem afetar os grupos restantes. Se todos os grupos forem cancelados, SHALL retornar ao passo inicial e informar a conclusão.

#### Scenario: Cancelar um grupo e receber outro
- **WHEN** o usuário cancela IHQ e confirma o recebimento do HP da mesma solicitação
- **THEN** somente HP é recebido e IHQ permanece cancelado

#### Scenario: Todos os exames cancelados na conferência
- **WHEN** o usuário cancela o último grupo pendente da solicitação
- **THEN** a conferência retorna ao passo inicial com feedback de cancelamento concluído

#### Scenario: Sem permissão na interface
- **WHEN** o usuário não possui `CASOS_CANCELAR`
- **THEN** a ação “Cancelar exame” não é apresentada
- **AND** a API continua protegida independentemente da interface

### Requirement: Leitura de solicitação cancelada
Quando todos os grupos da solicitação estiverem cancelados, a leitura SHALL apresentar a classificação `CANCELADA` e os metadados disponíveis do cancelamento, sem oferecer recebimento desses grupos.

#### Scenario: Leitura após cancelamento total
- **WHEN** o usuário lê uma solicitação cujos grupos foram todos cancelados
- **THEN** recebe estado `CANCELADA`, motivo, autor e data/hora, sem falso aviso de solicitação inexistente

### Requirement: Solicitação regularizada retorna à recepção
Uma solicitação reaberta após rejeição SHALL aparecer como pendente e exibir o contexto da rejeição anterior durante a nova conferência.

#### Scenario: Solicitação reaparece na fila
- **WHEN** grupos devolvidos na recepção são regularizados e reabertos
- **THEN** os grupos elegíveis aparecem em `GET /api/ap/solicitacoes/pendentes` e a leitura da solicitação os classifica como `PENDENTE`

#### Scenario: Metadados da devolução na leitura individual
- **WHEN** o usuário consulta uma solicitação reaberta por código de 7 dígitos, código com hífen ou etiqueta de 10 dígitos
- **THEN** a resposta inclui os metadados da devolução regularizada vinculada ao grupo, permitindo exibir o aviso de ocorrência anterior na conferência

#### Scenario: Metadados da devolução na fila pendente
- **WHEN** o usuário abre uma solicitação reaberta pela listagem de pendentes
- **THEN** os dados do grupo incluem os mesmos metadados da devolução regularizada retornados pela leitura individual

#### Scenario: Conferência informa rejeição anterior
- **WHEN** a equipe abre para conferência um grupo cuja rejeição anterior foi regularizada
- **THEN** a interface exibe um aviso informativo sobre a devolução anterior sem substituir ou alterar os dados originais da ocorrência

#### Scenario: Novo recebimento associa ocorrência anterior
- **WHEN** o grupo reaberto é recebido por confirmação de entrada ou vinculação IHQ
- **THEN** os registros anteriores de não conformidade e devolução são associados ao caso criado para esse grupo, sem modificar os horários da rejeição ou da regularização

### Requirement: Vínculo de Revisão ao caso de origem na recepção
Quando uma Revisão que gera caso próprio for recebida, a recepção SHALL permitir associá-la ao caso principal de origem, mantendo o fluxo de recebimento e o identificador próprios da Revisão.

#### Scenario: Revisão e caso principal na mesma solicitação
- **WHEN** uma solicitação recebida contém uma Revisão e um caso principal elegível
- **THEN** o caso principal é pré-selecionado como origem da Revisão
- **AND** o usuário pode confirmar ou escolher outro caso elegível

#### Scenario: Revisão solicitada posteriormente
- **WHEN** uma Revisão chega sem caso principal na mesma solicitação
- **THEN** o usuário pode pesquisar e selecionar manualmente um caso de origem elegível por número interno, prontuário ou nome

#### Scenario: Prontuário divergente na Revisão
- **WHEN** o caso de origem selecionado para a Revisão possui prontuário diferente do prontuário da solicitação
- **THEN** o sistema exibe alerta de divergência e só permite confirmar após confirmação explícita do usuário

#### Scenario: Revisão vinculada recebida
- **WHEN** a recepção confirma uma Revisão vinculada
- **THEN** o sistema cria o registro próprio da Revisão, persiste o vínculo com a origem e registra o evento de recebimento
- **AND** o caso de origem mantém seu status e sua identificação


### Requirement: Associação da IHQ conforme os grupos da solicitação
Quando uma solicitação AGHU de IHQ possuir grupo HP próprio, a recepção SHALL vincular a IHQ exclusivamente ao HP da mesma solicitação. A seleção manual SHALL ficar disponível somente quando não houver grupo HP próprio.

#### Scenario: HP e IHQ pendentes juntos
- **WHEN** HP e IHQ da mesma solicitação estão pendentes e ambos são marcados para receber
- **THEN** a IHQ é associada automaticamente ao HP criado na conferência, sem seletor de origem

#### Scenario: HP desmarcado e IHQ marcado
- **WHEN** HP e IHQ estão pendentes, mas somente IHQ está marcada
- **THEN** a confirmação da IHQ é bloqueada com orientação para receber o HP junto ou antes

#### Scenario: HP recebido anteriormente
- **WHEN** o HP da mesma solicitação já foi recebido e a IHQ continua pendente
- **THEN** a tela mostra apenas o número do HP associado, sem radio buttons, busca ou opção para trocar

#### Scenario: IHQ avulsa
- **WHEN** uma solicitação IHQ não possui grupo HP próprio
- **THEN** a recepção permite buscar e selecionar manualmente um histopatológico existente
- **AND** o backend aceita somente caso elegível e preserva a confirmação de divergência de prontuário
