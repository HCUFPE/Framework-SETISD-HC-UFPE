# Spec Delta

## Purpose

Organiza o menu lateral em seções e dá acesso autenticado às telas do fluxo de recepção, separando as páginas de demonstração do framework das telas de trabalho do setor.

## ADDED Requirements

### Requirement: Seções do menu lateral
O menu lateral SHALL exibir duas seções com título. A seção "Recepção" contém Início, Recepção de amostras, Consulta de casos, Rejeições e devoluções e Configurações, nessa ordem. A seção "Temporário" contém Componentes, Novidades dos Componentes e Exemplo.

#### Scenario: Usuário autenticado abre o sistema
- **WHEN** o usuário autenticado vê o menu lateral expandido
- **THEN** são exibidas as seções "Recepção" e "Temporário", com os itens na ordem definida

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
