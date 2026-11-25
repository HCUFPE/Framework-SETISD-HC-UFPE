# SPEC.md — Contrato de Desenvolvimento (SDD)

## 1. Visão Geral e Resultados Esperados

Este documento é a **fonte de verdade executável** para a implementação do **Sistema Interno de Gestão de Fila e Triagem de Exames (Otimização da Gestão de Vagas para Exames Diagnósticos)** do **HC-UFPE (EBSERH)**, construído sobre o `Framework-SETISD-HC-UFPE`.

### Objetivos de Alto Nível (MVP para 04/12 e Demonstração Presencial em 09/12)
- [ ] **Leitura AGHU Multi-Provedor:** Consumir solicitações oficiais do AGHU via `ExameCsvProvider` (CSV oficial do Drive em dev) e `ExamePostgresProvider` (SQL nativo em produção).
- [ ] **Importação e Higienização (`Forms × AGHU`):** Importar planilha do Google Forms sem alterá-la, cruzando com o AGHU para detectar códigos inválidos, exames divergentes, duplicidades e exames já realizados, com busca ativa por prontuário.
- [ ] **Priorização Determinística e Configurável:** Ordenar a fila com base em pesos editáveis pela gestão (padrão inicial: Oncologia → Transplante → Nefrologia/Hemodiálise → Vulneráveis → Rotina) exibindo justificativa clara da posição.
- [ ] **Motor de Alertas e Filtro Geográfico:** Alertar incompatibilidades (preparo/mesmo dia), janelas de retorno (espirometria ≤ 10d, INR ≤ 72h), preparo e jejum; oferecer filtro geográfico (Capital/RMR/Interior/TFD) para vagas de última hora sem alterar a prioridade clínica.
- [ ] **Controle de Confirmação 24h e Auditoria:** Acompanhar o fluxo ideal (`Na Fila` → `Aguardando Confirmação 24h` → `Confirmado / Agendado no AGHU` ou `Sem Resposta 24h`) com trilha imutável em `audit_logs`.
- [ ] **Dashboard de KPIs e Conformidade SETISD:** Exibir indicadores gerenciais e manter 100% de aderência aos 11 pilares (`pytest` + `audit_framework.py`).

---

## 2. Contexto do Projeto (Especificação Oficial)

As definições detalhadas estão distribuídas nos seguintes documentos:
- [Validação e Fluxo de Negócio](00-validacao-negocio.md) *(Fase 0 — Negócio e Matriz de Decisões)*
- [Visão](01-visao.md)
- [Requisitos](02-requisitos.md)
- [Casos de Uso e Fluxo TO-BE](03-casos-uso.md)
- [Modelo de Dados e Schemas](04-modelo-dados.md)
- [Interfaces e Contratos API/TS](05-interfaces.md)
- [Arquitetura, Segurança e Guardrails](06-arquitetura.md)
- [Glossário](07-glossario.md)
- [Processo Atual Visual (AS-IS)](processo-atual.JPG)

---

## 3. Limites de Escopo e Guardrails (Anti-Patterns)

**A IA E A EQUIPE DEVEM:**
- Seguir rigorosamente `AGENTS.md`, o fluxo unidirecional (`SQL → Provider → Controller → Router`) e o Modelo de Dados em `04-modelo-dados.md`.
- Manter **todas as regras de prioridade, preparo, retorno e incompatibilidade configuráveis via banco local SQLite** (com seed inicial editável).
- Registrar `registrar_auditoria()` em todas as mutações (`NEGOCIO_CLINICO`, `CONFIGURACAO`, `SEGURANCA`).
- Proteger todos os novos roteadores com `dependencies=[Depends(auth_handler.decode_token)]` (*Default-Private Router Pattern*).
- Criar testes `pytest` para cada nova funcionalidade e validar os 11 pilares SETISD ao concluir cada fase.

**A IA E A EQUIPE NÃO DEVEM:**
- Escrever no banco PostgreSQL do AGHU ou alterar o ticket impresso (`AELR_TICKET_PACIENTE`).
- Criar portal externo para o paciente ou integração de disparo automático de WhatsApp/SMS.
- Incluir no escopo atendimentos presenciais diretos na Central, remarcação/faltas, códigos em lote do AGHU ou fila estadual (CMCE).
- Usar `DELETE` físico (Hard Delete) ou alterar registros em `audit_logs`.
- Usar `CPF` como chave obrigatória de identificação do paciente (usar `prontuario` + `codigo_solicitacao`).
- Hardcodar credenciais ou alterar os interceptadores Axios / middleware de Security Headers.

---

## 4. Task Breakdown (Plano Incremental e Divisão por Integrante)

### Fase 1: Fundação, Dados e Provider AGHU — **Komata** *(Início Imediato)*
- [ ] `[TASK-001]` **(Komata)** Incorporar `consulta_aghu_exames.sql` (e queries auxiliares por solicitação/prontuário) em `src/providers/sql/exames/` e o CSV oficial do Drive em `data/exames_aghu_mock.csv`.
- [ ] `[TASK-002]` **(Komata)** Criar `ExameProviderInterface` e `ExameCsvProvider` (normalizando aspas duplas do CSV oficial, alias `data_solicitao` e `prontuario` anulável).
- [ ] `[TASK-003]` **(Komata)** Criar `ExamePostgresProvider`, registrar a fábrica `get_exame_provider(STRATEGY)` em `src/dependencies.py` e criar testes `pytest` do Provider CSV.
- [ ] `[TASK-004]` **(Komata)** Criar models SQLAlchemy (`ImportacaoForms`, `AcompanhamentoFila`, `RegraPrioridade`, `RegraExame`, `IncompatibilidadeExame`) em `src/models/` com suporte a soft delete (`deleted_at`).
- [ ] `[TASK-005]` **(Komata)** Criar migração Alembic para as novas tabelas e script de seed inicial (pesos padrão, regras de espirometria/INR/mamografia e incompatibilidades iniciais).

### Fase 2: Regras de Negócio e API REST (Backend FastAPI)
- [ ] `[TASK-006]` **(Eduardo)** Implementar CRUD configurável de Pesos, Regras de Exames e Incompatibilidades (`src/controllers/regras_controller.py` e `src/routers/regras.py`, RBAC `GESTOR_CENTRAL`/`ADMINISTRADOR`, soft delete, auditoria `CONFIGURACAO` e testes `pytest`).
- [ ] `[TASK-007]` **(Eduardo)** Implementar importação e higienização `Forms × AGHU` (`POST /api/importacoes/forms`, `GET /api/importacoes`, detectando código inválido, exame divergente e duplicidades + testes `pytest`).
- [ ] `[TASK-008]` **(Gabriel)** Implementar motor determinístico de priorização clínica (score + justificativa explicável lendo `regras_prioridade`) e filtro geográfico operacional (Capital/RMR/Interior/TFD) + testes `pytest`.
- [ ] `[TASK-009]` **(Gabriel)** Implementar detector de conflitos, preparo e janelas de retorno (cruzamento de exames do mesmo prontuário contra `incompatibilidades_exames` e `regras_exames`: colonoscopia × sangue, ressonância × oftalmo, espirometria ≤ 10d, INR ≤ 72h, jejum/diabético) + testes `pytest`.
- [ ] `[TASK-010]` **(Gabriel)** Implementar endpoints `/api/exames/*` (`GET /fila`, `GET /fila/{id}`, busca ativa por prontuário `GET /aghu/buscar`, `PATCH /vincular-solicitacao` e controle de confirmação 24h `PATCH /fila/{id}/status` com `audit_logs`) + testes `pytest`.
- [ ] `[TASK-011]` **(Arthur)** Implementar endpoints `GET /api/dashboard/kpis` e `GET /api/admin/audit-logs` + testes `pytest`.

### Fase 3: Interface Web (Frontend Vue 3 + Pinia + Tailwind)
- [ ] `[TASK-012]` **(Pedro)** Criar tipos TypeScript (`frontend/src/types/exames.ts`) e stores Pinia (`exames.ts`, `regras.ts`, `dashboard.ts`).
- [ ] `[TASK-013]` **(Pedro)** Implementar tela principal `FilaExames.vue` (fila priorizada com motivo do score, badges de alertas/24h, filtro geográfico de urgência, busca ativa por prontuário e modal de atualização de status).
- [ ] `[TASK-014]` **(Murilo)** Implementar `ImportacaoForms.vue` (upload CSV/XLSX + relatório de higienização/duplicidades/divergências e histórico).
- [ ] `[TASK-015]` **(Murilo)** Implementar `RegrasConfiguracao.vue` (3 abas editáveis: Pesos de Prioridade, Regras por Exame e Matriz de Incompatibilidades).
- [ ] `[TASK-016]` **(Arthur)** Implementar `DashboardKpis.vue` e atualizar navegação no `DefaultLayout.vue` + rotas em `frontend/src/router/index.ts`.

### Fase 4: Conformidade, Build e Preparação para Deploy (09/12)
- [ ] `[TASK-017]` **(Eduardo)** Executar suíte `pytest` completa, validar conformidade de 100% nos 11 pilares SETISD (`audit_framework.py`), build do frontend (`npm run build`), validação ponta a ponta em `./dev.sh` / `compose.yaml` e preparar tag `v1.0.0`.

---

## 5. Critérios de Verificação Global
- [ ] 100% dos testes `pytest` passando (existentes + novos módulos).
- [ ] 100% de conformidade nos 11 pilares arquiteturais do SETISD.
- [ ] Zero rotas clínicas sem `Depends(auth_handler.decode_token)`.
- [ ] Zero hardcodes de segredos ou regras de negócio não editáveis.
- [ ] Fluxo completo validado ponta a ponta (Importação Forms → Higienização → Fila Priorizada → Filtro Urgência → Aguardo 24h → Confirmação AGHU → KPIs e Audit Log).
