## ADDED Requirements

### Requirement: Seleção das etiquetas a imprimir
Ao imprimir as etiquetas de um caso com mais de uma amostra, a pré-visualização SHALL listar as amostras com número e descrição, todas marcadas por padrão, e permitir marcar só algumas, com a ação "Todas" para remarcar todas (sem ação "Nenhuma"). SHALL mostrar e imprimir apenas as etiquetas marcadas, e "Imprimir" SHALL ficar desabilitado com nenhuma marcada. Com uma única amostra, a seleção não aparece.

#### Scenario: Imprimir todas
- **WHEN** o usuário abre a impressão de etiquetas de um caso com 3 amostras e clica em "Imprimir" sem mudar a seleção
- **THEN** as 3 etiquetas são impressas

#### Scenario: Imprimir uma amostra específica
- **WHEN** o usuário desmarca as amostras 1 e 3 e clica em "Imprimir"
- **THEN** só a etiqueta da amostra 2 é pré-visualizada e impressa, e o histórico registra a impressão da amostra 2

#### Scenario: Nenhuma marcada
- **WHEN** o usuário desmarca todas as amostras
- **THEN** a pré-visualização fica vazia e "Imprimir" fica desabilitado

#### Scenario: Caso com uma amostra
- **WHEN** o usuário imprime as etiquetas de um caso com uma amostra
- **THEN** a pré-visualização mostra a etiqueta sem a lista de seleção

## MODIFIED Requirements

### Requirement: Registro da impressão
Cada impressão SHALL registrar um evento no histórico do caso ("Etiquetas impressas" ou "Ficha de trabalho impressa"), com o usuário e a data e hora. Para etiquetas, o evento SHALL informar quais amostras foram impressas.

#### Scenario: Reimpressão
- **WHEN** o usuário imprime a ficha de trabalho pela segunda vez
- **THEN** o histórico passa a ter dois eventos "Ficha de trabalho impressa"

#### Scenario: Impressão parcial de etiquetas
- **WHEN** o usuário imprime só as etiquetas das amostras 2 e 4
- **THEN** o evento "Etiquetas impressas" informa as amostras 2 e 4

### Requirement: Etiqueta do frasco
A etiqueta do frasco SHALL ter 50 × 25 mm, uma por amostra do caso, e exibir nesta ordem:
- o número interno em destaque, o número da amostra e o código de barras;
- o nome completo do paciente, sem abreviação nem truncamento, quebrando em até duas linhas com redução da fonte quando necessário;
- a data de recebimento no SAP;
- o nº da solicitação AGHU;
- o prontuário;
- o exame.

#### Scenario: Caso com duas amostras
- **WHEN** o usuário imprime as etiquetas de um caso com as amostras 2 e 3
- **THEN** são geradas duas etiquetas, cada uma com o código do respectivo item e a indicação "Amostra 2" ou "Amostra 3", e as demais informações iguais

#### Scenario: Nome completo
- **WHEN** o paciente se chama "MARIA DAS GRAÇAS DE ALBUQUERQUE CAVALCANTI DOS SANTOS"
- **THEN** a etiqueta exibe o nome inteiro, sem reticências

### Requirement: Ficha de trabalho
A ficha de trabalho SHALL ser um documento A4, com o cabeçalho institucional e o tipo de exame, organizado em blocos nesta ordem:
1. Identificação: nº interno em destaque, código de barras e data de recebimento no SAP.
2. Solicitação: nº da solicitação, data da solicitação e exame (nome e sigla).
3. Paciente e origem: nome completo do paciente, prontuário, origem e unidade solicitante.
4. Solicitante: especialidade.
5. Material: lista das amostras, cada uma com número e descrição do material, e informações clínicas.

#### Scenario: Caso urgente
- **WHEN** o caso é urgente
- **THEN** a ficha exibe o selo URGENTE junto ao número interno, sem motivo

#### Scenario: Ficha com várias amostras
- **WHEN** o caso tem as amostras 1 "MAMA DIREITA 10H" e 2 "MAMA DIREITA 2H"
- **THEN** o bloco Material lista as duas amostras separadamente, com número e descrição

#### Scenario: Nome completo na ficha
- **WHEN** a ficha é impressa
- **THEN** o bloco Paciente e origem exibe o nome completo do paciente
