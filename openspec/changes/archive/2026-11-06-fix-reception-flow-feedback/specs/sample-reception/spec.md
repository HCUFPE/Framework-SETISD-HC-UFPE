## MODIFIED Requirements

### Requirement: Passos da recepção
A tela "Recepção de amostras" SHALL conduzir o recebimento em quatro passos: "Ler etiqueta AGHU", "Conferir", "Completar e confirmar" e "Etiquetas e ficha". O indicador de passos SHALL aparecer apenas a partir do passo "Conferir", mostrando os passos concluídos, o atual e os futuros. A tela inicial (passo "Ler etiqueta AGHU") não SHALL exibir o indicador.

#### Scenario: Início da recepção
- **WHEN** o usuário abre a tela "Recepção de amostras"
- **THEN** o passo "Ler etiqueta AGHU" é exibido sem o indicador de passos, e o campo de leitura recebe o foco

#### Scenario: Conferência iniciada
- **WHEN** o usuário inicia o recebimento de uma solicitação
- **THEN** o indicador de passos é exibido com "Ler etiqueta AGHU" concluído e "Conferir" como atual

### Requirement: Lista de solicitações pendentes
O passo 1 SHALL apresentar as solicitações do AGHU aguardando recebimento como uma fila de tarefas "Para receber", com a quantidade de pendentes. Cada item mostra tipo e nome do exame, nº da solicitação, material, origem e há quanto tempo aguarda, e tem a ação "Iniciar recebimento", equivalente à leitura do número. A fila SHALL listar primeiro as de Congelação e depois as demais, da mais antiga para a mais nova. Itens que aguardam há mais de 2 horas SHALL ser destacados.

#### Scenario: Ler pela lista
- **WHEN** o usuário clica em "Iniciar recebimento" em um item da fila
- **THEN** o resultado é o mesmo de ler o número dessa solicitação

#### Scenario: Espera longa
- **WHEN** uma solicitação aguarda recebimento há 3 horas
- **THEN** o item exibe "há 3 h" com destaque de atraso

#### Scenario: Lista vazia
- **WHEN** não há solicitações aguardando recebimento
- **THEN** a fila exibe "Nenhuma solicitação aguardando recebimento." com indicação de que não há tarefas pendentes

### Requirement: Campos de complementação do caso principal
Para os tipos HP, CG, CCV e CO, o sistema SHALL exigir quantidade de peças ou frascos (inteiro a partir de 1), "Urgente?" (Sim ou Não, sem valor padrão) e procedimento (lista padronizada). O motivo da urgência SHALL ser exigido quando "Urgente?" for Sim. Observações são opcionais. Para Congelação (CO), "Urgente?" SHALL ficar em Sim e não ser editável.

#### Scenario: Urgência sem motivo
- **WHEN** o usuário marca "Urgente?" como Sim e deixa o motivo vazio
- **THEN** a confirmação é recusada e o campo de motivo é indicado como obrigatório

#### Scenario: Urgência não informada
- **WHEN** o usuário tenta confirmar sem escolher Sim ou Não em "Urgente?"
- **THEN** a confirmação é recusada e o campo é indicado como obrigatório

#### Scenario: Congelação selecionada
- **WHEN** o usuário seleciona o tipo de exame Congelação (CO)
- **THEN** "Urgente?" passa a Sim, sem opção de alterar, e o motivo da urgência vem preenchido com "Exame de congelação (intraoperatório)", editável e ainda obrigatório

#### Scenario: Troca de Congelação para outro tipo
- **WHEN** o usuário troca o tipo de Congelação (CO) para Histopatológico (HP)
- **THEN** "Urgente?" volta a ser editável e sem valor escolhido, e o motivo sugerido é limpo se não tiver sido editado
