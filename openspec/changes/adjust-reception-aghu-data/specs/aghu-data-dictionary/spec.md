## Purpose

Define os domínios, formatos e regras de qualidade dos dados vindos do AGHU, tendo `data/dicionario_dados.md` como referência única, para que todo campo de status ou de opções predefinidas no SAP use exatamente os valores do AGHU.

## ADDED Requirements

### Requirement: Dicionário de dados como referência
O tipo, o formato e as opções de todo dado vindo do AGHU SHALL seguir `data/dicionario_dados.md`. Um campo de status ou com opções predefinidas no dicionário SHALL oferecer e exibir apenas os valores listados nele, sem valores inventados pelo SAP. Os dados de demonstração SHALL usar apenas valores existentes no dicionário.

#### Scenario: Dados de demonstração
- **WHEN** a recepção é aberta com os dados de demonstração
- **THEN** todo status, origem, exame e unidade exibido é um dos valores listados no dicionário

### Requirement: Status do item no AGHU
O status de cada amostra SHALL usar os 8 pares código/descrição do AGHU: LI LIBERADO, AC A COLETAR, EX EXECUTANDO, AE AREA EXECUTORA, CA CANCELADO, CO COLETADO, EC EM COLETA e PE PENDENTE. O status SHALL ser exibido por amostra, porque amostras da mesma solicitação podem ter status diferentes. Um código fora da lista SHALL ser exibido como recebido, com a indicação "status não catalogado".

#### Scenario: Amostras com status diferentes
- **WHEN** uma solicitação tem a amostra 1 com status LI e a amostra 2 com status AC
- **THEN** cada amostra exibe o próprio status, "LIBERADO" e "A COLETAR"

#### Scenario: Status desconhecido
- **WHEN** uma amostra chega com o código de status "XX"
- **THEN** o status é exibido como "XX" com a indicação "status não catalogado"

### Requirement: Origem do AGHU
A origem SHALL ter apenas os valores do AGHU, exibidos com o texto do AGHU: Ambulatório, Internação, Cirurgia e Paciente Externo. Uma origem vazia ou desconhecida SHALL ser exibida como "Não informada".

#### Scenario: Origem Cirurgia
- **WHEN** a solicitação vem com origem "Cirurgia"
- **THEN** a origem é exibida como "Cirurgia"

### Requirement: Exames do AGHU
O exame SHALL ser identificado pela sigla do AGHU, uma das 12 do dicionário (APECR, CCVM, HPDER, IMUHI, MBIOP, MPCIR, CITOP, CONGE, CITO, COUT2, COLUT, CPMAM), e exibido com o nome do AGHU. O tipo de exame do SAP SHALL ser sugerido pela sigla. Siglas fora da lista não são de Anatomia Patológica e SHALL ser ignoradas.

#### Scenario: Siglas com o mesmo nome
- **WHEN** duas solicitações têm as siglas MBIOP e MPCIR
- **THEN** as duas exibem o nome "ANATOMOPATOLÓGICO - MAMA" acompanhado da sigla, que as diferencia

### Requirement: Unidades do AGHU
Toda lista de unidades de origem SHALL oferecer as unidades do dicionário. Antes de exibir ou comparar uma unidade, SHALL remover caracteres invisíveis (como U+200B) e espaços nas pontas.

#### Scenario: Unidade com caractere invisível
- **WHEN** a unidade chega como "UAP: HISTOPATOLÓGICO" seguida de um zero-width space
- **THEN** ela é exibida e filtrada como "UAP: HISTOPATOLÓGICO"

### Requirement: Datas do AGHU
As datas de solicitação e de nascimento SHALL ser lidas no formato `dd/mm/aaaa` e exibidas só como data, sem hora, porque o AGHU não fornece hora.

#### Scenario: Data da solicitação
- **WHEN** a solicitação vem com data "22/04/2026"
- **THEN** a data é exibida como "22/04/2026", sem horário

### Requirement: Campos vazios do AGHU
Prontuário e especialidade vazios (Paciente Externo), informações clínicas vazias e descrição do material vazia (exame CITO) SHALL ser aceitos sem erro e exibidos como "Não informado". O SAP não SHALL exibir campos que não existem no AGHU, como sexo e médico solicitante.

#### Scenario: Paciente externo sem prontuário
- **WHEN** uma solicitação de origem "Paciente Externo" chega sem prontuário e sem especialidade
- **THEN** a recepção exibe "Não informado" nesses campos e permite o recebimento

#### Scenario: Campos inexistentes no AGHU
- **WHEN** o passo "Conferir" exibe os dados da solicitação
- **THEN** não há campos de sexo nem de médico solicitante

### Requirement: Nome do paciente
O nome do paciente SHALL ser exibido completo, como veio do AGHU, sem abreviação nem truncamento.

#### Scenario: Nome longo
- **WHEN** o nome do paciente tem 60 caracteres
- **THEN** o nome aparece inteiro, com quebra de linha se necessário
