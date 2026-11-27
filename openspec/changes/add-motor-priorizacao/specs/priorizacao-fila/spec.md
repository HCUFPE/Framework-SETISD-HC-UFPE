## Purpose

Define como o sistema calcula, de forma determinística e explicável, a prioridade clínica de cada solicitação da fila de exames a partir das regras configuráveis pela gestão, e como os filtros operacionais e geográficos são aplicados sem alterar essa prioridade.

## ADDED Requirements

### Requirement: Score calculado a partir das regras configuradas
O sistema SHALL calcular o `score_prioridade` de cada item usando exclusivamente as regras de `regras_prioridade` com `ativo = true` e `deleted_at` nulo. Nenhum peso MUST estar fixo no código.

O score SHALL ser composto por:
- **Grupo clínico principal:** o MAIOR peso entre as regras dos tipos `CLINICA`, `GRUPO_CLINICO` e `VULNERAVEL` que casarem com o item (pesos desses tipos não se somam entre si).
- **Rotina:** quando nenhuma regra de grupo clínico casar, aplica-se a regra `GRUPO_CLINICO` cujo `valor_match` é `ROTINA`, se existir e estiver ativa.
- **Bônus aditivos:** soma dos pesos das regras `AFINIDADE_EXAME` e `RETORNO_PROXIMO` que casarem.

Uma regra `CLINICA`, `GRUPO_CLINICO` ou `VULNERAVEL` SHALL casar quando qualquer termo do seu `valor_match` (separado por vírgula, comparação sem acento e sem diferença de maiúsculas) estiver contido na especialidade solicitante, na unidade solicitante ou no grupo prioritário manual do item. A regra cujo termo é `HEMODIALISE` SHALL casar também quando o item tiver a marcação de hemodiálise.

#### Scenario: Oncologia supera rotina mesmo com solicitação mais recente
- **WHEN** a fila contém um item de rotina solicitado em 01/11 e um item da Oncologia solicitado em 20/11, com as regras do seed inicial
- **THEN** o item da Oncologia aparece antes do item de rotina

#### Scenario: Grupos clínicos não se somam
- **WHEN** um item casa com Nefrologia (65) e com Hemodiálise (75) e não tem bônus
- **THEN** o score do item é 75 e não 140

#### Scenario: Regra inativa ou excluída é ignorada
- **WHEN** a regra de Oncologia está com `ativo = false` ou `deleted_at` preenchido
- **THEN** itens da Oncologia não recebem o peso dessa regra

#### Scenario: Item sem grupo recebe rotina
- **WHEN** um item não casa com nenhuma regra de grupo clínico
- **THEN** o score base do item é o peso da regra de rotina e o motivo de rotina é listado

### Requirement: Bônus de retorno próximo e afinidade clínica
O sistema SHALL somar o peso de uma regra `RETORNO_PROXIMO` quando a data de retorno médico do item estiver entre hoje e hoje + N dias (inclusive), sendo N lido do `valor_match` no formato `<=N`. Datas de retorno já passadas ou ausentes MUST NOT receber o bônus.

O sistema SHALL somar o peso de uma regra `AFINIDADE_EXAME` quando a especialidade ou unidade solicitante compartilhar ao menos um termo significativo (4+ letras, sem acento) com a unidade executora ou o nome do exame cadastrados em `regras_exames` para o código do exame do item.

#### Scenario: Retorno dentro da janela recebe bônus
- **WHEN** a data de retorno do item é daqui a 10 dias e a regra de retorno é `<=15` com peso 20
- **THEN** o score inclui +20 e os motivos incluem o nome da regra de retorno

#### Scenario: Retorno fora da janela ou passado não recebe bônus
- **WHEN** a data de retorno do item é daqui a 30 dias, ou foi ontem
- **THEN** o score não inclui o bônus de retorno

#### Scenario: Afinidade entre clínica e exame
- **WHEN** um item da Gastroenterologia solicita colonoscopia, cuja unidade executora cadastrada contém "GASTROENTEROLOGIA"
- **THEN** o score inclui o peso da regra de afinidade

### Requirement: Justificativa explícita do score
O sistema SHALL retornar, junto com o score, a lista `motivos_prioridade` com uma entrada por regra aplicada, no formato `"<nome da regra> +<peso>"`, na ordem: grupo clínico principal, depois bônus em ordem decrescente de peso. A soma dos pesos listados MUST ser igual ao score.

#### Scenario: Motivos somam o score
- **WHEN** um item da Oncologia tem retorno em 5 dias
- **THEN** os motivos são `["Oncologia +100", "Retorno em até 15 dias +20"]` (nomes conforme cadastro) e o score é 120

### Requirement: Ordenação determinística
O sistema SHALL ordenar a fila por score decrescente, depois por data de solicitação crescente (mais antiga primeiro; itens sem data vão para o fim do empate) e por fim pelo id crescente. Dadas as mesmas solicitações, as mesmas regras e a mesma data de referência, o resultado MUST ser idêntico em todas as execuções.

#### Scenario: Desempate pela data de solicitação
- **WHEN** dois itens têm o mesmo score e datas de solicitação diferentes
- **THEN** o item com a data mais antiga aparece primeiro

#### Scenario: Execuções repetidas produzem a mesma ordem
- **WHEN** a fila é calculada duas vezes com os mesmos dados e regras
- **THEN** a ordem e os scores são idênticos

### Requirement: Alteração de peso reflete imediatamente
O sistema SHALL reler as regras de prioridade a cada cálculo da fila, sem cache entre requisições, de modo que uma alteração de peso no banco local mude a ordenação na próxima leitura sem reiniciar o servidor.

#### Scenario: Peso alterado inverte a ordem
- **WHEN** a regra de rotina tem seu peso alterado no banco para um valor maior que o de Oncologia e a fila é recalculada
- **THEN** o item de rotina passa a aparecer antes do item da Oncologia

### Requirement: Filtros operacionais e geográficos preservam o score
O sistema SHALL permitir filtrar a fila já pontuada por código do exame, unidade solicitante, status operacional, status de higienização, município, região geográfica (`CAPITAL`, `RMR`, `INTERIOR`, `NAO_INFORMADO`), somente pacientes com TFD, e busca textual (prontuário ou código de solicitação exatos, ou parte do nome do paciente). Os filtros MUST ser aplicados depois do cálculo do score e MUST NOT alterar o score nem os motivos de nenhum item. A ordem relativa dos itens restantes MUST ser a mesma da fila completa.

#### Scenario: Filtro por região mantém o score
- **WHEN** a fila completa é filtrada por região `CAPITAL`
- **THEN** cada item retornado tem o mesmo score e motivos que tinha na fila completa, na mesma ordem relativa

#### Scenario: Filtro de TFD
- **WHEN** o filtro "somente TFD" está ativo
- **THEN** apenas itens com TFD são retornados

#### Scenario: Busca por prontuário
- **WHEN** a busca contém um número de prontuário existente
- **THEN** apenas os itens desse prontuário são retornados
