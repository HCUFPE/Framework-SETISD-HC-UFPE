# app-navigation Specification

## Purpose

Organiza o menu lateral em seções e dá acesso autenticado às telas do fluxo de recepção, separando as páginas de demonstração do framework das telas de trabalho do setor.

## Requirements

### Requirement: Seções do menu lateral
O menu lateral SHALL exibir duas seções com título. A seção "Recepção" contém Recepção de amostras, Consulta de casos e Rejeições e devoluções, nessa ordem. A seção "Outros" contém Início, Componentes, Novidades dos Componentes, Exemplo e Configurações, nessa ordem.

#### Scenario: Usuário autenticado abre o sistema
- **WHEN** o usuário autenticado vê o menu lateral expandido
- **THEN** são exibidas as seções "Recepção" e "Outros", com os itens na ordem definida

#### Scenario: Menu recolhido
- **WHEN** o usuário recolhe o menu lateral
- **THEN** os títulos das seções são ocultados e os itens continuam acessíveis pelos ícones, com o nome exibido como dica

### Requirement: Contador de solicitações pendentes
O item "Recepção de amostras" SHALL exibir a quantidade de solicitações do AGHU aguardando recebimento e SHALL atualizá-la quando uma solicitação for recebida ou devolvida.

#### Scenario: Solicitação recebida
- **WHEN** há 5 solicitações pendentes e o usuário confirma a entrada de uma delas
- **THEN** o contador passa a exibir 4

#### Scenario: Nenhuma pendente
- **WHEN** não há solicitações aguardando recebimento
- **THEN** o contador não é exibido

### Requirement: Acesso autenticado às telas do fluxo
As telas Recepção de amostras, Consulta de casos, Detalhe do caso e Rejeições e devoluções SHALL exigir usuário autenticado. Um acesso sem autenticação SHALL ser redirecionado para a tela de login.

#### Scenario: Acesso sem login
- **WHEN** um usuário não autenticado acessa `/recepcao`
- **THEN** o sistema exibe a tela de login

### Requirement: Item ativo no menu
O menu SHALL destacar o item da tela atual. As subtelas SHALL destacar o item de origem: o detalhe do caso destaca "Consulta de casos".

#### Scenario: Detalhe do caso aberto
- **WHEN** o usuário está no detalhe de um caso
- **THEN** o item "Consulta de casos" aparece destacado no menu

### Requirement: Botão de recolher o menu lateral
O menu lateral SHALL ter um botão próprio, com ícone de painel lateral e nome acessível "Recolher menu" ou "Expandir menu" conforme o estado, que recolhe e expande o menu. O nome do sistema no topo do menu SHALL ser apenas informativo e não SHALL recolher ou expandir o menu.

#### Scenario: Recolher pelo botão
- **WHEN** o usuário clica no botão de recolher com o menu expandido
- **THEN** o menu é recolhido, exibindo só os ícones, e o botão continua visível com o nome acessível "Expandir menu"

#### Scenario: Clique no nome do sistema
- **WHEN** o usuário clica no nome do sistema no topo do menu
- **THEN** o menu permanece no estado em que estava

### Requirement: Nome do sistema
O sistema SHALL se identificar como "Sistema de Gestão Integrada de Serviços de Anatomia Patológica" no topo do menu lateral, no cabeçalho da versão móvel e no título da aba do navegador. No menu expandido, o nome SHALL aparecer sem ícone ao lado e quebrar em várias linhas, sem cortes. No menu recolhido, o nome é ocultado e só o botão de expandir aparece no topo.

#### Scenario: Menu expandido
- **WHEN** o usuário vê o menu lateral expandido
- **THEN** o nome completo do sistema aparece no topo, sem reticências

### Requirement: Retorno à tela inicial da recepção pelo menu
Clicar no item "Recepção de amostras" do menu SHALL sempre exibir a tela inicial da recepção (passo de leitura com a lista de pendentes), mesmo que o usuário já esteja nessa tela, descartando sem confirmação o recebimento em andamento.

#### Scenario: Recebimento em andamento
- **WHEN** o usuário está no passo "Completar e confirmar" e clica em "Recepção de amostras" no menu
- **THEN** a tela volta ao passo de leitura com o campo limpo e em foco, e os dados preenchidos são descartados
