## ADDED Requirements

### Requirement: Campos de seleção com busca
Os campos de seleção das telas do fluxo de anatomia patológica SHALL abrir uma lista com campo de busca por digitação, que filtra as opções sem diferenciar maiúsculas, minúsculas e acentos. As opções SHALL exibir cursor de mão e destaque de cor ao passar o mouse ou navegar pelo teclado, com a opção selecionada em negrito e marcada. A lista SHALL ser operável por teclado (setas, Enter, Esc) e fechar ao perder o foco.

#### Scenario: Busca por digitação
- **WHEN** o usuário abre o campo "Procedimento" e digita "agulha"
- **THEN** a lista mostra só "Biópsia por agulha grossa" e "Punção aspirativa por agulha fina (PAAF)"

#### Scenario: Digitar com o campo fechado
- **WHEN** o campo de seleção está em foco, fechado, e o usuário digita uma letra
- **THEN** a lista abre já filtrando por essa letra

#### Scenario: Hover em opção
- **WHEN** o usuário passa o mouse sobre uma opção
- **THEN** a opção exibe cursor de mão e fundo destacado na cor primária suave do tema

#### Scenario: Nenhuma opção encontrada
- **WHEN** o texto digitado não corresponde a nenhuma opção
- **THEN** a lista exibe "Nenhuma opção encontrada."
