# Tasks

## 1. Confirmar contratos e decisões de acesso

- [x] 1.1 Mapear cada método de frontend/src/services/ap/types.ts para endpoint, payload, resposta e regra já existente nas specs e nos casos de uso.
- [x] 1.2 Reutilizar o catálogo e as dependências de add-sector-access-profiles; não adicionar usuários, sessões ou permissões locais à API.
- [x] 1.3 Não oferecer vínculo manual de IHQ, documentar associação automática futura com mecanismo a definir e remover o registro de impressão; conceder atualização da devolução aos perfis validados.
- [x] 1.4 Conceder consulta e atualização de devoluções a Recepcionista SAP e Coordenação/Administrador após validação SAP/HC; manter permissões distintas.

## 2. Persistência e provedores

- [x] 2.1 Definir modelos SQLAlchemy para o subconjunto de solicitação, caso, conferência, material inicial, vínculo IHQ, histórico, não conformidade e devolução alinhados ao modelo de dados existente.
- [x] 2.2 Criar migração Alembic, chaves estrangeiras, índices e restrições contra recebimento/vínculo duplicado e códigos internos repetidos.
- [x] 2.3 Criar interfaces de provider e implementação persistente no APP_DB para estado de domínio.
- [x] 2.4 Migrar fixture fictícia de solicitações para provedor de desenvolvimento/testes, com carga idempotente e opção de indisponibilidade simulada.
- [x] 2.5 Bloquear o uso do provedor fictício em produção e não configurar conexão AGHU nesta mudança.
- [x] 2.6 Garantir unicidade do número interno sob concorrência e atomicidade de gravação de domínio, histórico e auditoria.

## 3. Controllers, endpoints e segurança

- [x] 3.1 Implementar controllers para consultas e operações existentes sem alterar as regras funcionais.
- [x] 3.2 Implementar endpoints do catálogo de API documentado em design.md, com schemas Pydantic/aliases compatíveis com os tipos TypeScript.
- [x] 3.3 Proteger todas as rotas, inclusive GET, com identidade e exigir_permissao do catálogo central.
- [x] 3.4 Negar explicitamente operações pendentes, sem curinga de administrador e sem tratar consulta como autorização de mutação.
- [x] 3.5 Derivar autor do token, chamar o helper AuditLog com estados anterior/novo e IP do servidor e reverter estado se auditoria falhar.
- [x] 3.6 Preservar formato {"detail": "..."} e códigos de erro de autenticação, autorização, validação, conflito, inexistência e indisponibilidade do provider.

## 4. Adaptar serviços do frontend

- [x] 4.1 Criar implementações HTTP de AghuService, CasoService, NaoConformidadeService e AuditoriaService usando frontend/src/services/api.ts.
- [x] 4.2 Preservar assinaturas e retornos que stores e views usam, ignorando qualquer usuário enviado pelo cliente como autoria.
- [x] 4.3 Selecionar os serviços HTTP como origem normal em frontend/src/services/ap/index.ts e manter mocks somente em seleção explícita de teste/desenvolvimento isolado.
- [x] 4.4 Converter erros HTTP para ServiceError sem fallback silencioso, tratar 401/403 e refletir permissões nas ações já existentes.
- [x] 4.5 Manter telas e componentes Vue; executar impressão física no navegador sem endpoint, evento de histórico ou registro de auditoria.

## 5. Testes e critérios de aceite

- [x] 5.1 Reexecutar testes de todos os endpoints com token ausente, identidades mockadas de cada um dos nove perfis, identidade sem perfil e identidade com múltiplos perfis; verificar permissões pelo catálogo central.
- [x] 5.2 Verificar que esta mudança não oferece associação manual de IHQ, que a impressão não gera registro no backend, que a atualização de devolução é restrita aos perfis validados e que não há permissões presumidas para Citotécnico.
- [x] 5.3 Reexecutar testes de chamadas diretas à API, payload com autor forjado, validações, conflitos de estado, indisponibilidade do provider e erros {"detail": "..."}.
- [x] 5.4 Revalidar persistência entre sessões, seed idempotente, unicidade concorrente e rollback quando auditoria falha.
- [x] 5.5 Verificar auditoria da atualização de situação quanto a identidade, categoria, recurso, estados anterior/novo e IP, sem dados clínicos desnecessários.
- [x] 5.6 Verificar a impressão física no navegador, integração das stores/views e ausência de sucesso falso ou de operações de módulos futuros.
- [x] 5.7 Executar e registrar as verificações de arquitetura e frontend definidas em AGENTS.md e openspec/config.yaml. `npx vue-tsc --noEmit`, `npm run build` e a suíte Pytest passaram; o auditor reportou 10/11 porque o pilar de conectividade híbrida AD + RBAC institucional está fora do escopo desta mudança e sob responsabilidade futura do HC.
