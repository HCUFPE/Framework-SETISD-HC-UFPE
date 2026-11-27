## Why

Durante a visita técnica ao Serviço de Anatomia Patológica (SAP/HC-UFPE) em 11/11, identificou-se a necessidade operacional de manter vínculo relacional formal entre casos primários (como Histopatológico `HP`, Citologia `CG` ou `CCV`) e seus **exames derivados** — especificamente **Imuno-histoquímica (IHQ)** e **Revisão de Lâmina / Revisão Anatomopatológica** — solicitados tanto em conjunto na mesma requisição do AGHU quanto posteriormente pelo patologista após análise morfológica.

Atualmente, o modelo de dados contempla apenas a tabela `ApExameIhq` associada unilateralmente a `ApCaso` (`caso_numero`), apresentando três limitações estruturais:
1. **Ausência de relacionamento entre casos (`ApCaso` ↔ `ApCaso`):** casos de Revisão (ou derivados que geram número interno próprio) não possuem chave estrangeira nem metadado de derivação apontando para o caso de origem (`HP`), impedindo navegação bidirecional entre o exame pai e os exames filhos.
2. **Fluxo acoplado exclusivamente à sigla `IHQ`:** o componente `CasoOrigemIhq.vue` e os endpoints `GET /api/ap/casos/elegiveis-ihq` e `POST /api/ap/recebimentos/ihq` tratam apenas o vínculo de IHQ, sem suporte estruturado para vincular pedidos de Revisão ao caso original.
3. **Visibilidade incompleta na consulta e no detalhe do caso:** embora `ApCaso` carregue `ihqs[]`, não há visão consolidada e bidirecional que permita partir de um caso derivado para o seu caso de origem nem acompanhar todos os derivados (IHQs e Revisões) com seus respectivos códigos internos e status a partir do caso principal.

## What Changes

- **Migração Alembic e evolução do modelo relacional (`ap_casos` e `ap_exames_ihq`):**
  - Nova revisão do Alembic adicionando em `ap_casos`:
    - `caso_origem_numero` (`String`, FK nullable para `ap_casos.numero_interno`, indexada), estabelecendo auto-relacionamento entre caso derivado e caso de origem;
    - `tipo_derivacao` (`String`, nullable — ex.: `"IHQ"`, `"REVISAO"`), classificando a natureza do vínculo.
  - Preservação e evolução da tabela `ap_exames_ihq` para exames IHQ vinculados ao caso principal, unificando a projeção de derivados no agregado do caso sem quebrar dados já persistidos.
- **Regras de negócio, integridade e independência operacional (`ReceptionController` e `ReceptionSqliteProvider`):**
  - Validação estrita ao vincular caso/exame derivado: exige existência do caso de origem, impede auto-vínculo (`numero_interno == caso_origem_numero`) e ciclos diretos, e bloqueia vínculo a casos em status terminal inválido (`CANCELADO` ou `DEVOLVIDO`).
  - **Vínculo automático e contingência manual:** na conferência (`PassoConferencia.vue`), quando uma solicitação de `IHQ` ou `Revisão` chega na mesma solicitação AGHU de um caso principal elegível, o sistema pré-seleciona o caso de origem automaticamente; quando solicitado posteriormente (sem caso na mesma solicitação), mantém a busca manual com confirmação explícita em caso de divergência de prontuário.
  - **Independência de ciclo de vida:** cada exame derivado mantém seu código interno próprio (`IH-XXXX/YY` ou numeração do caso derivado) e pode ser cancelado ou devolvido individualmente sem cancelar o caso de origem (`HP`).
  - **Histórico bidirecional e auditoria:** toda vinculação registra eventos imutáveis em `ApHistoricoCaso` tanto no caso de origem quanto no derivado (quando aplicável) e grava registro transacional em `AuditLog`.
- **Evolução dos endpoints e contratos da API (`src/routers/reception.py` e `src/schemas/reception.py`):**
  - Estender `ConfirmarEntradaInput` para aceitar opcionalmente `casoOrigemNumero` e `tipoDerivacao` na entrada de casos derivados (como Revisão), mantendo o fluxo `POST /api/ap/recebimentos/ihq` para IHQ e compatibilidade retroativa com `GET /api/ap/casos/elegiveis-ihq`.
  - Enriquecer o payload de `GET /api/ap/casos/{numero}` com `casoOrigem` (resumo com `numeroInterno`, `tipoExame`, `status`, `dataEntradaSap`) e `examesDerivados` (lista unificada de IHQs e casos derivados vinculados, com código interno, tipo, status e data).
- **Interface de Recepção e Detalhe do Caso (`CasoOrigemIhq.vue`, `PassoConferencia.vue` e `DetalheCaso.vue`):**
  - Generalizar o seletor de caso de origem na conferência para atender tanto `IHQ` quanto `Revisão`, exibindo o contexto do caso pai selecionado.
  - Em `DetalheCaso.vue`, exibir card/banner de navegação para o **Caso de Origem** quando o registro visualizado for derivado, e consolidar a seção de **Exames Derivados** no caso principal com links diretos para cada exame filho.

## Capabilities

### New Capabilities
- `derived-exams-relational-link`: relacionamento estruturado em banco de dados (via migração Alembic) entre casos primários (`HP`, `CG`, `CCV`) e exames derivados (`IHQ` e `Revisão`), com vínculo automático ou manual na recepção, independência de status e navegação bidirecional.

### Modified Capabilities
- `sample-reception`: suporte ao vínculo de caso de origem para exames de Revisão além de IHQ durante a conferência, mantendo a contingência de seleção manual e auditoria completa.
- `case-detail`: exibição bidirecional do vínculo entre caso de origem e exames derivados (`IHQ` e `Revisão`) na tela de detalhe do caso.

## Impact

- **Backend:**
  - `alembic/versions/`: nova migração aditiva criando as colunas `caso_origem_numero` (FK para `ap_casos.numero_interno`) e `tipo_derivacao` em `ap_casos`.
  - `src/models/ap_reception.py`: atualização do modelo ORM `ApCaso` com os campos relacionais e constraint/índice de origem.
  - `src/providers/interfaces/reception_provider_interface.py` e `src/providers/implementations/reception_sqlite_provider.py`: persistência de `caso_origem_numero` / `tipo_derivacao` e montagem de `casoOrigem` e `examesDerivados` em `_caso_payload`.
  - `src/controllers/reception_controller.py`, `src/routers/reception.py` e `src/schemas/reception.py`: validação de elegibilidade do caso de origem para `IHQ` e `Revisão`, registro de histórico bidirecional e auditoria.
  - `tests/test_reception_api.py`: testes cobrindo criação de Revisão vinculada a `HP`, vínculo de `IHQ`, navegação bidirecional em `GET /api/ap/casos/{numero}`, independência de cancelamento e bloqueio de auto-vínculo/caso cancelado.
- **Frontend:**
  - `frontend/src/types/ap.ts` e `frontend/src/constants/ap.ts`: tipagem de `casoOrigem`, `examesDerivados` e identificação de exames de Revisão.
  - `frontend/src/components/ap/recepcao/CasoOrigemIhq.vue` e `PassoConferencia.vue`: suporte unificado a vínculo de origem para `IHQ` e `Revisão`.
  - `frontend/src/views/ap/DetalheCaso.vue`: exibição do vínculo com o caso pai e lista navegável de exames derivados.
- **Dados / Banco:** Exige execução de `alembic upgrade head` (já automatizada no `Dockerfile` e `start.sh`). Migração puramente aditiva com colunas nullable, retrocompatível com todos os casos já existentes.

## Refinamento de regra: associação de origem da IHQ

- Solicitações AGHU que possuem grupo HP próprio SHALL vincular a IHQ exclusivamente ao caso HP da mesma solicitação. Se HP e IHQ estiverem pendentes juntos, a recepção SHALL associar a IHQ automaticamente ao HP gerado na mesma conferência e SHALL bloquear o recebimento da IHQ isolada até o HP ser recebido.
- Se o HP da solicitação já tiver sido recebido, a conferência SHALL exibir apenas o número do HP associado, sem seleção ou busca manual.
- A busca manual de histopatológico SHALL estar disponível somente para solicitações IHQ sem grupo HP próprio. O backend SHALL rejeitar vínculos para outro caso quando houver HP da mesma solicitação.
