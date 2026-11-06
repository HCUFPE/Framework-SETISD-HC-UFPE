# nonconformity-return Specification

## Purpose

Registra as não conformidades encontradas nas amostras, sempre com a devolução do material à unidade de origem, e permite acompanhar as rejeições na recepção e as devoluções de casos até a resolução.

## Requirements

### Requirement: Pontos de registro da não conformidade
O sistema SHALL permitir registrar uma não conformidade em três pontos:
- no passo 1 da recepção, para material sem etiqueta do AGHU;
- no passo "Conferir", para uma solicitação carregada;
- no detalhe de um caso ativo.

#### Scenario: Material sem etiqueta
- **WHEN** o usuário clica em "Material sem etiqueta do AGHU — registrar não conformidade" no passo 1
- **THEN** abre o registro com o tipo "Sem etiqueta do AGHU" já selecionado e exige a unidade de origem

#### Scenario: Caso ativo
- **WHEN** o usuário clica em "Não conformidade" no detalhe de um caso com status "Em processamento técnico"
- **THEN** abre o registro com o caso e a etapa atual já identificados

### Requirement: Contexto automático do registro
O registro SHALL exibir e gravar sem digitação o setor (Recepção), a etapa em que a não conformidade foi identificada, o caso (quando existir), a data e hora e o usuário autenticado. Quando houver solicitação, SHALL exibir também nº da solicitação, exame, origem, médico e especialidade.

#### Scenario: Registro a partir da conferência
- **WHEN** o registro é aberto a partir do passo "Conferir"
- **THEN** a etapa aparece como "Recepção (conferência)" e os dados da solicitação são exibidos sem edição

### Requirement: Dados da não conformidade
O primeiro passo do registro SHALL exigir o tipo, escolhido no catálogo padronizado, e o detalhamento. O nº CMCE é opcional. A unidade de origem SHALL ser exigida quando não houver solicitação nem caso. O catálogo é: Sem etiqueta do AGHU; Identificação divergente; Quantidade divergente; Material inadequado/insuficiente; Recipiente danificado/vazamento; Ausência de fixador/fixação inadequada; Requisição incompleta; Outro.

#### Scenario: Detalhamento ausente
- **WHEN** o usuário tenta avançar sem preencher o detalhamento
- **THEN** o sistema não avança e indica o campo como obrigatório

### Requirement: Devolução obrigatória
Toda não conformidade SHALL gerar uma devolução. O segundo passo SHALL exigir quem recebeu o material na unidade de origem e se foi solicitada nova amostra (Sim ou Não). Quem devolveu é o usuário autenticado e não é editável.

#### Scenario: Registro completo
- **WHEN** o usuário preenche os dois passos e clica em "Registrar devolução"
- **THEN** a não conformidade e a devolução ficam registradas juntas e o sistema confirma que o material saiu das filas ativas

#### Scenario: Quem recebeu ausente
- **WHEN** o usuário tenta registrar a devolução sem informar quem recebeu na origem
- **THEN** o registro é recusado e o campo é indicado como obrigatório

### Requirement: Efeito da devolução na recepção
Uma não conformidade registrada na recepção antes da criação do caso SHALL marcar a solicitação do AGHU (quando houver) como devolvida, retirá-la da lista de pendentes, não SHALL criar caso e SHALL fazer a recepção voltar ao passo 1.

#### Scenario: Devolução na conferência
- **WHEN** o usuário registra a devolução de uma solicitação a partir do passo "Conferir"
- **THEN** a solicitação sai da lista de pendentes, nenhum caso é criado e a tela volta ao passo 1

### Requirement: Efeito da devolução no caso
Uma não conformidade registrada em um caso SHALL mudar o status do caso para "Devolvido", registrar no histórico a não conformidade e a devolução e tornar o caso somente leitura, preservando todo o histórico e os materiais.

#### Scenario: Caso devolvido
- **WHEN** a devolução de um caso é registrada
- **THEN** o caso passa a "Devolvido", aparece com a faixa de bloqueio e mantém as abas e o histórico anteriores

### Requirement: Situação da devolução
A devolução SHALL ter uma das situações "Aguardando nova amostra", "Nova amostra recebida" ou "Encerrada". A situação inicial é "Aguardando nova amostra" quando foi solicitada nova amostra e "Encerrada" quando não foi.

#### Scenario: Sem nova amostra
- **WHEN** a devolução é registrada com "Nova amostra solicitada?" = Não
- **THEN** a situação inicial é "Encerrada"

### Requirement: Tela de rejeições e devoluções
A tela "Rejeições e devoluções" SHALL listar todas as devoluções, da mais recente para a mais antiga, com:
- data e hora;
- natureza ("Rejeição na recepção" quando não há caso, "Devolução de caso" quando há);
- tipo e detalhamento;
- origem e etapa;
- caso ou nº da solicitação;
- quem devolveu e quem recebeu;
- se houve nova amostra;
- a situação da devolução.

#### Scenario: Rejeição na recepção
- **WHEN** a devolução foi registrada sem caso para a solicitação 7712045
- **THEN** a linha aparece como "Rejeição na recepção" e mostra "AGHU 7712045" no lugar do caso

#### Scenario: Abrir caso devolvido
- **WHEN** o usuário clica no número do caso em uma "Devolução de caso"
- **THEN** o detalhe desse caso é aberto

### Requirement: Filtros de rejeições e devoluções
A tela SHALL filtrar por período (qualquer data, últimos 7 dias e últimos 30 dias), natureza, tipo de não conformidade, origem e etapa, exibir a quantidade de registros resultantes e paginar a lista em 10 por página.

#### Scenario: Filtro por natureza
- **WHEN** o usuário filtra por "Rejeição na recepção"
- **THEN** apenas as devoluções sem caso são exibidas, e o total reflete o filtro

#### Scenario: Sem resultados
- **WHEN** nenhum registro atende aos filtros
- **THEN** a tela exibe "Nenhuma devolução para os filtros selecionados."

### Requirement: Atualização da situação da devolução
O usuário SHALL poder alterar a situação de uma devolução na própria lista. Cada alteração registra auditoria com os valores anterior e novo, o usuário e a data e hora. Quando a situação passa a "Nova amostra recebida" ou "Encerrada", a não conformidade vinculada passa a "Resolvida".

#### Scenario: Nova amostra recebida
- **WHEN** o usuário altera a situação de "Aguardando nova amostra" para "Nova amostra recebida"
- **THEN** a nova situação é exibida, o sistema confirma a atualização e a auditoria registra os valores anterior e novo
