## Purpose

Define a camada de dados do frontend (tipos e stores) e a tela da fila de exames (`/fila`) que a Central de Marcação usa para consultar a fila priorizada, analisar alertas, controlar a confirmação em 24 horas e corrigir solicitações pela busca ativa no AGHU.

Verificação: o projeto não tem runner de testes de frontend; os cenários são verificados por `npm run build` (checagem de tipos com `vue-tsc`) e pelo fluxo manual no navegador contra o backend real, com `pytest` e `audit_framework.py` garantindo que o backend segue intacto.

## ADDED Requirements

### Requirement: Contratos TypeScript da fila
`frontend/src/types/exames.ts` SHALL exportar os tipos da seção 4 de `05-interfaces.md` e os tipos do detalhe de `src/schemas/fila.py` (`IOutroExame`, `IItemFilaDetalhe` com `outrosExames` e `orientacoesPreparo`), os corpos dos requests de status e vínculo, os filtros da fila com chaves snake_case e a linha da busca no AGHU com chaves snake_case.

#### Scenario: Build tipado
- **WHEN** `npm run build` é executado em `frontend/`
- **THEN** o `vue-tsc` termina sem erros usando esses tipos nas stores e na tela

### Requirement: Stores com carregamento e erro padronizados
As stores `exames`, `regras` e `dashboard` SHALL usar o `api.ts` existente, expor estado de carregamento e a mensagem de erro do campo `detail` da resposta (ou uma mensagem padrão quando não houver), e MUST NOT alterar os interceptadores do Axios.

#### Scenario: Erro do backend exibido
- **WHEN** o backend responde `400` com `{"detail": "Transição de NA_FILA para CONFIRMADO_AGENDADO_AGHU não permitida."}`
- **THEN** a store guarda exatamente essa mensagem e a ação devolve `null`

#### Scenario: Endpoint ainda não disponível
- **WHEN** a store `dashboard` chama `GET /api/dashboard/kpis` num backend sem a TASK-011
- **THEN** a store fica sem KPIs e com mensagem de erro, sem quebrar a aplicação

### Requirement: Fila priorizada na ordem da API
A rota `/fila` SHALL exigir autenticação e exibir os itens na ordem devolvida por `GET /api/exames/fila`, sem reordenar, mostrando posição, score com os motivos em tooltip, paciente, exame, unidade, município/região/TFD, status e alertas.

#### Scenario: Ordem preservada
- **WHEN** a API devolve um item da Oncologia antes de um de rotina
- **THEN** a tabela mostra o item da Oncologia na posição 1 e o tooltip do score lista os motivos

#### Scenario: Acesso sem login
- **WHEN** um usuário não autenticado abre `/fila`
- **THEN** é redirecionado para `/login`

### Requirement: Badges de alertas e prazo de 24h
A tabela SHALL exibir badges dos alertas de severidade `ALTA` e `MEDIA` (cores distintas) e MUST NOT exibir alertas `INFO`, que aparecem só no detalhe. Itens em `AGUARDANDO_CONFIRMACAO_24H` SHALL mostrar o prazo de confirmação convertido de UTC para o horário local e, quando o prazo já passou, um destaque de "vencido".

#### Scenario: Prazo vencido destacado
- **WHEN** um item aguarda confirmação com `prazoConfirmacaoEm` anterior ao horário atual
- **THEN** a linha mostra o badge de prazo vencido e o alerta `PRAZO_24H_VENCIDO`

#### Scenario: Alerta INFO só no detalhe
- **WHEN** um item tem apenas alertas `INFO`
- **THEN** a coluna de alertas da tabela fica vazia e o detalhe lista esses alertas

### Requirement: Filtros e paginação
A tela SHALL oferecer filtros de exame, unidade, status operacional, status de higienização, município, região (`CAPITAL`, `RMR`, `INTERIOR`, `NAO_INFORMADO`), apenas TFD, apenas 24h vencidos e busca, enviados como query params snake_case, e paginação por `limit`/`offset` usando o total do cabeçalho `X-Total-Count`. Alterar filtros SHALL voltar para a primeira página.

#### Scenario: Filtro geográfico
- **WHEN** o usuário filtra por região `CAPITAL`
- **THEN** a requisição leva `regiao=CAPITAL` e a tabela mostra só os itens devolvidos, com o mesmo score

#### Scenario: Paginação pelo total
- **WHEN** a API devolve `X-Total-Count: 23` com `limit=10`
- **THEN** a tela mostra "1–10 de 23" e permite ir para as páginas seguintes

### Requirement: Detalhe da solicitação
O detalhe SHALL exibir os dados do item, os motivos do score, todos os alertas (incluindo `INFO`), os outros exames do prontuário com a origem (`FILA` ou `AGHU`) e as orientações de preparo.

#### Scenario: Conflito com exame do AGHU
- **WHEN** o usuário abre o detalhe de uma colonoscopia cujo prontuário tem hemograma no AGHU
- **THEN** o detalhe lista o hemograma com origem `AGHU` e o alerta de incompatibilidade

### Requirement: Modal de status com transições permitidas
O modal de status SHALL oferecer só os destinos de `TRANSICOES_PERMITIDAS` para o status atual. Confirmar o agendamento (`CONFIRMADO_AGENDADO_AGHU`) MUST exigir data/hora, enviada em ISO 8601 com fuso, e SHALL permitir marcar preparo orientado. Observações SHALL poder ser informadas em qualquer transição. Itens com higienização diferente de `VALIDA` MUST NOT oferecer mudança de status.

#### Scenario: Status final
- **WHEN** o item está `CONFIRMADO_AGENDADO_AGHU` ou `CANCELADO`
- **THEN** o modal informa que não há transições disponíveis

#### Scenario: Confirmação sem data bloqueada
- **WHEN** o usuário escolhe confirmar o agendamento sem informar data/hora
- **THEN** o botão de salvar fica desabilitado e nenhuma requisição é enviada

#### Scenario: Horário agendado preservado
- **WHEN** o usuário confirma com data/hora local 01/12 09:30
- **THEN** a requisição envia `dataAgendadaAghu` em ISO com fuso e o detalhe volta exibindo 01/12 09:30

### Requirement: Busca ativa no AGHU e vinculação
A busca ativa SHALL estar disponível só para itens `NAO_ENCONTRADA` ou `DIVERGENCIA_EXAME`, buscar por prontuário, código de solicitação ou nome (mínimo de 3 letras) em `GET /api/exames/aghu/buscar` e permitir vincular um resultado com `PATCH /api/exames/fila/{id}/vincular-solicitacao`.

#### Scenario: Nome curto
- **WHEN** o usuário busca por nome com menos de 3 letras
- **THEN** a tela avisa e não envia a requisição

#### Scenario: Corrigir código digitado errado
- **WHEN** o usuário vincula um resultado do AGHU a um item `NAO_ENCONTRADA`
- **THEN** o item passa a `VALIDA`, a tela confirma e recarrega a fila
