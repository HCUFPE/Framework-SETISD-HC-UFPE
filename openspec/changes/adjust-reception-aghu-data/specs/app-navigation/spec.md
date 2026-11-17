## MODIFIED Requirements

### Requirement: Botão de recolher o menu lateral
O menu lateral SHALL ter um botão próprio, com ícone de painel lateral e nome acessível "Recolher menu" ou "Expandir menu" conforme o estado, que recolhe e expande o menu. Com o menu recolhido, um clique em qualquer parte dele SHALL expandi-lo, com cursor de mão em toda a área (um clique em item do menu também navega). O nome do sistema no topo do menu expandido SHALL ser apenas informativo e não SHALL recolher o menu.

#### Scenario: Recolher pelo botão
- **WHEN** o usuário clica no botão de recolher com o menu expandido
- **THEN** o menu é recolhido, exibindo só os ícones, e o botão continua visível com o nome acessível "Expandir menu"

#### Scenario: Expandir clicando no menu recolhido
- **WHEN** o usuário clica em uma área vazia do menu recolhido
- **THEN** o menu é expandido

#### Scenario: Clique no nome do sistema
- **WHEN** o usuário clica no nome do sistema no topo do menu expandido
- **THEN** o menu permanece expandido

### Requirement: Seções do menu lateral
O menu lateral SHALL exibir duas seções com título. A seção "Recepção" contém Recepção de amostras, Consulta de casos e Devoluções, nessa ordem. A seção "Outros" contém Início, Componentes, Novidades dos Componentes, Exemplo e Configurações, nessa ordem.

#### Scenario: Usuário autenticado abre o sistema
- **WHEN** o usuário autenticado vê o menu lateral expandido
- **THEN** são exibidas as seções "Recepção" e "Outros", com os itens na ordem definida, e o item de devoluções se chama "Devoluções"

#### Scenario: Menu recolhido
- **WHEN** o usuário recolhe o menu lateral
- **THEN** os títulos das seções são ocultados e os itens continuam acessíveis pelos ícones, com o nome exibido como dica

### Requirement: Contador de solicitações pendentes
O item "Recepção de amostras" SHALL exibir a quantidade de solicitações do AGHU (não de amostras nem de tipos de exame) com amostras aguardando recebimento e SHALL atualizá-la quando um recebimento ou devolução esvaziar a solicitação.

#### Scenario: Solicitação recebida
- **WHEN** todos os tipos pendentes de uma solicitação são recebidos
- **THEN** o contador diminui em uma unidade

#### Scenario: Recebimento parcial
- **WHEN** só um de dois tipos pendentes de uma solicitação é recebido
- **THEN** o contador não muda, pois a solicitação continua pendente

#### Scenario: Nenhuma pendente
- **WHEN** não há solicitações aguardando recebimento
- **THEN** o contador não é exibido
