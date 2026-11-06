# ui-interaction-feedback Specification

## Purpose

Garante que todo elemento clicável da interface dê retorno visual e de cursor consistente, para que o usuário saiba o que é interativo, o que está sendo acionado e o que está indisponível.

## Requirements

### Requirement: Cursor de elemento clicável
Todo elemento clicável habilitado (botões, links, linhas de tabela clicáveis, abas, etiquetas de filtro removíveis, cabeçalho recolhível do menu lateral, botão de fechar modal e botão de perfil) SHALL exibir o cursor de mão ao receber o ponteiro do mouse.

#### Scenario: Ponteiro sobre botão habilitado
- **WHEN** o usuário posiciona o mouse sobre um botão habilitado
- **THEN** o cursor exibido é o de mão (pointer)

#### Scenario: Ponteiro sobre linha clicável de tabela
- **WHEN** o usuário posiciona o mouse sobre uma linha de tabela que abre um detalhe ao ser clicada
- **THEN** o cursor exibido é o de mão

#### Scenario: Ponteiro sobre linha não clicável
- **WHEN** o usuário posiciona o mouse sobre uma linha de tabela sem ação de clique
- **THEN** o cursor permanece o padrão e a linha não sugere que é clicável

### Requirement: Estado de hover
Todo elemento clicável habilitado SHALL mudar de aparência (cor de fundo, cor do texto, borda ou sombra) enquanto o ponteiro do mouse estiver sobre ele, voltando à aparência original quando o ponteiro sair.

#### Scenario: Hover em botão
- **WHEN** o usuário passa o mouse sobre um botão habilitado
- **THEN** o botão muda de tonalidade enquanto o ponteiro estiver sobre ele

#### Scenario: Saída do ponteiro
- **WHEN** o ponteiro sai do elemento
- **THEN** o elemento volta à aparência original

### Requirement: Estado de clique
Todo elemento clicável habilitado SHALL exibir um retorno visual de "pressionado" enquanto o botão do mouse (ou o toque) estiver acionado sobre ele.

#### Scenario: Pressionar botão
- **WHEN** o usuário mantém o clique sobre um botão habilitado
- **THEN** o botão exibe um estado pressionado distinto do estado de hover

### Requirement: Foco visível por teclado
Todo elemento clicável SHALL exibir um contorno de foco visível quando receber foco pela navegação por teclado (Tab), sem exibir esse contorno quando o foco vier de um clique do mouse.

#### Scenario: Navegação por Tab
- **WHEN** o usuário navega com a tecla Tab até um botão, link, aba ou linha clicável
- **THEN** o elemento exibe um contorno de foco na cor primária do tema

#### Scenario: Clique com mouse
- **WHEN** o usuário clica com o mouse em um botão
- **THEN** o contorno de foco por teclado não é exibido

### Requirement: Estado desabilitado
Elementos clicáveis desabilitados SHALL exibir o cursor de "não permitido", aparência atenuada, e não SHALL reagir com hover, estado pressionado nem disparar a ação.

#### Scenario: Ponteiro sobre botão desabilitado
- **WHEN** o usuário posiciona o mouse sobre um botão desabilitado
- **THEN** o cursor exibido é o de "não permitido" e o botão não muda de aparência

#### Scenario: Clique em botão desabilitado
- **WHEN** o usuário clica em um botão desabilitado ou em carregamento
- **THEN** nenhuma ação é disparada
