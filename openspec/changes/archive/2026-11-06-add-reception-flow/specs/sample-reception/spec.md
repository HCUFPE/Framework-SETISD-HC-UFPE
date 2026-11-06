# Spec Delta

## Purpose

Permite que a recepção do Serviço de Anatomia Patológica receba uma amostra a partir da solicitação do AGHU: conferir o material físico, completar os dados e confirmar a entrada. A confirmação gera o número interno do caso ou vincula a IHQ ao caso de origem, sem redigitar os dados que já existem no AGHU.

## ADDED Requirements

### Requirement: Passos da recepção
A tela "Recepção de amostras" SHALL conduzir o recebimento em quatro passos: "Ler etiqueta AGHU", "Conferir", "Completar e confirmar" e "Etiquetas e ficha". O indicador de passos SHALL mostrar os passos concluídos, o atual e os futuros.

#### Scenario: Início da recepção
- **WHEN** o usuário abre a tela "Recepção de amostras"
- **THEN** o passo "Ler etiqueta AGHU" é o atual e o campo de leitura recebe o foco

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
O passo 1 SHALL listar as solicitações do AGHU aguardando recebimento, com nº da solicitação, exame, material, origem e data da solicitação, e uma ação "Ler etiqueta" em cada uma, equivalente à leitura do número.

#### Scenario: Ler pela lista
- **WHEN** o usuário clica em "Ler etiqueta" em uma solicitação da lista
- **THEN** o resultado é o mesmo de ler o número dessa solicitação

#### Scenario: Lista vazia
- **WHEN** não há solicitações aguardando recebimento
- **THEN** a lista exibe "Nenhuma solicitação aguardando recebimento."

### Requirement: AGHU indisponível
Quando o serviço de solicitações do AGHU estiver indisponível, a recepção SHALL exibir um aviso, desabilitar a leitura e a lista de pendentes e manter disponível o registro de material sem etiqueta.

#### Scenario: Falha ao consultar o AGHU
- **WHEN** a consulta de solicitações falha por indisponibilidade
- **THEN** o sistema exibe "AGHU indisponível no momento. A recepção de novas amostras está bloqueada." e desabilita a leitura

### Requirement: Dados da solicitação somente leitura
O passo "Conferir" SHALL exibir, sem permitir edição e identificados como vindos do AGHU, os seguintes dados: nº da solicitação, prontuário, nome do paciente, data de nascimento com idade, sexo, origem, unidade solicitante, especialidade, médico solicitante, data da solicitação, exame, descrição do material e informações clínicas.

#### Scenario: Conferência de solicitação carregada
- **WHEN** o passo "Conferir" é exibido
- **THEN** os dados do AGHU aparecem bloqueados para edição, com destaque para a descrição do material e as informações clínicas

### Requirement: Itens de conferência
O passo "Conferir" SHALL exigir que os quatro itens sejam marcados antes de avançar: "Identificação confere com a requisição", "Material corresponde à descrição", "Quantidade de frascos confere" e "Recipiente íntegro e adequado".

#### Scenario: Conferência completa
- **WHEN** os quatro itens estão marcados e o usuário clica em "Confirmar conferência"
- **THEN** o sistema avança para o passo "Completar e confirmar"

#### Scenario: Conferência incompleta
- **WHEN** algum item está desmarcado e o usuário clica em "Confirmar conferência"
- **THEN** o sistema permanece no passo e informa que todos os itens devem ser marcados ou que deve ser registrada uma não conformidade

### Requirement: Registro da conferência
O sistema SHALL registrar cada conferência com os quatro itens, o resultado, a observação, o usuário e a data e hora. O resultado SHALL ser "aceita" na confirmação da entrada e "rejeitada" quando terminar em não conformidade.

#### Scenario: Conferência aceita
- **WHEN** a entrada é confirmada
- **THEN** a conferência fica registrada como aceita, com os quatro itens marcados, e aparece na aba "Recepção" do caso

#### Scenario: Conferência rejeitada
- **WHEN** o usuário marca apenas três itens e registra uma não conformidade
- **THEN** a conferência fica registrada como rejeitada, com os itens no estado em que estavam

### Requirement: Saídas do passo de conferência
O passo "Conferir" SHALL oferecer "Registrar não conformidade", que abre o registro com os dados da solicitação, e "Ler outra etiqueta", que descarta a conferência em andamento e volta ao passo 1.

#### Scenario: Ler outra etiqueta
- **WHEN** o usuário clica em "Ler outra etiqueta"
- **THEN** o sistema volta ao passo 1 com o campo limpo e em foco, sem registrar conferência

### Requirement: Tipo de exame
O passo "Completar e confirmar" SHALL exigir o tipo de exame entre Histopatológico (HP), Citologia geral (CG), Citologia cérvico-vaginal (CCV), Congelação (CO) e Imuno-histoquímica (IHQ), já selecionado conforme o exame do AGHU e com a opção de alterar.

#### Scenario: Tipo sugerido
- **WHEN** a solicitação do AGHU é de exame anatomopatológico
- **THEN** o tipo HP aparece selecionado, com a indicação de que veio do exame do AGHU

### Requirement: Campos de complementação do caso principal
Para os tipos HP, CG, CCV e CO, o sistema SHALL exigir quantidade de peças ou frascos (inteiro de 1 em diante), "Urgente?" (Sim ou Não, sem valor padrão) e procedimento (lista padronizada). O motivo da urgência SHALL ser exigido quando "Urgente?" for Sim. Observações são opcionais.

#### Scenario: Urgência sem motivo
- **WHEN** o usuário marca "Urgente?" como Sim e deixa o motivo vazio
- **THEN** a confirmação é recusada e o campo de motivo é indicado como obrigatório

#### Scenario: Urgência não informada
- **WHEN** o usuário tenta confirmar sem escolher Sim ou Não em "Urgente?"
- **THEN** a confirmação é recusada e o campo é indicado como obrigatório

### Requirement: Vínculo da IHQ ao caso de origem
Para o tipo IHQ, o sistema SHALL exigir a escolha de um caso já existente e não SHALL gerar um novo caso. Só são aceitos casos principais (HP, CG, CCV ou CO) que não estejam devolvidos nem cancelados. A busca é feita por número interno, prontuário ou nome.

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
- **WHEN** o usuário pressiona Ctrl+Enter no passo "Completar e confirmar"
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
O passo "Etiquetas e ficha" SHALL exibir:
- o número gerado, com botão de copiar;
- a etapa para a qual o caso foi encaminhado;
- o selo URGENTE, quando for o caso;
- o lembrete "Registrar o recebimento no AGHU (solicitação <nº>)";
- as ações "Imprimir etiqueta(s)", "Imprimir ficha de trabalho", "Abrir detalhe do caso" e "Receber próxima amostra".

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
