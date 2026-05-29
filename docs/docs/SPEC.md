# SPEC.md - Contrato de Desenvolvimento (SDD)

## 1. Visão Geral e Resultados Esperados

Este documento é a ÚNICA fonte de verdade para a orquestração do desenvolvimento. O objetivo é construir um sistema de gestão clínica pediátrica para o HC/UFPE que digitalize o fluxo de atendimento de ponta a ponta, reduza o tempo de consulta de 1h30–2h para 35–45 minutos e elimine o formulário em papel.

### Objetivos de Alto Nível
- [ ] Autenticação via LDAP/AD com JWT + refresh token.
- [ ] Fila de atendimento com status em tempo real.
- [ ] Briefing clínico com alertas e histórico do paciente.
- [ ] Formulário digital de consulta com exportação AGHU.
- [ ] Dashboard gerencial com KPIs operacionais.
- [ ] Integração com AGHU via Provider (quando API disponível).

---

## 2. Contexto do Projeto (Documentação Imutável)

As definições detalhadas estão distribuídas nos seguintes documentos:
- [Visão](01-visao.md)
- [Requisitos](02-requisitos.md)
- [Casos de Uso](03-casos-uso.md)
- [Modelo de Dados](04-modelo-dados.md)
- [Interfaces](05-interfaces.md)
- [Arquitetura](06-arquitetura.md)
- [Glossário](07-glossario.md)

---

## 3. Limites de Escopo e Guardrails (Anti-Patterns)

**A IA DEVE:**
- Seguir rigorosamente o Modelo de Dados definido em `04-modelo-dados.md`.
- Criar a interface do Provider antes de qualquer implementação concreta de novo domínio.
- Usar Pydantic v2 para validação de entrada em todos os endpoints FastAPI.
- Usar soft delete (`deleted_at`) — nunca `DELETE` SQL em entidades de domínio.
- Declarar a `STRATEGY` de fonte de dados no roteador — nunca no controller ou provider.
- Manter segredos em `.env` — nunca hardcode no código.

**A IA NÃO DEVE:**
- Criar dependências externas não listadas em `pyproject.toml` sem aprovação explícita.
- Alterar arquivos de infraestrutura (`database.py`, `main.py`, `alembic.ini`) sem instrução explícita.
- Burlar ou contornar o sistema de RBAC baseado nos grupos do AD.
- Refatorar código não relacionado à task atual.
- Implementar exclusão física de registros.
- Adicionar lógica de negócio no roteador (deve ir no controller).

---

## 4. Task Breakdown (Plano de Implementação)

### Fase 1: Infraestrutura e Autenticação ✅ (em andamento)
- [x] [TASK-001] Autenticação LDAP/AD com emissão de JWT.
- [x] [TASK-002] Refresh token HttpOnly com rotação.
- [x] [TASK-003] Provider pattern com estratégia CSV/PostgreSQL.
- [x] [TASK-004] Endpoint de listagem de pacientes.
- [ ] [TASK-005] Migrations Alembic para todas as entidades do modelo de dados (`04-modelo-dados.md`).
- [ ] [TASK-006] Endpoint de criação/atualização de `QueueEntry` com auditoria de status.

### Fase 2: Módulo de Consulta
- [ ] [TASK-007] Endpoint `POST /api/consultas` — registro de consulta completa (antropometria, anamnese, exame físico, diagnóstico, procedimentos, encaminhamentos).
- [ ] [TASK-008] Endpoint `GET /api/pacientes/{id}/consultas` — histórico de consultas por paciente.
- [ ] [TASK-009] Endpoint `POST /api/consultas/{id}/encaminhamentos` — registro de encaminhamento.
- [ ] [TASK-010] Endpoint `PATCH /api/encaminhamentos/{id}/retorno` — confirmar retorno de encaminhamento.
- [ ] [TASK-011] Endpoint `POST /api/consultas/{id}/dados-externos` — registro de dados externos com `origemDescricao` obrigatório.

### Fase 3: Módulo de Alertas e Dashboard
- [ ] [TASK-012] Lógica de geração automática de alertas por categoria (peso, marco, encaminhamento, falta, negligência).
- [ ] [TASK-013] Endpoint `GET /api/pacientes/{id}/alertas` — alertas ativos por paciente.
- [ ] [TASK-014] Endpoint `GET /api/dashboard` — KPIs agregados com filtro de período (7/30/90 dias).
- [ ] [TASK-015] Endpoint `GET /api/dashboard/alertas-populacionais` — alertas filtrável por categoria.
- [ ] [TASK-016] Endpoint `GET /api/dashboard/encaminhamentos` — efetividade por especialidade.

### Fase 4: Integração AGHU
- [ ] [TASK-017] Implementar `AGHUProvider` para `PacienteProviderInterface` (dependente do mapeamento de endpoints por Filipe).
- [ ] [TASK-018] Sincronização de dados pós-consulta com AGHU via Provider.

### Fase 5: Frontend Vue 3
- [ ] [TASK-019] Tela de Fila de Atendimento com status em tempo real.
- [ ] [TASK-020] Tela de Briefing Clínico com alertas, linha do tempo e dados antropométricos.
- [ ] [TASK-021] Formulário de Consulta completo (6 abas + seções fixas de diagnóstico e procedimentos).
- [ ] [TASK-022] Geração de texto AGHU e ficha de encaminhamento.
- [ ] [TASK-023] Dashboard Gerencial com KPIs, gráficos e tabelas.
- [ ] [TASK-024] Caderneta Digital com curvas de crescimento.

---

## 5. Critérios de Verificação Global

- [ ] Todos os endpoints protegidos por JWT (`auth_handler.decode_token` no roteador).
- [ ] Nenhum segredo presente no código — verificar via grep antes de commit.
- [ ] Zero registros deletados fisicamente — verificar que `deleted_at` é usado em todas as entidades.
- [ ] Provider pattern respeitado — controller não importa implementação concreta, apenas interface.
- [ ] STRATEGY declarada no roteador, nunca no controller.
- [ ] Campo `origemDescricao` validado no backend antes de persistir `ConsultaExterna`.
- [ ] CID-10 principal obrigatório quando há encaminhamentos — validação no backend.
