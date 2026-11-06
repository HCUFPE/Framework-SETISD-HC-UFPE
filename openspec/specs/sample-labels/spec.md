# sample-labels Specification

## Purpose

Gera as identificações impressas do caso: a etiqueta do frasco, que acompanha a amostra pelo setor, e a ficha de trabalho, que reúne os dados da solicitação para o acompanhamento físico. Em nenhuma das duas o código de barras carrega dados pessoais.

## Requirements

### Requirement: Pré-visualização antes de imprimir
A impressão de etiquetas e da ficha SHALL abrir uma pré-visualização em escala real, com as ações "Imprimir" e "Fechar". "Imprimir" SHALL enviar à impressora apenas o conteúdo pré-visualizado, sem menu, cabeçalho ou botões da aplicação.

#### Scenario: Impressão
- **WHEN** o usuário clica em "Imprimir" na pré-visualização
- **THEN** a janela de impressão do navegador é aberta só com as etiquetas ou a ficha

### Requirement: Registro da impressão
Cada impressão SHALL registrar um evento no histórico do caso ("Etiquetas impressas" ou "Ficha de trabalho impressa"), com o usuário e a data e hora.

#### Scenario: Reimpressão
- **WHEN** o usuário imprime a ficha de trabalho pela segunda vez
- **THEN** o histórico passa a ter dois eventos "Ficha de trabalho impressa"

### Requirement: Código de barras opaco
O código de barras da etiqueta e da ficha SHALL codificar apenas o código do item ou o número interno do caso, nunca nome, prontuário ou outro dado pessoal. A leitura desse código pelo campo global de leitura SHALL abrir o caso correspondente.

#### Scenario: Leitura da etiqueta impressa
- **WHEN** o código de barras de uma etiqueta é lido no campo global de leitura
- **THEN** o detalhe do caso correspondente é aberto

### Requirement: Etiqueta do frasco
A etiqueta do frasco SHALL ter 50 × 25 mm, uma por amostra do caso, e exibir nesta ordem:
- o número interno em destaque e o código de barras;
- a data de recebimento no SAP;
- o nº da solicitação AGHU;
- o prontuário;
- o exame.

#### Scenario: Caso com duas amostras
- **WHEN** o usuário imprime as etiquetas de um caso com duas amostras
- **THEN** são geradas duas etiquetas, cada uma com o código do respectivo item, e as demais informações iguais

### Requirement: Ficha de trabalho
A ficha de trabalho SHALL ser um documento A4, com o cabeçalho institucional e o tipo de exame, organizado em blocos nesta ordem:
1. Identificação: nº interno em destaque, código de barras e data de recebimento no SAP.
2. Solicitação: nº da solicitação, data da solicitação e exame.
3. Paciente e origem: prontuário, origem e unidade solicitante.
4. Solicitante: especialidade e médico solicitante.
5. Material: descrição do material e informações clínicas.

#### Scenario: Caso urgente
- **WHEN** o caso é urgente
- **THEN** a ficha exibe o selo URGENTE junto ao número interno, com o motivo da urgência

### Requirement: Acompanhamento físico na ficha
Depois dos blocos de dados, a ficha de trabalho SHALL ter o quadro "Acompanhamento físico por setor", com uma linha por etapa do fluxo do tipo do caso e espaços em branco para data e hora, responsável e visto. O rodapé SHALL trazer a data e hora de emissão.

#### Scenario: Ficha de caso CO
- **WHEN** o usuário imprime a ficha de um caso de congelação
- **THEN** o quadro de acompanhamento lista as etapas Recepção, Congelação, Microscopia, Aprovação e Arquivo, e o rodapé mostra a data e hora de emissão
