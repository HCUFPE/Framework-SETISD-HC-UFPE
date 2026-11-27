# Tasks

## 1. Reabertura transacional no backend

- [x] 1.1 Atualizar provider/interface para validar os estados de `ApDevolucao`, `ApSolicitacao` e `ApCaso` e reabrir grupos ou caso na mesma sessão; verificar com testes de sucesso, HTTP 409 para cada estado bloqueado e rollback sem mutação parcial.
- [x] 1.2 Persistir `statusCasoAnterior` e a natureza original da rejeição no payload da ocorrência; verificar com testes de criação de devolução de caso e leitura de ocorrências pré-recepção após associação a caso.
- [x] 1.3 Orquestrar no controller o evento imutável `FLUXO_REABERTO` e a auditoria com estados anterior/novo, usuário e IP na mesma transação; verificar com testes de conteúdo da auditoria e rollback quando a gravação falhar.

## 2. Associação histórica no recebimento

- [x] 2.1 Associar não conformidade e devolução prévias ao caso criado para o `solicitacaoId` reaberto nos fluxos `confirmar_entrada` e `vincular_ihq`; verificar ambos os fluxos, preservação dos timestamps e idempotência sem eventos duplicados.
- [x] 2.2 Retornar os metadados da devolução regularizada em `ler_solicitacao` por código de 7 dígitos, código com hífen e etiqueta de 10 dígitos, e na listagem de pendentes; verificar que o aviso aparece em `PassoConferencia.vue` em todas as formas de abertura.
- [x] 2.3 Cobrir regressão de estado da devolução após a solicitação avançar; verificar que recebimento ou cancelamento posterior resulta em HTTP 409 e preserva estados e histórico.

## 3. Interface de reabertura e contexto

- [x] 3.1 Atualizar `RejeicoesDevolucoes.vue` para confirmar a reabertura e oferecer atalho à recepção ou ao caso correto; verificar cada tipo de devolução, mensagens de erro e navegação.
- [x] 3.2 Exibir o aviso de devolução regularizada em `PassoConferencia.vue` e o evento/contexto completo em `DetalheCaso.vue`; verificar rejeições pré-recepção e casos reabertos sem ocultar ocorrências anteriores.

## 4. Verificação integrada

- [x] 4.1 Executar `uv run pytest --basetemp=.venv/.pytest_tmp tests/test_reception_api.py` e verificar os cenários de ponta a ponta de rejeição, regularização, reabertura, novo recebimento, metadados em todas as modalidades de leitura e bloqueios terminais.
- [x] 4.2 Executar `npx vue-tsc --noEmit` e `npm run build` em `frontend/`; verificar compilação TypeScript sem erros e atualização de `src/static/dist/`.
- [x] 4.3 Executar `python audit_framework.py .` na raiz e verificar conformidade de 100% (EXCELENTE) nos 11 pilares.
