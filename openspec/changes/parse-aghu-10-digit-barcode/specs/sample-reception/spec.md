# Spec Delta: sample-reception

## MODIFIED Requirements

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

### Requirement: Grupos de exame e recebimento parcial
As amostras SHALL ser agrupadas pela chave `<codigoSolicitacao>:<tipoExame>`. O passo "Conferir" SHALL permitir selecionar grupos inteiros para recebimento, todos selecionados por padrão quando a leitura não especificar amostra. Quando a leitura identificar uma amostra específica pertencente a um grupo pendente em solicitação com múltiplos grupos, o passo "Conferir" SHALL pré-marcar e destacar apenas o grupo correspondente à amostra bipada, mantendo opção explícita para exibir e marcar os demais grupos pendentes da solicitação. Grupos desmarcados permanecem pendentes; amostras de um mesmo grupo não podem ser recebidas parcialmente.

#### Scenario: Recebimento parcial por tipo
- **WHEN** uma solicitação possui grupos HP e CO e o usuário seleciona apenas CO
- **THEN** o grupo CO é recebido e HP permanece pendente na mesma solicitação

#### Scenario: Solicitação mista bipada por etiqueta de 10 dígitos
- **WHEN** a solicitação `7712340` possui grupos `CO` (amostra `1`) e `HP` (amostra `2`) pendentes e o usuário bipa `"7712340002"`
- **THEN** a conferência exibe o grupo `HP` pré-marcado e destacado pela amostra bipada, oferecendo opção explícita para exibir/marcar também o grupo `CO`

#### Scenario: Nenhum grupo selecionado
- **WHEN** o usuário desmarca todos os grupos e confirma
- **THEN** a confirmação é recusada e nenhum registro é persistido

## ADDED Requirements

### Requirement: Feedback quando a amostra bipada já foi tratada
Quando a bipagem identificar uma amostra específica cujo grupo de exame já foi recebido ou devolvido, enquanto outros grupos da mesma solicitação permanecem aguardando recebimento, o sistema SHALL sinalizar claramente a situação da amostra bipada sem impedir o recebimento dos demais grupos pendentes.

#### Scenario: Amostra bipada já recebida com outro grupo pendente
- **WHEN** o grupo `CO` (amostra `1`) da solicitação já foi recebido e o grupo `HP` (amostra `2`) segue pendente, e o usuário bipa `"7712340001"`
- **THEN** a conferência abre com o grupo `HP` pendente e exibe aviso informando que a amostra bipada (`1`, grupo `CO`) já foi recebida

#### Scenario: Amostra bipada já devolvida com outro grupo pendente
- **WHEN** o grupo `CO` (amostra `1`) da solicitação já foi devolvido e o grupo `HP` (amostra `2`) segue pendente, e o usuário bipa `"7712340001"`
- **THEN** a conferência abre com o grupo `HP` pendente e exibe aviso informando que a amostra bipada (`1`, grupo `CO`) já foi devolvida
