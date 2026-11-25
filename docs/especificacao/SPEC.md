# SPEC.md - Contrato de Desenvolvimento (SDD) — SAE-HC

## 1. Visão Geral e Resultados Esperados
Este documento é a **ÚNICA fonte de verdade** para a orquestração do desenvolvimento do Sistema de Agendamento de Exames do HC-UFPE (SAE-HC). Toda implementação deve ser rastreável até um requisito de `02-requisitos.md` e validada contra os critérios desta seção.

### Objetivos de Alto Nível
- [ ] Fila única de solicitações, ordenada automaticamente por critérios de priorização versionados (RF005/RF006, RN-02/RN-03).
- [ ] Tela de trabalho da Central de Marcação com conferência contra o AGHUX, assinatura eletrônica e registro de contato (RF007/RF008/RF010/RF011).
- [ ] Painel gerencial em tempo real com os cinco indicadores de negócio e relatórios (RF014).
- [ ] Administração de critérios de priorização e da equipe com perfis locais validados no AD (RF006/RF016).
- [ ] Trilha de auditoria imutável para toda mutação (RF013, RNF002/RNF005).

### Entrega atual (F0 a F3)
Escopo aprovado: **frontend navegável com dados simulados**, agora alimentados pelo export real do AGHUX (576 itens agrupados em 493 solicitações). Nenhum endpoint de domínio é criado nesta entrega; os contratos HTTP ficam documentados em `05-interfaces.md` para a entrega seguinte. O adaptador de mocks é controlado por `VITE_USE_MOCKS` (`frontend/.env.example`, documentado em `06-arquitetura.md`). O resumo de escopo (política de vagas/compatibilidade) fica pendente de apontamentos e **não é implementado nesta entrega**.

## 2. Contexto do Projeto (Documentação Imutável)
- [Validação e Fluxo de Negócio](00-validacao-negocio.md) (Fase 0 - Negócio)
- [Visão](01-visao.md)
- [Requisitos](02-requisitos.md)
- [Casos de Uso](03-casos-uso.md)
- [Modelo de Dados](04-modelo-dados.md)
- [Interfaces](05-interfaces.md)
- [Arquitetura](06-arquitetura.md)
- [Glossário](07-glossario.md)

## 3. Limites de Escopo e Guardrails (Anti-Patterns)
**A IA DEVE:**
- Seguir rigorosamente o Modelo de Dados definido em `04-modelo-dados.md`, inclusive soft delete e criptografia AES-256 de CPF/CNS.
- Implementar testes automatizados para cada nova funcionalidade de backend; no frontend desta entrega, validar com `npm run build` e verificar manualmente os fluxos das telas.
- Manter os interceptadores de `frontend/src/services/api.ts` e os componentes reutilizáveis do framework.
- Proteger toda rota de dados com `Depends(auth_handler.decode_token)` no roteador; no frontend, declarar `meta.roles` e tratar a autorização no backend como fonte de verdade.
- Registrar mudanças de critérios, perfis e solicitações via `registrar_auditoria()` com `dados_anteriores`, `dados_novos`, `ip_origem` e categoria.
- Executar o auditor de conformidade ao final de cada entrega. O script `audit_framework.py` possui um defeito conhecido na função `colorize()` (`ENDC` não qualificado) que **não deve ser corrigido nesta entrega**; executá-lo por shim em memória:
  `python -c "import audit_framework as a; a.ENDC=''; a.FrameworkAuditor('.').run()"`

**A IA NÃO DEVE:**
- Criar dependências externas não documentadas em `06-arquitetura.md` (nesta entrega: nenhuma dependência npm nova; gráficos em SVG/CSS).
- Implementar exclusão física de registros (usar `deleted_at`).
- Burlar o sistema RBAC; esconder controles no frontend nunca substitui a validação no backend.
- Alterar manualmente a prioridade individual de solicitações na tela do operador (RN-02); exceções são exclusivas da Área Gestora e exigem justificativa (RN-03).
- Corrigir `audit_framework.py`, `src/main.py` ou demais arquivos de infraestrutura sem instrução explícita neste `SPEC.md`.

## 4. Task Breakdown (Plano de Implementação)

### Fase 0 — Alinhamento de especificação e identidade
- [x] [TASK-010] Reescrever `03-casos-uso.md` com os atores e casos de uso do SAE-HC.
- [x] [TASK-011] Reescrever `04-modelo-dados.md` com as entidades de solicitação, priorização, equipe e auditoria.
- [x] [TASK-012] Documentar protótipos, estados e contratos de API em `05-interfaces.md`.
- [x] [TASK-013] Documentar stack, adaptador de mocks e guardrails em `06-arquitetura.md`.
- [x] [TASK-014] Atualizar identidade do sistema e versão inicial (`src/version.py`) para `SAE-HC` / `v0.1.0`.

### Fase 1 — Casca navegável
- [x] [TASK-015] Rotas com `meta.roles`, tela de acesso negado e redirect inicial por perfil.
- [x] [TASK-016] Menu lateral do `DefaultLayout.vue` por grupo funcional, com filtro por perfil e rodapé SemVer.
- [x] [TASK-017] Tipos compartilhados, fixtures de mocks e adaptador com o mesmo contrato do `api.ts`.

### Fase 2 — Telas com mocks
- [x] [TASK-018] Fila de Marcação com ordenação por prioridade, filtros e painel lateral de conferência (RF005/RF007/RF008/RF010/RF011).
- [x] [TASK-019] Painel de Gestão com os cinco KPIs e gráficos em SVG/CSS (RF014).
- [x] [TASK-020] Relatórios com filtros, prévia e exportação CSV (RF014).
- [x] [TASK-021] Critérios de Priorização com pesos, versionamento e justificativa (RF006).
- [x] [TASK-022] Equipe e Perfis com "Consultar AD" simulado e perfis locais (RF016).
- [x] [TASK-025] Importar o export CSV do AGHUX para os mocks: agrupar itens por solicitação, preservar datas reais, ancorar "agora" em `2026-09-28T16:05:34.227` e paginar a fila de 20 em 20 (RF005/RF007/RF014).

### Fase 3 — Contratos para o backend (documentação nesta entrega)
- [x] [TASK-023] Publicar em `05-interfaces.md` os contratos de `/api/fila`, `/api/painel/indicadores`, `/api/relatorios`, `/api/criterios-priorizacao` e `/api/admin/equipe`.

### Fase 4 — Backend de domínio (entrega futura)
- [ ] [TASK-024] Implementar models, providers, controllers e routers protegidos; integração real com formulário externo e AGHUX; notificações e regras de cancelamento/reagendamento.

## 5. Critérios de Verificação Global
- [ ] `npm run build` conclui sem erros de tipo (`vue-tsc`) para o frontend.
- [ ] Auditoria arquitetural: 11/11 (100%, EXCELENTE) com o comando via shim da Seção 3.
- [ ] `uv run pytest` sem regressões na suíte existente.
- [ ] Nenhuma mutação de tela sem registro correspondente no histórico simulado (auditoria em F4).
- [ ] Nenhum CPF/CNS inventado nos mocks: o export AGHUX não contém esses campos, e a listagem usa prontuário; mascaramento e criptografia ficam para o backend (Fase 4).
- [ ] Zero dependências externas novas em `frontend/package.json` nesta entrega.
