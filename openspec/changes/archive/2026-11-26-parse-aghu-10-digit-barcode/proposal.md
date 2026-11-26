## Why

As etiquetas impressas pelo AGHU para os frascos trazem um código de barras contínuo de **10 dígitos**, composto pelos **7 dígitos do código da solicitação** seguidos pelos **3 dígitos do número da amostra** (por exemplo, `7712340001` para a amostra `001` da solicitação `7712340`). Atualmente, o método `ler_solicitacao` (`src/controllers/reception_controller.py`) reconhece apenas o código puro da solicitação ou o formato separado por hífen (`7712340-001`), fazendo com que a bipagem direta da etiqueta do AGHU retorne `NAO_ENCONTRADA` e obrigando o recepcionista a digitar o código manualmente. Além disso, quando a solicitação possui múltiplos tipos de exame (como `CO` + `HP` ou `HP` + `IHQ`), a tela de conferência não filtra nem destaca automaticamente o exame correspondente à amostra bipada.

## What Changes

- **Parsing do código de 10 dígitos do AGHU:** `ReceptionController.ler_solicitacao` (e a leitura no frontend) passa a decompor entradas numéricas contínuas de 10 dígitos em `codigo_solicitacao = codigo[:7]` e `numero_amostra = codigo[7:]` (com comparação tolerante a zeros à esquerda, ex.: `"001"` e `"1"`), mantendo compatibilidade retroativa com códigos puros de solicitação, `codigo-amostra` e `codigo:TIPO`.
- **Identificação e filtro do exame pela amostra bipada:** Quando uma amostra específica é identificada na bipagem (seja via 10 dígitos ou `codigo-amostra`), a resposta de `GET /api/ap/solicitacoes/{codigo}` informa a amostra bipada (`amostraBipada`) e os grupos de exame correspondentes (`examesFiltrados` / `grupoSelecionadoId`).
- **Pré-seleção e destaque na conferência (`PassoConferencia.vue`):**
  - Se a solicitação tiver múltiplos exames pendentes e a bipagem apontar para uma amostra específica, a conferência filtra ou destaca o grupo de exame dono daquela amostra já pré-marcado para recebimento, mantendo opção explícita para exibir os demais exames pendentes da mesma solicitação quando necessário.
  - Se o exame daquela amostra específica já tiver sido recebido ou devolvido enquanto outros exames da solicitação seguem pendentes, a resposta sinaliza claramente o estado da amostra bipada sem impedir o recebimento dos demais exames pendentes.
- **Cobertura de testes:** Novos testes unitários e de API em `tests/test_reception_api.py` cobrindo bipagem de 10 dígitos, zeros à esquerda no número da amostra, solicitação mista filtrada pela amostra bipada e código inexistente.

## Capabilities

### New Capabilities
- `aghu-barcode-parsing`: decomposição determinística do código de barras de 10 dígitos do AGHU (`7` dígitos de solicitação + `3` dígitos de amostra) e resolução da amostra alvo dentro dos grupos de exame da solicitação.

### Modified Capabilities
- `sample-reception`: leitura por etiqueta bipada de 10 dígitos, filtragem/pré-seleção do grupo de exame correspondente à amostra bipada na etapa de conferência e feedback específico quando a amostra bipada já foi recebida ou devolvida.

## Impact

- **Backend:**
  - `src/controllers/reception_controller.py`: extração do parser de código bipado (`_extrair_codigo_e_amostra`) em `ler_solicitacao` e enriquecimento do retorno `PENDENTE` / `RECEBIDA` / `DEVOLVIDA` com os metadados da amostra bipada.
  - `tests/test_reception_api.py`: cenários de leitura com 10 dígitos em solicitações simples e mistas.
- **Frontend:**
  - `frontend/src/types/ap.ts` e `frontend/src/stores/recepcao.ts`: suporte ao metadado da amostra bipada no resultado de leitura e inicialização dos grupos selecionados na conferência.
  - `frontend/src/components/ap/recepcao/PassoConferencia.vue` e `PassoLeitura.vue`: destaque/filtro do exame correspondente à amostra bipada e botão/atalho para visualizar todos os exames da solicitação quando filtrados.
- **Dados / Banco:** Nenhuma alteração de schema ou migração Alembic necessária.