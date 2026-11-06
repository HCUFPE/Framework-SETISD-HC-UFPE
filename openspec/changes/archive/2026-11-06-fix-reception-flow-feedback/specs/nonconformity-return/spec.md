## MODIFIED Requirements

### Requirement: Dados da não conformidade
O primeiro passo do registro SHALL exigir o tipo, escolhido no catálogo padronizado, e o detalhamento. A unidade de origem SHALL ser exigida quando não houver solicitação nem caso. O registro não SHALL pedir nº CMCE. O catálogo é: Sem etiqueta do AGHU; Identificação divergente; Quantidade divergente; Material inadequado/insuficiente; Recipiente danificado/vazamento; Ausência de fixador/fixação inadequada; Requisição incompleta; Outro.

#### Scenario: Detalhamento ausente
- **WHEN** o usuário tenta avançar sem preencher o detalhamento
- **THEN** o sistema não avança e indica o campo como obrigatório

#### Scenario: Sem campo CMCE
- **WHEN** o usuário abre o registro de não conformidade
- **THEN** não há campo de nº CMCE no formulário

### Requirement: Tela de rejeições e devoluções
A tela "Rejeições e devoluções" SHALL listar todas as devoluções, da mais recente para a mais antiga, com:
- data e hora;
- natureza ("Rejeição na recepção" quando não há caso, "Devolução de caso" quando há);
- tipo e detalhamento;
- origem e etapa;
- caso ou nº da solicitação;
- quem devolveu;
- se houve nova amostra;
- a situação da devolução, como selo somente leitura;
- a ação "Alterar situação".

#### Scenario: Rejeição na recepção
- **WHEN** a devolução foi registrada sem caso para a solicitação 7712045
- **THEN** a linha aparece como "Rejeição na recepção" e mostra "AGHU 7712045" no lugar do caso

#### Scenario: Abrir caso devolvido
- **WHEN** o usuário clica no número do caso em uma "Devolução de caso"
- **THEN** o detalhe desse caso é aberto

#### Scenario: Situação não editável na tabela
- **WHEN** o usuário vê a lista de devoluções
- **THEN** a coluna "Situação" mostra a situação atual como selo, sem campo de edição

### Requirement: Atualização da situação da devolução
O usuário SHALL poder alterar a situação de uma devolução pela ação "Alterar situação", que abre um modal com a identificação da devolução e somente o campo de situação. Salvar sem mudar a situação não SHALL registrar alteração. Cada alteração registra auditoria com os valores anterior e novo, o usuário e a data e hora. Quando a situação passa a "Nova amostra recebida" ou "Encerrada", a não conformidade vinculada passa a "Resolvida".

#### Scenario: Nova amostra recebida
- **WHEN** o usuário abre "Alterar situação", escolhe "Nova amostra recebida" no lugar de "Aguardando nova amostra" e salva
- **THEN** o modal fecha, a nova situação aparece no selo da linha, o sistema confirma a atualização e a auditoria registra os valores anterior e novo

#### Scenario: Cancelar a alteração
- **WHEN** o usuário abre "Alterar situação", muda a opção e fecha o modal sem salvar
- **THEN** a situação da devolução permanece a anterior

## ADDED Requirements

### Requirement: Devolução gerada pela não conformidade
Toda não conformidade SHALL gerar uma devolução. O segundo passo do registro SHALL exigir apenas se foi solicitada nova amostra (Sim ou Não). Quem devolveu é o usuário autenticado e não é editável. O registro não SHALL pedir quem recebeu o material na unidade de origem.

#### Scenario: Registro completo
- **WHEN** o usuário preenche os dois passos e clica em "Registrar devolução"
- **THEN** a não conformidade e a devolução ficam registradas juntas e o sistema confirma que o material saiu das filas ativas

#### Scenario: Nova amostra não informada
- **WHEN** o usuário tenta registrar a devolução sem responder se foi solicitada nova amostra
- **THEN** o registro é recusado e o campo é indicado como obrigatório

#### Scenario: Sem campo de quem recebeu
- **WHEN** o usuário chega ao segundo passo do registro
- **THEN** não há campo para informar quem recebeu o material na unidade de origem

## REMOVED Requirements

### Requirement: Devolução obrigatória
**Reason**: Substituído por "Devolução gerada pela não conformidade", que retira a exigência de informar quem recebeu o material na unidade de origem.
**Migration**: Não há dados reais a migrar (dados mockados). O campo sai dos registros, das exibições e dos dados de exemplo.
