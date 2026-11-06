# code-scan Specification

## Purpose

Permite que o usuário leia, com o leitor de código de barras, ou digite um código em qualquer tela e seja levado direto à recepção da solicitação ou ao caso correspondente, sem precisar navegar pelos menus.

## Requirements

### Requirement: Campo global de leitura
O cabeçalho SHALL exibir, para usuários autenticados, o campo "Ler código ou buscar caso (F2)". A tecla F2 SHALL colocar o foco nesse campo a partir de qualquer tela. A leitura é disparada pelo Enter, ignorando espaços nas pontas e diferenças entre maiúsculas e minúsculas.

#### Scenario: Atalho F2
- **WHEN** o usuário pressiona F2 em qualquer tela autenticada
- **THEN** o campo global de leitura recebe o foco

### Requirement: Leitura de solicitação AGHU pendente
A leitura do número de uma solicitação aguardando recebimento SHALL abrir a Recepção de amostras já no passo "Conferir", com a solicitação carregada.

#### Scenario: Solicitação pendente em outra tela
- **WHEN** o usuário está na Consulta de casos e lê o número de uma solicitação pendente
- **THEN** a Recepção de amostras é aberta no passo "Conferir" com essa solicitação

### Requirement: Leitura de caso, item ou IHQ
O sistema SHALL abrir o detalhe do caso nestes casos:
- leitura do número interno de um caso, do nº AGHU de uma solicitação já recebida ou do código de um item de material: abre o caso correspondente;
- leitura do código de uma IHQ: abre o caso de origem.

Quando for um item de material, o detalhe SHALL abrir na aba Materiais, com o item destacado.

#### Scenario: Leitura do código de uma amostra
- **WHEN** o usuário lê o código da segunda amostra de um caso
- **THEN** o detalhe do caso abre na aba Materiais, com essa amostra destacada

#### Scenario: Leitura do código de IHQ
- **WHEN** o usuário lê o código de uma IHQ vinculada ao caso HP-0003/26
- **THEN** o detalhe de HP-0003/26 abre na aba IHQ

### Requirement: Código não encontrado
Quando o código não corresponder a nenhuma solicitação, caso, item ou IHQ, o sistema SHALL informar "Nenhum registro encontrado para o código <código>. Confira a etiqueta ou digite o número.", manter o texto no campo e não SHALL mudar de tela.

#### Scenario: Código inexistente
- **WHEN** o usuário lê um código que não existe
- **THEN** a mensagem de não encontrado é exibida e a tela atual é mantida

### Requirement: Solicitação devolvida
A leitura do número de uma solicitação devolvida SHALL informar que ela foi devolvida, com a data e o tipo da não conformidade, sem abrir a recepção.

#### Scenario: Leitura de solicitação devolvida
- **WHEN** o usuário lê o número de uma solicitação devolvida
- **THEN** o sistema informa a devolução e permanece na tela atual
