# aghu-barcode-parsing Specification

## Purpose

Define a decomposição determinística de códigos de barras de 10 dígitos impressos nas etiquetas de frascos do AGHU em código da solicitação e número da amostra, bem como a resolução do grupo de exame correspondente.

## ADDED Requirements

### Requirement: Decomposição do código de barras de 10 dígitos do AGHU
O sistema SHALL decompor entradas numéricas contínuas de exatos 10 dígitos em `codigoSolicitacao` (primeiros 7 dígitos) e `numeroAmostra` (últimos 3 dígitos), preservando a compatibilidade com os formatos `<solicitação>`, `<solicitação>-<amostra>` e `<solicitação>:<tipo>`.

#### Scenario: Código contínuo de 10 dígitos
- **WHEN** o usuário envia o código `"7712340001"`
- **THEN** o parser extrai `codigoSolicitacao = "7712340"` e `numeroAmostra = "001"`

#### Scenario: Código separado por hífen
- **WHEN** o usuário envia o código `"7712340-3"`
- **THEN** o parser extrai `codigoSolicitacao = "7712340"` e `numeroAmostra = "3"`

#### Scenario: Código puro da solicitação ou com tipo
- **WHEN** o usuário envia `"7712340"` ou `"7712340:HP"`
- **THEN** o parser extrai `codigoSolicitacao = "7712340"` e `numeroAmostra = null`

#### Scenario: Entrada numérica com tamanho diferente de 10 dígitos
- **WHEN** o usuário envia `"7712340"` (7 dígitos) ou `"77123400012"` (11 dígitos)
- **THEN** o parser não aplica fatiamento posicional de 10 dígitos e trata a entrada como código integral

### Requirement: Resolução tolerante a zeros à esquerda no número da amostra
Ao localizar a amostra bipada entre os grupos de exame da solicitação, o sistema SHALL comparar números de amostra numéricos ignorando zeros à esquerda, preservando a correspondência exata quando houver caracteres não numéricos.

#### Scenario: Correspondência entre 3 dígitos e número sem zeros à esquerda
- **WHEN** a etiqueta bipada informa `numeroAmostra = "001"` e o grupo da solicitação contém amostra com `numeroAmostra = "1"`
- **THEN** o sistema reconhece a amostra `"1"` como correspondente à amostra bipada

#### Scenario: Amostra inexistente na solicitação
- **WHEN** a etiqueta bipada informa `numeroAmostra = "099"` e nenhum grupo da solicitação possui amostra equivalente
- **THEN** o sistema identifica a solicitação normalmente e retorna `grupoSelecionadoId = null` e `examesFiltrados = []`

### Requirement: Metadados da amostra bipada na resposta de leitura
Quando `numeroAmostra` for extraído da leitura, a resposta da API de leitura da solicitação SHALL informar `amostraBipada` (número normalizado da amostra), `grupoSelecionadoId` (ID do grupo que contém a amostra, se pendente) e `examesFiltrados` (lista com o grupo correspondente, ou vazia se não encontrado/não pendente).

#### Scenario: Amostra bipada pertence a grupo pendente
- **WHEN** a solicitação `7712340` tem os grupos `CO` (amostra `1`) e `HP` (amostra `2`) pendentes e o usuário bipa `"7712340002"`
- **THEN** a resposta `PENDENTE` inclui `amostraBipada = "002"`, `grupoSelecionadoId = "7712340:HP"` e `examesFiltrados` contendo apenas `"7712340:HP"`
