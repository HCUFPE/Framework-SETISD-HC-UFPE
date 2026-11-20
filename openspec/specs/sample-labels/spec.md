# sample-labels Specification

## Purpose

Gera as identificações impressas do caso: a etiqueta do frasco, que acompanha a amostra pelo setor, e a ficha de trabalho, que reúne os dados da solicitação para o acompanhamento físico. Em nenhuma das duas o código de barras carrega dados pessoais.

## Requirements

### Requirement: Pré-visualização antes de imprimir
A impressão de etiquetas e da ficha SHALL abrir uma pré-visualização em escala real, com as ações "Imprimir" e "Fechar". "Imprimir" SHALL enviar à impressora apenas o conteúdo pré-visualizado, sem menu, cabeçalho ou botões da aplicação.

#### Scenario: Impressão
- **WHEN** o usuário clica em "Imprimir" na pré-visualização
- **THEN** a janela de impressão do navegador é aberta só com as etiquetas ou a ficha

### Requirement: Código de barras opaco
O código de barras da etiqueta e da ficha SHALL codificar apenas o código do item ou o número interno do caso, nunca nome, prontuário ou outro dado pessoal. A leitura desse código pelo campo global de leitura SHALL abrir o caso correspondente.

#### Scenario: Leitura da etiqueta impressa
- **WHEN** o código de barras de uma etiqueta é lido no campo global de leitura
- **THEN** o detalhe do caso correspondente é aberto

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

#### Scenario: Seleção parcial
- **WHEN** o usuário seleciona somente uma amostra de um caso com várias amostras
- **THEN** somente a etiqueta dessa amostra é impressa localmente pelo navegador, sem chamada de API, histórico ou auditoria

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

### Requirement: Acompanhamento físico na ficha
Depois dos blocos de dados, a ficha de trabalho SHALL ter o quadro "Acompanhamento físico por setor", com uma linha por etapa do fluxo do tipo do caso e espaços em branco para data e hora, responsável e visto. O rodapé SHALL trazer a data e hora de emissão.

#### Scenario: Ficha de caso CO
- **WHEN** o usuário imprime a ficha de um caso de congelação
- **THEN** o quadro de acompanhamento lista as etapas Recepção, Congelação, Microscopia, Aprovação e Arquivo, e o rodapé mostra a data e hora de emissão

### Requirement: Seleção das etiquetas a imprimir
Ao imprimir as etiquetas de um caso com mais de uma amostra, a pré-visualização SHALL listar as amostras com número e descrição, todas marcadas por padrão, e permitir marcar só algumas, com a ação "Todas" para remarcar todas (sem ação "Nenhuma"). SHALL mostrar e imprimir apenas as etiquetas marcadas, e "Imprimir" SHALL ficar desabilitado com nenhuma marcada. Com uma única amostra, a seleção não aparece.

#### Scenario: Imprimir todas
- **WHEN** o usuário abre a impressão de etiquetas de um caso com 3 amostras e clica em "Imprimir" sem mudar a seleção
- **THEN** as 3 etiquetas são impressas

#### Scenario: Imprimir uma amostra específica
- **WHEN** o usuário desmarca as amostras 1 e 3 e clica em "Imprimir"
- **THEN** só a etiqueta da amostra 2 é pré-visualizada e impressa localmente pelo navegador, sem criar registro no backend

#### Scenario: Nenhuma marcada
- **WHEN** o usuário desmarca todas as amostras
- **THEN** a pré-visualização fica vazia e "Imprimir" fica desabilitado

#### Scenario: Caso com uma amostra
- **WHEN** o usuário imprime as etiquetas de um caso com uma amostra
- **THEN** a pré-visualização mostra a etiqueta sem a lista de seleção

### Requirement: Impressão local
A pré-visualização, impressão e reimpressão SHALL ocorrer apenas no navegador usando `window.print()`, sem chamada de API, registro no histórico do caso ou `AuditLog`.

#### Scenario: Reimpressão local
- **WHEN** o usuário imprime a ficha de trabalho pela segunda vez
- **THEN** o navegador imprime a ficha novamente sem criar registro no backend

#### Scenario: Impressão parcial local de etiquetas
- **WHEN** o usuário imprime só as etiquetas das amostras 2 e 4
- **THEN** o navegador imprime apenas essas etiquetas sem criar registro no backend
