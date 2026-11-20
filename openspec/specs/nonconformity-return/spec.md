# nonconformity-return Specification

## Purpose

Registra as não conformidades encontradas nas amostras, sempre com a devolução do material à unidade de origem, e permite acompanhar as rejeições na recepção e as devoluções de casos até a resolução.

## Requirements

### Requirement: Pontos de registro da não conformidade
O sistema SHALL permitir registrar uma não conformidade em três pontos, sempre no modal "Não conformidade e devolução":
- no passo 1 da recepção, para material sem etiqueta do AGHU;
- no passo "Conferir", para uma solicitação carregada;
- no detalhe de um caso ativo.

#### Scenario: Material sem etiqueta
- **WHEN** o usuário clica em "Registrar não conformidade de material sem etiqueta do AGHU" no passo 1
- **THEN** o modal abre com o tipo "Amostra sem solicitação ou sem etiqueta do AGHU" já selecionado e exige a unidade de origem

#### Scenario: Caso ativo
- **WHEN** o usuário clica em "Não conformidade" no detalhe de um caso com status "Em processamento técnico"
- **THEN** o modal abre com o caso e a etapa atual já identificados

### Requirement: Contexto automático do registro
O registro SHALL gravar sem digitação o setor (Recepção), a etapa em que a não conformidade foi identificada, o caso (quando existir), a data e hora e o usuário autenticado. Como o formulário fica na tela que já mostra a solicitação ou o caso, não SHALL repetir esses dados.

#### Scenario: Registro a partir da conferência
- **WHEN** a não conformidade é registrada a partir do passo "Conferir"
- **THEN** ela fica gravada com a etapa "Recepção (conferência)", a solicitação, o usuário e a data e hora, sem que o usuário digite esses dados

### Requirement: Dados da não conformidade
O registro SHALL exigir o tipo, escolhido em um campo de seleção com busca por digitação com o catálogo do formulário do setor, com as opções sem ponto final. A "Observação" SHALL ser opcional e ter altura de três linhas. A unidade de origem SHALL ser exigida quando não houver solicitação nem caso, escolhida entre as unidades do AGHU. O registro não SHALL pedir nº CMCE. O catálogo é, nesta ordem:
1. Amostra sem solicitação ou sem etiqueta do AGHU
2. Solicitação do exame não corresponde ao tipo de material enviado
3. Falta descrição do material no frasco
4. Etiqueta, identificação do paciente na peça ou requisição ilegível
5. Numeração dos frascos não corresponde à numeração do AGHU
6. Quantidade de frascos não confere com o descrito no AGHU
7. Lateralidade divergente ou não informada
8. Falta carimbo e/ou assinatura do médico responsável
9. Acondicionamento inadequado ou sem fixador
10. Várias solicitações do mesmo exame em códigos diferentes
11. Não descreveu as peças no campo informações clínicas
12. Formulário do Siscan não preenchido corretamente
13. Sem agendamento no sistema CMCE (SES-PE)
14. Outros

#### Scenario: Detalhamento ausente
- **WHEN** o usuário escolhe "Outros" e tenta registrar sem descrever a não conformidade
- **THEN** o sistema não registra e indica o campo de texto como obrigatório

#### Scenario: Tipo não escolhido
- **WHEN** o usuário tenta registrar sem escolher o tipo
- **THEN** o registro é recusado e o select é indicado como obrigatório

#### Scenario: Solução sugerida para solicitações duplicadas
- **WHEN** o usuário escolhe "Várias solicitações do mesmo exame em códigos diferentes"
- **THEN** o formulário exibe a solução "Unir os diversos materiais em única solicitação."

#### Scenario: Observação vazia
- **WHEN** o usuário escolhe um tipo diferente de "Outros", responde "Nova amostra solicitada?" e deixa a observação vazia
- **THEN** o registro é aceito

#### Scenario: Sem campo CMCE
- **WHEN** o usuário abre o registro de não conformidade
- **THEN** não há campo de nº CMCE no formulário

### Requirement: Efeito da devolução na recepção
Uma não conformidade registrada na recepção antes da criação do caso SHALL marcar como devolvidos os tipos de exame escolhidos da solicitação do AGHU (quando houver) e retirá-los da lista de pendentes. Ela não SHALL criar caso e SHALL fazer a recepção voltar ao passo 1.

#### Scenario: Devolução na conferência
- **WHEN** o usuário registra a devolução de uma solicitação a partir do passo "Conferir"
- **THEN** os tipos devolvidos saem da lista de pendentes, nenhum caso é criado e a tela volta ao passo 1

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
- tipo, com o texto informado quando for "Outros", e a observação;
- origem e etapa;
- caso ou nº da solicitação;
- quem devolveu;
- se houve nova amostra;
- a situação da devolução, como selo somente leitura;
- a ação "Alterar situação".

#### Scenario: Rejeição na recepção
- **WHEN** a devolução foi registrada sem caso para a solicitação 7712045
- **THEN** a linha aparece como "Rejeição na recepção" e mostra "AGHU 7712045" no lugar do caso

#### Scenario: Tipo Outros
- **WHEN** a devolução foi registrada com o tipo "Outros" e o texto "Frasco sem tampa"
- **THEN** a linha mostra "Outros: Frasco sem tampa"

#### Scenario: Abrir caso devolvido
- **WHEN** o usuário clica no número do caso em uma "Devolução de caso"
- **THEN** o detalhe desse caso é aberto

#### Scenario: Situação não editável na tabela
- **WHEN** o usuário vê a lista de devoluções
- **THEN** a coluna "Situação" mostra a situação atual como selo, sem campo de edição

### Requirement: Filtros de rejeições e devoluções
A tela SHALL filtrar por período (qualquer data, últimos 7 dias e últimos 30 dias), natureza, tipo de não conformidade (o catálogo de 14 tipos), origem e etapa. Ela SHALL exibir a quantidade de registros resultantes e paginar a lista em 10 por página.

#### Scenario: Filtro por natureza
- **WHEN** o usuário filtra por "Rejeição na recepção"
- **THEN** apenas as devoluções sem caso são exibidas, e o total reflete o filtro

#### Scenario: Filtro por tipo
- **WHEN** o usuário abre o filtro de tipo de não conformidade
- **THEN** as opções são os 14 tipos do catálogo, na ordem do formulário do setor

#### Scenario: Sem resultados
- **WHEN** nenhum registro atende aos filtros
- **THEN** a tela exibe "Nenhuma devolução para os filtros selecionados."

### Requirement: Atualização da situação da devolução
O usuário SHALL poder alterar a situação de uma devolução pela ação "Alterar situação", que abre um modal com a identificação da devolução e somente o campo de situação. Salvar sem mudar a situação não SHALL registrar alteração. Cada alteração registra auditoria com os valores anterior e novo, o usuário e a data e hora. Quando a situação passa a "Nova amostra recebida" ou "Encerrada", a não conformidade vinculada passa a "Resolvida".

#### Scenario: Nova amostra recebida
- **WHEN** o usuário abre "Alterar situação", escolhe "Nova amostra recebida" no lugar de "Aguardando nova amostra" e salva
- **THEN** o modal fecha, a nova situação aparece no selo da linha, o sistema confirma a atualização e a auditoria registra os valores anterior e novo

#### Scenario: Cancelar a alteração
- **WHEN** o usuário abre "Alterar situação", muda a opção e fecha o modal sem salvar
- **THEN** a situação da devolução permanece a anterior

### Requirement: Devolução gerada pela não conformidade
Toda não conformidade SHALL gerar uma devolução. O registro SHALL exigir "Nova amostra solicitada?" (Sim ou Não), sem valor pré-selecionado. Quem devolveu é o usuário autenticado e não é editável. O registro não SHALL pedir quem recebeu o material na unidade de origem.

#### Scenario: Registro completo
- **WHEN** o usuário escolhe o tipo, responde "Nova amostra solicitada?" e clica em "Registrar devolução"
- **THEN** a não conformidade e a devolução ficam registradas juntas e o sistema confirma que o material saiu das filas ativas

#### Scenario: Nova amostra não informada
- **WHEN** o usuário tenta registrar a devolução sem responder se foi solicitada nova amostra
- **THEN** o registro é recusado e o campo é indicado como obrigatório

#### Scenario: Sem valor pré-selecionado
- **WHEN** o formulário de não conformidade é aberto
- **THEN** nem "Sim" nem "Não" está marcado em "Nova amostra solicitada?"

#### Scenario: Sem campo de quem recebeu
- **WHEN** o usuário preenche o formulário de não conformidade
- **THEN** não há campo para informar quem recebeu o material na unidade de origem

### Requirement: Autorização de registro e atualização existentes

O registro de não conformidade/devolução e a atualização de situação SHALL exigir permissões explícitas do catálogo vigente. O backend SHALL aplicar as verificações tanto na criação quanto na atualização.

#### Scenario: Atualização direta sem permissão

- **WHEN** usuário sem permissão chama diretamente a operação de atualização da situação
- **THEN** o backend responde 403 e não altera a situação nem registra mutação

#### Scenario: Atualização por Recepção ou Administração

- **WHEN** Recepcionista SAP ou Coordenação/Administrador atualiza diretamente a situação de uma devolução
- **THEN** o backend autoriza a operação, persiste a situação e registra autoria autenticada e auditoria
- **AND** outros perfis continuam sujeitos à negação por padrão

### Requirement: Registro da não conformidade em modal
Nos três pontos de registro, o botão de não conformidade SHALL abrir o modal "Não conformidade e devolução", com o contexto (etapa, usuário e aviso de devolução) no topo, os campos do registro no corpo e as ações "Cancelar" e "Registrar devolução" no rodapé. "Cancelar", o botão de fechar e a tecla Esc fecham o modal sem registrar nada. Clicar fora do modal não o fecha. A cada abertura o formulário começa vazio. Ao registrar, o modal fecha.

#### Scenario: Abrir na conferência
- **WHEN** o usuário clica em "Registrar não conformidade" no passo "Conferir"
- **THEN** o modal "Não conformidade e devolução" é aberto, com o campo do tipo em foco

#### Scenario: Observação sem redimensionamento
- **WHEN** o formulário de não conformidade é exibido
- **THEN** o campo "Observação" não oferece o controle de redimensionar a caixa de texto

#### Scenario: Cancelar o registro
- **WHEN** o usuário escolhe um tipo e clica em "Cancelar"
- **THEN** o modal fecha, nada é registrado e a conferência continua como estava

#### Scenario: Reabrir o modal
- **WHEN** o usuário cancela o registro e abre o modal de novo
- **THEN** o formulário aparece vazio

#### Scenario: Todos os erros de uma vez
- **WHEN** o usuário clica em "Registrar devolução" no registro de material sem etiqueta sem preencher nada
- **THEN** o modal indica de uma vez a unidade de origem e "Nova amostra solicitada?" como obrigatórios

### Requirement: Opção "Outros"
Quando o tipo escolhido for "Outros", o sistema SHALL exibir um campo de texto obrigatório para descrever a não conformidade. Para os demais tipos, o campo não SHALL aparecer.

#### Scenario: Outros sem descrição
- **WHEN** o usuário escolhe "Outros" e tenta registrar com o texto vazio
- **THEN** o registro é recusado e o campo é indicado como obrigatório

#### Scenario: Troca de Outros para outro tipo
- **WHEN** o usuário escolhe "Outros" e depois troca para "Falta descrição do material no frasco"
- **THEN** o campo de texto desaparece

### Requirement: Devolução por tipo de exame
Uma não conformidade registrada na conferência SHALL devolver tipos de exame inteiros da solicitação. Quando houver mais de um tipo pendente, o formulário SHALL listar os tipos com as suas amostras, todos marcados por padrão, e exigir ao menos um marcado; só os tipos marcados são devolvidos. Tipos desmarcados continuam pendentes, e tipos já recebidos não SHALL ser afetados.

#### Scenario: Devolver só um tipo
- **WHEN** a solicitação 1200001 tem os grupos CO e HP pendentes e o usuário desmarca CO e registra a não conformidade
- **THEN** só o grupo HP é devolvido, e a solicitação continua na fila com o grupo CO

#### Scenario: Nenhum tipo marcado
- **WHEN** o usuário desmarca todos os tipos e tenta registrar a devolução
- **THEN** o registro é recusado com o aviso "Selecione ao menos um exame para devolver."

#### Scenario: Exame já recebido
- **WHEN** o grupo CO da solicitação 1200001 já foi recebido e o usuário registra uma não conformidade na conferência do grupo HP
- **THEN** só o HP é devolvido, e o caso da Congelação não muda
