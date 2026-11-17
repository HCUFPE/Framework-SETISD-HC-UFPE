## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Leitura da solicitação AGHU
No passo 1, o usuário SHALL informar o código da solicitação AGHU por leitor ou digitação, confirmando com Enter. O código pode vir só com o número da solicitação ou no formato `<solicitação>-<amostra>`; em ambos os casos, uma solicitação com tipos de exame aguardando recebimento SHALL abrir o passo "Conferir" com todos os tipos pendentes dela.

#### Scenario: Solicitação pendente
- **WHEN** o usuário informa o código de uma solicitação com amostras aguardando recebimento e pressiona Enter
- **THEN** os dados da solicitação e todas as amostras pendentes são carregados no passo "Conferir"

#### Scenario: Leitura com número da amostra
- **WHEN** o usuário lê "1200001-3"
- **THEN** o sistema abre a conferência da solicitação 1200001 inteira

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

### Requirement: Dados da solicitação somente leitura
O passo "Conferir" SHALL exibir, sem permitir edição e identificados como vindos do AGHU, os seguintes dados: nº da solicitação, prontuário, nome completo do paciente, data de nascimento com idade, origem, unidade solicitante, especialidade, data da solicitação e informações clínicas, além da tabela de amostras com o exame de cada uma. Os campos seguem o dicionário de dados do AGHU.

#### Scenario: Conferência de solicitação carregada
- **WHEN** o passo "Conferir" é exibido
- **THEN** os dados do AGHU aparecem bloqueados para edição, com destaque para as amostras e as informações clínicas, e sem campos de sexo nem de médico solicitante

### Requirement: Registro da conferência
O sistema SHALL registrar cada conferência com o exame e as amostras conferidas, o resultado, a observação, o usuário e a data e hora. O resultado SHALL ser "aceita" na confirmação da entrada e "rejeitada" quando terminar em não conformidade.

#### Scenario: Conferência aceita
- **WHEN** a entrada é confirmada
- **THEN** a conferência fica registrada como aceita, com as amostras conferidas, e aparece na aba "Recepção" do caso

#### Scenario: Conferência rejeitada
- **WHEN** o usuário registra uma não conformidade na conferência
- **THEN** a conferência fica registrada como rejeitada, vinculada à não conformidade

### Requirement: Saídas do passo de conferência
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

### Requirement: Campos de complementação do caso principal
A urgência SHALL ser da solicitação, não de cada tipo de exame: quando houver tipo principal (HP, CG, CCV, CO) marcado para receber, o painel de conferência SHALL exibir um único "Urgente?" (Sim ou Não, sem valor padrão), aplicado a todos os casos gerados na conferência, sem campo de motivo. Para cada tipo principal marcado, SHALL exigir o procedimento (lista padronizada com busca). A quantidade de amostras SHALL ser a do tipo no AGHU, sem campo editável. Observações são opcionais e valem para todos os registros da conferência. Quando um tipo Congelação (CO) estiver marcado, "Urgente?" SHALL ficar em Sim e não ser editável.

#### Scenario: Quantidade vinda do AGHU
- **WHEN** o grupo HP tem 3 amostras
- **THEN** o bloco HP indica "amostras 1, 2, 3", sem campo editável de quantidade

#### Scenario: Urgência única da solicitação
- **WHEN** a solicitação tem os grupos HP e IHQ e o usuário marca "Urgente?" como Sim
- **THEN** há um só campo "Urgente?" no painel, sem campo de motivo, e o caso HP gerado fica urgente

#### Scenario: Urgência sem motivo
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

### Requirement: Passos da recepção
A tela "Recepção de amostras" SHALL conduzir o recebimento em três passos: "Ler etiqueta AGHU", "Conferir" e "Etiquetas e ficha". O indicador de passos SHALL aparecer apenas a partir do passo "Conferir", mostrando os passos concluídos, o atual e os futuros. A tela inicial (passo "Ler etiqueta AGHU") não SHALL exibir o indicador.

#### Scenario: Início da recepção
- **WHEN** o usuário abre a tela "Recepção de amostras"
- **THEN** o passo "Ler etiqueta AGHU" é exibido sem o indicador de passos, e o campo de leitura recebe o foco

#### Scenario: Conferência iniciada
- **WHEN** o usuário inicia o recebimento de uma solicitação
- **THEN** o indicador de passos é exibido com "Ler etiqueta AGHU" concluído e "Conferir" como atual, seguido apenas de "Etiquetas e ficha"

### Requirement: Tipo de exame
O tipo de exame de cada grupo (Histopatológico HP, Citologia geral CG, Citologia cérvico-vaginal CCV, Congelação CO ou Imuno-histoquímica IHQ) SHALL ser definido pelas siglas dos exames do AGHU e exibido no passo "Conferir" sem opção de alterar.

#### Scenario: Tipo sugerido
- **WHEN** as amostras da solicitação são do exame APECR
- **THEN** o passo "Conferir" exibe o bloco "HP · Histopatológico", sem campo para trocar o tipo

### Requirement: Validação antes da confirmação
Ao tentar confirmar a conferência com campos obrigatórios faltando, o sistema SHALL recusar a confirmação, mostrar um resumo com a quantidade e a lista dos campos faltantes, com link para cada um, e destacar cada campo com a sua mensagem.

#### Scenario: Dois campos faltando
- **WHEN** o usuário clica em "Confirmar conferência" sem procedimento e sem "Urgente?"
- **THEN** o sistema exibe "Faltam 2 campos obrigatórios para confirmar" com links para os dois campos e não cria o caso

## REMOVED Requirements

### Requirement: Itens de conferência
**Reason**: Os quatro checkboxes tornavam a conferência mais lenta sem gerar informação útil. Quando algo não confere, o caminho é a não conformidade, que agora usa o catálogo do formulário do setor.
**Migration**: "Confirmar conferência" avança direto. As divergências que os itens cobriam (identificação, material, quantidade, recipiente) são registradas como não conformidade com o tipo correspondente.
