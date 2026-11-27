# Tasks

## 1. Persistência e migração

- [x] 1.1 Adicionar a relação opcional de origem e o tipo de derivação ao modelo `ApCaso`, com FK autorreferente e índice; verificar mapeamento SQLAlchemy e compatibilidade de criação das tabelas.
- [x] 1.2 Criar migração aditiva das colunas e índice, sem alterar linhas existentes; verificar upgrade e rollback em banco temporário e confirmar que casos antigos seguem consultáveis.
- [x] 1.3 Estender a persistência de Revisão para gravar o número interno próprio, origem e tipo de derivação; verificar no provider que a relação persiste após nova sessão.
- [x] 1.4 Integrar Revisão ao reconhecimento de tipo e à geração de identificador interno sem alterar sequências existentes de casos principais; verificar a geração e unicidade do identificador de Revisão.

## 2. Regras de recepção e API

- [x] 2.1 Estender o contrato de confirmação para receber origem e tipo de derivação opcionais; verificar validação de payload válido e rejeição de campos incompatíveis.
- [x] 2.2 Implementar elegibilidade da origem, bloqueio de autorreferência e ciclos, estado terminal e divergência de prontuário; verificar cenários permitidos e recusados diretamente no controller/provider.
- [x] 2.3 Implementar sugestão automática de origem pela solicitação e busca manual para Revisão, preservando confirmação explícita para prontuário divergente; verificar os dois caminhos por testes de API.
- [x] 2.4 Registrar histórico nos casos envolvidos e auditoria da mutação na mesma transação; verificar que falha de auditoria reverte vínculo, caso e histórico.
- [x] 2.5 Adicionar testes de API para recebimento de Revisão vinculada, IHQ vinculada, origem inelegível, autovínculo, ciclo e independência de cancelamento/devolução; executar `uv run pytest tests/test_reception_api.py`.

## 3. Contrato de detalhe do caso

- [x] 3.1 Estender a montagem do payload de caso com `casoOrigem` e `examesDerivados`, projetando IHQs existentes sem duplicá-las como casos; verificar payload de caso de origem, derivado e caso legado sem vínculo.
- [x] 3.2 Adicionar testes de provider e API para navegação bidirecional, status atualizado de derivados e metadados de origem; executar os testes focados de recepção e verificar persistência entre sessões.

## 4. Interface

- [x] 4.1 Generalizar o seletor de origem na conferência para IHQ e Revisão, com sugestão automática, busca manual e confirmação de divergência; verificar o fluxo com `npx vue-tsc --noEmit` e build de produção.
- [x] 4.2 Exibir origem no detalhe do derivado e lista consolidada navegável de IHQs e Revisões no caso principal; verificar estados com e sem derivados e executar `npx vue-tsc --noEmit` em `frontend/`.

## 5. Verificação integrada

- [x] 5.1 Executar a suíte backend na raiz com `uv run pytest --basetemp=.venv/.pytest_tmp` e corrigir regressões na recepção, no detalhe e nas permissões relacionadas.
- [x] 5.2 Executar `npx vue-tsc --noEmit` e `npm run build` em `frontend/` para atualizar `src/static/dist/`, além de `python audit_framework.py .`; confirmar ausência de erros de tipagem e conformidade arquitetural de 100%.


## 6. Regra de associação da IHQ por solicitação

- [x] 6.1 Vincular automaticamente a IHQ ao HP da mesma solicitação, bloquear IHQ isolada enquanto esse HP estiver pendente e exibir o HP associado sem controles de seleção.
- [x] 6.2 Restringir a busca manual ao pedido IHQ sem grupo HP próprio e reforçar a regra no `ReceptionController`.
- [x] 6.3 Cobrir pedido misto pendente, HP já recebido com tentativa de outra origem e IHQ avulsa nos testes de API; executar pytest, build frontend e auditoria arquitetural.
