# Tasks

## 1. Backend: Parsing de 10 dígitos e metadados da amostra bipada

- [x] 1.1 Extrair `_extrair_codigo_e_amostra` e `_normalizar_numero_amostra` em `src/controllers/reception_controller.py`, atualizando `ReceptionController.ler_solicitacao` para decompor códigos de 10 dígitos (`[:7]` e `[7:]`), preservar `<codigo>-<amostra>` e `<codigo>:<tipo>`, e enriquecer a resposta com `amostraBipada`, `grupoSelecionadoId`, `examesFiltrados` e `amostraBipadaSituacao` quando aplicável. Verificar com testes unitários/API em `tests/test_reception_api.py`.
- [x] 1.2 Adicionar testes em `tests/test_reception_api.py` cobrindo: bipagem de 10 dígitos (`7712340001`), correspondência tolerante a zeros à esquerda (`"001"` vs `"1"`), solicitação mista com `grupoSelecionadoId` e `examesFiltrados`, amostra bipada já recebida/devolvida com outro grupo pendente (`amostraBipadaSituacao`), e código inexistente de 10 dígitos retornando `NAO_ENCONTRADA`. Verificar executando `pytest tests/test_reception_api.py`.

## 2. Frontend: Tipos, Store e UI de Conferência

- [x] 2.1 Atualizar `LeituraSolicitacao` em `frontend/src/types/ap.ts` e o estado/actions de `useRecepcaoStore` em `frontend/src/stores/recepcao.ts` para armazenar `amostraBipada`, `grupoSelecionadoId` e `amostraBipadaSituacao` na leitura e limpá-los ao reiniciar ou iniciar pela fila. Verificar com `npx vue-tsc --noEmit` em `frontend/`.
- [x] 2.2 Atualizar `PassoConferencia.vue`, `DadosSolicitacao.vue`, `ItemResultado.vue`, `RecepcaoAmostras.vue` e `BuscaCasoField.vue` para destacar a amostra bipada na tabela e no grupo correspondente, exibir todos os exames pendentes por padrão pré-marcando apenas o grupo da amostra bipada, exibir alerta quando a amostra bipada já tiver sido recebida ou devolvida, e aplicar ajustes de espaçamento, capitalização e centralização na UI. Verificar com `npm run build` em `frontend/`.

## 3. Verificação Final e Conformidade

- [x] 3.1 Executar a suíte completa de testes (`uv run pytest`), build do frontend (`npm run build` em `frontend/`) e auditoria do framework (`python audit_framework.py .`) garantindo 100% de conformidade.
