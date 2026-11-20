## MODIFIED Requirements

### Requirement: Cabeçalho do caso
O detalhe SHALL exibir:
- o número interno, com ação de copiar;
- o selo de status;
- o selo URGENTE, quando aplicável, sem motivo;
- tipo de exame, paciente com prontuário, material e data de entrada.

#### Scenario: Caso urgente
- **WHEN** o usuário abre um caso urgente
- **THEN** o cabeçalho mostra o selo URGENTE, sem dica de motivo

### Requirement: Abas Solicitação AGHU e Recepção
A aba Solicitação AGHU SHALL exibir, somente leitura e identificados como vindos do AGHU, os mesmos dados mostrados na conferência, inclusive a lista das amostras do caso com número, descrição do material e status no AGHU. A aba Recepção SHALL exibir:
- entrada e responsável;
- tipo de exame, quantidade de amostras, urgência (Sim ou Não), procedimento e observações;
- a conferência registrada, com as amostras conferidas e o resultado.

#### Scenario: Conferência na aba Recepção
- **WHEN** o usuário abre a aba Recepção de um caso recebido no sistema
- **THEN** a conferência aparece com as amostras conferidas, o resultado "Aceita", o responsável e a data e hora, sem itens de checkbox

#### Scenario: Amostras na aba Solicitação AGHU
- **WHEN** o usuário abre a aba Solicitação AGHU de um caso com as amostras 2 e 3
- **THEN** as duas amostras aparecem separadas, cada uma com número, descrição e status no AGHU

### Requirement: Ações do caso ativo
Para casos ativos, o detalhe SHALL oferecer, nesta ordem, "Não conformidade", "Cancelar caso" e "Imprimir" (etiquetas das amostras ou ficha de trabalho). Para casos bloqueados, SHALL oferecer apenas "Imprimir". As ações SHALL ficar na mesma linha do número interno e dos selos, alinhadas à direita, e quebrar para a linha seguinte só quando não houver espaço. "Não conformidade" SHALL abrir o modal "Não conformidade e devolução". A impressão de etiquetas SHALL permitir escolher quais amostras imprimir quando o caso tiver mais de uma.

#### Scenario: Imprimir a partir do detalhe
- **WHEN** o usuário escolhe "Imprimir" e depois "Ficha de trabalho"
- **THEN** a pré-visualização da ficha de trabalho do caso é aberta

#### Scenario: Imprimir etiquetas escolhidas
- **WHEN** o usuário escolhe "Imprimir" e depois "Etiquetas" em um caso com 4 amostras
- **THEN** a pré-visualização permite marcar quais das 4 amostras imprimir

#### Scenario: Não conformidade no detalhe
- **WHEN** o usuário clica em "Não conformidade" em um caso ativo
- **THEN** o modal "Não conformidade e devolução" é aberto com o caso e a etapa atual identificados

#### Scenario: Posição das ações
- **WHEN** o usuário abre um caso ativo em tela larga
- **THEN** "Não conformidade", "Cancelar caso" e "Imprimir" aparecem nessa ordem, na linha do número interno e dos selos
