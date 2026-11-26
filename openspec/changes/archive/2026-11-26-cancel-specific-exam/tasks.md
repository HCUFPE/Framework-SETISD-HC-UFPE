# Tasks

## 1. Backend: estado, endpoint e auditoria

- [x] 1.1 Revisar `ApSolicitacao`, `ReceptionController` e fluxo existente de cancelamento de caso para confirmar persistência do payload, transação e padrão de permissões.
- [x] 1.2 Implementar `CancelarExameSolicitacaoInput` e `POST /api/ap/solicitacoes/cancelamento`, protegendo por `CASOS_CANCELAR`, validando chave/motivo/estado e derivando autor e IP do contexto autenticado/requisição.
- [x] 1.3 Persistir `CANCELADA` e `motivo`, `canceladoPor`, `canceladoEm` no grupo alvo sem alterar grupos irmãos; gravar `AuditLog` na mesma transação.
- [x] 1.4 Atualizar `ler_solicitacao`, `listar_solicitacoes_pendentes` e `contar_solicitacoes_pendentes` para tratar estado cancelado por grupo e solicitação totalmente cancelada.
- [x] 1.5 Adicionar testes de API para cancelamento parcial e total, motivo inválido, grupo inexistente, estados terminais, permissão 403, autor/IP confiáveis, auditoria atômica e recebimento de grupo irmão.

## 2. Frontend: tipos, serviço, store e interface

- [x] 2.1 Atualizar tipos de recepção e leitura para `CANCELADA` e metadados de cancelamento; integrar endpoint no serviço e store, incluindo atualização reativa dos pendentes.
- [x] 2.2 Implementar ação e modal com motivo obrigatório por grupo pendente em `PassoConferencia.vue`, condicionado a `CASOS_CANCELAR`; após sucesso, manter grupos irmãos recebíveis e retornar à leitura inicial quando todos forem cancelados.
- [x] 2.3 Apresentar estado, motivo, autor e data/hora em `PassoLeitura.vue` para solicitação totalmente cancelada.

## 3. Verificação

- [x] 3.1 Executar testes focados de recepção, `npx vue-tsc --noEmit` e `npm run build` em `frontend/` para atualizar `src/static/dist/`.
- [x] 3.2 Executar `python audit_framework.py .` e confirmar 100% de conformidade; corrigir eventuais regressões introduzidas pela implementação.
