## Purpose

Define como o sistema gera alertas automáticos para cada solicitação da fila — incompatibilidades entre exames do mesmo paciente, janelas de retorno, preparo, jejum, idade, prazo de confirmação e duplicidade — a partir das regras configuráveis da gestão.

## ADDED Requirements

### Requirement: Estrutura e fonte dos alertas
Cada alerta SHALL conter `tipo` (um de `INCOMPATIBILIDADE`, `JANELA_RETORNO`, `ANTECEDENCIA_PREPARO`, `JEJUM_CLINICO`, `IDADE_MAMOGRAFIA`, `PRAZO_24H_VENCIDO`, `DUPLICIDADE`), `severidade` (`ALTA`, `MEDIA` ou `INFO`) e `mensagem` em português. O detector SHALL usar somente registros de `regras_exames` e `incompatibilidades_exames` com `ativo = true` e `deleted_at` nulo. A lista de alertas SHALL ser ordenada por severidade (`ALTA`, `MEDIA`, `INFO`), depois por tipo e por mensagem, sendo idêntica para a mesma entrada.

#### Scenario: Regra desativada não gera alerta
- **WHEN** a incompatibilidade colonoscopia × sangue está com `ativo = false`
- **THEN** nenhum alerta de incompatibilidade é gerado para esse par

#### Scenario: Item sem regras não gera alerta de regra
- **WHEN** o exame do item não tem regra cadastrada e não há outros exames no prontuário
- **THEN** a lista de alertas não contém alertas de regra de exame

### Requirement: Incompatibilidade entre exames do mesmo prontuário
O sistema SHALL comparar o exame do item com os demais exames pendentes ou agendados do mesmo prontuário (itens ativos da fila e, quando informados, solicitações do AGHU) e gerar `INCOMPATIBILIDADE` quando o par existir na matriz em qualquer direção (origem × conflitante ou conflitante × origem). A mensagem MUST citar os dois exames e o motivo cadastrado.
- Quando os dois exames têm data agendada e a distância entre elas, em dias, é menor que o intervalo mínimo cadastrado (ou é o mesmo dia, no tipo `MESMO_DIA`), a severidade SHALL ser `ALTA`.
- Quando ao menos um dos dois ainda não tem data, a severidade SHALL ser `MEDIA`, informando o intervalo mínimo a respeitar.
- Quando ambos têm data e respeitam o intervalo, nenhum alerta SHALL ser gerado.

Itens cancelados ou excluídos MUST NOT ser considerados.

#### Scenario: Colonoscopia e exame de sangue pendentes
- **WHEN** o prontuário tem colonoscopia e hemograma na fila, ambos sem data agendada
- **THEN** o item de colonoscopia recebe alerta `INCOMPATIBILIDADE` `MEDIA` citando o intervalo mínimo de 2 dias, e o item de hemograma recebe o alerta correspondente

#### Scenario: Agendados com intervalo insuficiente
- **WHEN** colonoscopia está agendada para 10/12 e hemograma para 11/12, com intervalo mínimo de 2 dias
- **THEN** o alerta `INCOMPATIBILIDADE` tem severidade `ALTA`

#### Scenario: Ressonância e oftalmologia no mesmo dia
- **WHEN** ressonância de crânio e mapeamento de retina estão agendados no mesmo dia
- **THEN** é gerado alerta `INCOMPATIBILIDADE` `ALTA`

#### Scenario: Intervalo respeitado
- **WHEN** colonoscopia está agendada para 10/12 e hemograma para 15/12
- **THEN** nenhum alerta de incompatibilidade é gerado

### Requirement: Janela de retorno
Para exames com `janela_retorno_max_horas` definida e item com data de retorno médico, o sistema SHALL gerar `JANELA_RETORNO`. A referência do retorno SHALL ser o início do dia do retorno.
- Com data agendada: severidade `ALTA` se o exame estiver agendado depois do retorno ou mais de `janela_retorno_max_horas` antes dele.
- Sem data agendada: severidade `INFO` informando o período válido para agendar; severidade `ALTA` se o retorno já passou.
- Com data agendada dentro da janela: nenhum alerta.

#### Scenario: Espirometria agendada mais de 10 dias antes do retorno
- **WHEN** a espirometria (janela 240h) está agendada 12 dias antes do retorno
- **THEN** é gerado `JANELA_RETORNO` `ALTA`

#### Scenario: Espirometria agendada após o retorno
- **WHEN** a espirometria está agendada um dia depois do retorno
- **THEN** é gerado `JANELA_RETORNO` `ALTA`

#### Scenario: INR acima de 72h
- **WHEN** o INR (janela 72h) está agendado 4 dias antes do retorno
- **THEN** é gerado `JANELA_RETORNO` `ALTA`

#### Scenario: INR dentro da janela
- **WHEN** o INR está agendado 2 dias antes do retorno
- **THEN** nenhum alerta de janela de retorno é gerado

### Requirement: Antecedência de preparo
Para exames com `antecedencia_minima_dias` maior que zero, o sistema SHALL gerar `ANTECEDENCIA_PREPARO`: `ALTA` quando a data agendada estiver a menos dias do momento do contato (ou de agora, sem contato registrado) do que o mínimo exigido; `INFO` com as orientações de preparo quando ainda não houver data agendada.

#### Scenario: Colonoscopia agendada sem tempo de preparo
- **WHEN** a colonoscopia (antecedência 3 dias) é agendada para daqui a 1 dia
- **THEN** é gerado `ANTECEDENCIA_PREPARO` `ALTA`

#### Scenario: Colonoscopia ainda sem data
- **WHEN** a colonoscopia ainda não tem data agendada
- **THEN** é gerado `ANTECEDENCIA_PREPARO` `INFO` informando os 3 dias mínimos

### Requirement: Jejum e diabéticos
Para exames com `exige_jejum = true`, o sistema SHALL gerar `JEJUM_CLINICO`: severidade `MEDIA` recomendando os primeiros horários da manhã quando o item estiver marcado como diabético e o exame tiver `priorizar_manha_diabetico = true`; severidade `INFO` informando a necessidade de jejum nos demais casos.

#### Scenario: Paciente diabético com exame em jejum
- **WHEN** um paciente diabético tem hemograma (jejum, priorizar manhã) na fila
- **THEN** é gerado `JEJUM_CLINICO` `MEDIA` recomendando horário matutino

### Requirement: Alerta etário
Para exames com `idade_minima_alerta`, o sistema SHALL gerar `IDADE_MAMOGRAFIA`: `MEDIA` quando a idade conhecida do paciente for menor que a idade mínima; `INFO` pedindo conferência da idade quando a data de nascimento não estiver disponível. Nenhum alerta SHALL ser gerado quando a idade conhecida atender ao mínimo.

#### Scenario: Mamografia sem data de nascimento
- **WHEN** o item é mamografia e não há data de nascimento
- **THEN** é gerado `IDADE_MAMOGRAFIA` `INFO` pedindo conferência da idade mínima de 40 anos

### Requirement: Prazo de 24h vencido
O sistema SHALL gerar `PRAZO_24H_VENCIDO` com severidade `ALTA` quando o item estiver em `AGUARDANDO_CONFIRMACAO_24H` e o prazo de confirmação for anterior ao momento atual.

#### Scenario: Prazo expirado
- **WHEN** o item aguarda confirmação e o prazo venceu há 1 hora
- **THEN** é gerado `PRAZO_24H_VENCIDO` `ALTA`

#### Scenario: Prazo em andamento
- **WHEN** o item aguarda confirmação e o prazo vence daqui a 2 horas
- **THEN** não é gerado alerta de prazo

### Requirement: Duplicidade
O sistema SHALL gerar `DUPLICIDADE` com severidade `ALTA` quando o item estiver com status de higienização `DUPLICADA` ou quando existir outro item ativo (não cancelado e não excluído) com o mesmo prontuário e o mesmo código de exame.

#### Scenario: Mesmo exame duas vezes no prontuário
- **WHEN** o prontuário tem dois itens ativos de ultrassonografia de abdome
- **THEN** ambos recebem alerta `DUPLICIDADE` `ALTA`
