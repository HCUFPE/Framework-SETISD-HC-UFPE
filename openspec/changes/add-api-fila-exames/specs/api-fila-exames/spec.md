## Purpose

Define o contrato HTTP que a Central de Marcação usa para operar a fila de exames: consultar a fila priorizada com alertas, abrir o detalhe de uma solicitação, controlar a confirmação em 24 horas, corrigir solicitações pela busca ativa e consultar o AGHU em modo somente leitura.

## ADDED Requirements

### Requirement: Rotas protegidas por autenticação
Todas as rotas sob `/api/exames` SHALL exigir token JWT válido. Requisições sem token ou com token inválido MUST receber `401`. Erros SHALL ser retornados no formato `{"detail": "<mensagem>"}`.

#### Scenario: Acesso sem token
- **WHEN** um cliente chama `GET /api/exames/fila` sem cabeçalho `Authorization`
- **THEN** a resposta é `401`

### Requirement: Listagem da fila priorizada
`GET /api/exames/fila` SHALL retornar a lista de itens da fila (não excluídos) ordenada pelo motor de priorização, cada um com os campos do contrato `IItemFila` em camelCase: `id`, `codigoSolicitacao`, `codigoExame`, `nomeExame`, `prontuario`, `nomePaciente`, `telefoneContato`, `municipio`, `regiaoGeografica`, `utilizaTfd`, `unidadeSolicitante`, `dataSolicitacao`, `dataRetornoMedico`, `statusHigienizacao`, `statusOperacional`, `scorePrioridade`, `motivosPrioridade`, `alertas`, `contatoIniciadoEm`, `prazoConfirmacaoEm`, `dataAgendadaAghu`, `preparoOrientado`. `nomeExame` e `dataSolicitacao` SHALL vir do AGHU quando a solicitação for encontrada (`dataSolicitacao` cai para a data de entrada na fila quando não for).

Sem filtros de status, a listagem SHALL trazer apenas itens com higienização `VALIDA` e status operacional `NA_FILA`, `AGUARDANDO_CONFIRMACAO_24H` ou `SEM_RESPOSTA_24H`.

#### Scenario: Fila ordenada com score e motivos
- **WHEN** existem um item da Oncologia e um de rotina válidos na fila
- **THEN** a resposta é `200`, o item da Oncologia vem primeiro e ambos trazem `scorePrioridade`, `motivosPrioridade` e `alertas`

#### Scenario: Itens finalizados ficam fora por padrão
- **WHEN** existe um item `CONFIRMADO_AGENDADO_AGHU` e a fila é consultada sem filtro de status
- **THEN** esse item não aparece na resposta

### Requirement: Filtros e paginação da fila
`GET /api/exames/fila` SHALL aceitar os parâmetros opcionais `codigo_exame`, `unidade`, `status_operacional`, `status_higienizacao`, `municipio`, `regiao` (`CAPITAL`, `RMR`, `INTERIOR`, `NAO_INFORMADO`), `apenas_tfd`, `apenas_24h_vencidos`, `busca`, `limit` (1 a 500) e `offset` (0 ou mais), combináveis entre si. Informar `status_operacional` ou `status_higienizacao` SHALL substituir o filtro padrão correspondente. O cabeçalho `X-Total-Count` SHALL conter o total após os filtros e antes da paginação. Os filtros MUST NOT alterar `scorePrioridade` nem `motivosPrioridade`. Valores inválidos de enumeração MUST retornar `422`.

#### Scenario: Filtro geográfico preserva o score
- **WHEN** a fila é consultada com `regiao=CAPITAL`
- **THEN** só itens da capital são retornados, com o mesmo score que têm na fila sem filtro

#### Scenario: Somente prazos de 24h vencidos
- **WHEN** a fila é consultada com `apenas_24h_vencidos=true`
- **THEN** só itens em `AGUARDANDO_CONFIRMACAO_24H` com prazo anterior a agora são retornados

#### Scenario: Paginação
- **WHEN** a fila tem 3 itens e é consultada com `limit=2&offset=0`
- **THEN** a resposta tem 2 itens e `X-Total-Count: 3`

#### Scenario: Região inválida
- **WHEN** a fila é consultada com `regiao=SERTAO`
- **THEN** a resposta é `422`

### Requirement: Detalhe da solicitação
`GET /api/exames/fila/{id}` SHALL retornar o item com os mesmos campos da listagem, mais `outrosExames` (demais exames do mesmo prontuário vindos da fila local e do AGHU, cada um com `codigoSolicitacao`, `codigoExame`, `nomeExame`, `origem` `FILA` ou `AGHU` e, quando houver, `dataAgendada` e `statusOperacional`) e `orientacoesPreparo` do exame. Os alertas do detalhe SHALL considerar também os exames do AGHU. Item inexistente ou excluído MUST retornar `404`.

#### Scenario: Detalhe com conflito vindo do AGHU
- **WHEN** o item é uma colonoscopia e o AGHU tem um hemograma para o mesmo prontuário
- **THEN** `outrosExames` inclui o hemograma com `origem` `AGHU` e `alertas` inclui `INCOMPATIBILIDADE`

#### Scenario: Item inexistente
- **WHEN** o cliente chama `GET /api/exames/fila/99999`
- **THEN** a resposta é `404`

### Requirement: Transições de status com prazo de 24h
`PATCH /api/exames/fila/{id}/status` SHALL receber `statusOperacional` e, opcionalmente, `dataAgendadaAghu`, `preparoOrientado` e `observacoes`, e aplicar somente estas transições:
- `NA_FILA` → `AGUARDANDO_CONFIRMACAO_24H` ou `CANCELADO`
- `AGUARDANDO_CONFIRMACAO_24H` → `CONFIRMADO_AGENDADO_AGHU`, `SEM_RESPOSTA_24H` ou `CANCELADO`
- `SEM_RESPOSTA_24H` → `NA_FILA` ou `CANCELADO`

Ao entrar em `AGUARDANDO_CONFIRMACAO_24H`, o sistema SHALL gravar `contatoIniciadoEm` = agora e `prazoConfirmacaoEm` = agora + 24 horas. Ao voltar para `NA_FILA`, SHALL limpar esses dois campos. `CONFIRMADO_AGENDADO_AGHU` MUST exigir `dataAgendadaAghu`. Transição não listada, item com higienização diferente de `VALIDA` ou confirmação sem data MUST retornar `400` sem alterar o item. Item inexistente MUST retornar `404`. A resposta de sucesso SHALL ser `200` com o item atualizado.

#### Scenario: Iniciar aguardo de 24h
- **WHEN** um item `NA_FILA` recebe `statusOperacional=AGUARDANDO_CONFIRMACAO_24H`
- **THEN** a resposta é `200`, `contatoIniciadoEm` é o momento da requisição e `prazoConfirmacaoEm` é exatamente 24 horas depois

#### Scenario: Confirmar agendamento no AGHU
- **WHEN** um item aguardando confirmação recebe `CONFIRMADO_AGENDADO_AGHU` com `dataAgendadaAghu` e `preparoOrientado=true`
- **THEN** a resposta é `200` e o item guarda a data agendada e o preparo orientado

#### Scenario: Confirmação sem data
- **WHEN** um item aguardando confirmação recebe `CONFIRMADO_AGENDADO_AGHU` sem `dataAgendadaAghu`
- **THEN** a resposta é `400` e o item não muda

#### Scenario: Transição inválida
- **WHEN** um item `NA_FILA` recebe `CONFIRMADO_AGENDADO_AGHU`
- **THEN** a resposta é `400` com `detail` explicando a transição não permitida

#### Scenario: Prazo vencido é sinalizado
- **WHEN** um item está aguardando confirmação com prazo de 24h já vencido e a fila é consultada
- **THEN** o item traz alerta `PRAZO_24H_VENCIDO`

### Requirement: Auditoria das mutações
Toda alteração bem-sucedida de status ou de vínculo de solicitação SHALL gravar um registro em `audit_logs` com categoria `NEGOCIO_CLINICO`, usuário do token, IP de origem, recurso `acompanhamento_fila:<id>`, ação (`ALTERAR_STATUS_FILA` ou `VINCULAR_SOLICITACAO`), e os campos alterados antes (`dados_anteriores`) e depois (`dados_novos`). Requisições rejeitadas MUST NOT gravar auditoria.

#### Scenario: Transição auditada
- **WHEN** o usuário `admin` move um item de `NA_FILA` para `AGUARDANDO_CONFIRMACAO_24H`
- **THEN** existe um registro em `audit_logs` com usuário `admin`, categoria `NEGOCIO_CLINICO`, `dados_anteriores` com `NA_FILA` e `dados_novos` com `AGUARDANDO_CONFIRMACAO_24H` e o prazo calculado

#### Scenario: Transição rejeitada não audita
- **WHEN** uma transição inválida é rejeitada com `400`
- **THEN** nenhum registro novo é criado em `audit_logs`

### Requirement: Vinculação de solicitação por busca ativa
`PATCH /api/exames/fila/{id}/vincular-solicitacao` SHALL receber `codigoSolicitacao` e `codigoExame`, consultar o AGHU e, se o par existir, atualizar o item com código de solicitação, código do exame e prontuário do AGHU e mudar a higienização para `VALIDA`. Só itens com higienização `NAO_ENCONTRADA` ou `DIVERGENCIA_EXAME` SHALL poder ser vinculados (`400` nos demais). Par inexistente no AGHU MUST retornar `404`. Se já existir outro item ativo com o mesmo prontuário e exame, MUST retornar `409`. O sistema MUST NOT escrever no AGHU.

#### Scenario: Corrigir código digitado errado
- **WHEN** um item `NAO_ENCONTRADA` é vinculado a uma solicitação e exame existentes no AGHU
- **THEN** a resposta é `200`, o item fica `VALIDA` com o prontuário do AGHU e a ação é auditada

#### Scenario: Solicitação inexistente no AGHU
- **WHEN** o código informado não existe no AGHU
- **THEN** a resposta é `404` e o item não muda

#### Scenario: Vínculo geraria duplicidade
- **WHEN** já existe item ativo do mesmo prontuário e exame
- **THEN** a resposta é `409`

### Requirement: Busca ativa no AGHU
`GET /api/exames/aghu/buscar` SHALL aceitar `prontuario`, `codigo_solicitacao` ou `nome` (mínimo de 3 caracteres, parte do nome, sem diferenciar maiúsculas) e retornar as solicitações do AGHU encontradas em modo somente leitura, com os campos normalizados do provider. Sem nenhum parâmetro, MUST retornar `400`. Sem resultados, SHALL retornar `200` com lista vazia.

#### Scenario: Busca por prontuário
- **WHEN** o cliente busca um prontuário existente no CSV do AGHU
- **THEN** a resposta é `200` com as solicitações desse prontuário

#### Scenario: Busca por nome
- **WHEN** o cliente busca `nome=anonimizado 01`
- **THEN** a resposta contém as solicitações do paciente cujo nome contém esse trecho

#### Scenario: Busca sem parâmetros
- **WHEN** o cliente chama a busca sem parâmetros
- **THEN** a resposta é `400`
