# SPEC.md - Contrato de Desenvolvimento (SDD) — SAE-HC

## 1. Visão Geral e Resultados Esperados
Este documento é a **ÚNICA fonte de verdade** para a orquestração do desenvolvimento do Sistema de Agendamento de Exames do HC-UFPE (SAE-HC). Toda implementação deve ser rastreável até um requisito de `02-requisitos.md` e validada contra os critérios desta seção.

### Objetivos de Alto Nível
- [ ] Fila única de solicitações, ordenada automaticamente por critérios de priorização versionados (RF005/RF006, RN-02/RN-03).
- [ ] Tela de trabalho da Central de Marcação com conferência contra o AGHUX, assinatura eletrônica e registro de contato (RF007/RF008/RF010/RF011).
- [ ] Painel gerencial em tempo real com os cinco indicadores de negócio e relatórios (RF014).
- [ ] Administração de critérios de priorização e da equipe com perfis locais validados no AD (RF006/RF016).
- [ ] Trilha de auditoria imutável para toda mutação (RF013, RNF002/RNF005).

### Entrega atual (F0 a F3 + início da Fase 4 — v0.2.0)
Escopo aprovado: **frontend navegável com dados simulados**, agora alimentados pelo export real do AGHUX (576 itens agrupados em 493 solicitações), **mais o backend da integração Microsoft Forms → AGHUX**, que inicia a Fase 4. A versão é `v0.2.0` (`src/version.py` e fallback em `frontend/src/config/version.ts`); **nenhuma tag de produção foi criada**.

A integração adota a abordagem híbrida (Forms → Power Automate → webhook assinado), persiste eventos e solicitações no banco local com criptografia de CPF/CNS e trilha de auditoria, e expõe a tela administrativa `/integracoes`. Os contratos HTTP já implantados estão em `05-interfaces.md`; os demais contratos de domínio permanecem documentados para entregas seguintes. As telas operacionais (Fila, Painel, Relatórios, Critérios e Equipe) continuam usando o adaptador de mocks, controlado por `VITE_USE_MOCKS` (`frontend/.env.example`, documentado em `06-arquitetura.md`). O resumo de escopo (política de vagas/compatibilidade) segue pendente de apontamentos e **não é implementado nesta entrega**.

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
- Seguir rigorosamente o Modelo de Dados definido em `04-modelo-dados.md`, inclusive soft delete e criptografia AES-GCM (chave de 32 bytes, nonce de 96 bits) de CPF/CNS.
- Implementar testes automatizados para cada nova funcionalidade de backend; validar o frontend com `npm run build` e verificar manualmente os fluxos das telas.
- Manter os interceptadores de `frontend/src/services/api.ts` e os componentes reutilizáveis do framework.
- Proteger toda rota de dados com `Depends(auth_handler.decode_token)` no roteador; a única exceção pública é `POST /api/integracoes/forms/webhook`, protegida por HMAC-SHA256, timestamp e nonce. No frontend, declarar `meta.roles` e tratar a autorização no backend como fonte de verdade.
- Registrar mudanças de critérios, perfis e solicitações via `registrar_auditoria()` com `dados_anteriores`, `dados_novos`, `ip_origem` e categoria.
- Executar o auditor de conformidade ao final de cada entrega. O script `audit_framework.py` possui um defeito conhecido na função `colorize()` (`ENDC` não qualificado) que **não deve ser corrigido nesta entrega**; executá-lo por shim em memória:
  `python -c "import audit_framework as a; a.ENDC=''; a.FrameworkAuditor('.').run()"`

**A IA NÃO DEVE:**
- Criar dependências externas não documentadas em `06-arquitetura.md`. Nesta entrega há **uma dependência backend nova**, `cryptography>=42`, e **zero dependências npm novas**; gráficos seguem em SVG/CSS.
- Implementar exclusão física de registros (usar `deleted_at`).
- Burlar o sistema RBAC; esconder controles no frontend nunca substitui a validação no backend.
- Alterar manualmente a prioridade individual de solicitações na tela do operador (RN-02); exceções são exclusivas da Área Gestora e exigem justificativa (RN-03).
- Corrigir `audit_framework.py`, `src/main.py` ou demais arquivos de infraestrutura sem instrução explícita neste `SPEC.md`.
- Prometer recursos não implementados: agendamento real no AGHU, provider `FORMS_API` funcional ou tag de produção. `FORMS_API` e `AGHU` são apenas pontos de extensão reservados.

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

### Fase 4 — Backend de domínio (iniciada nesta entrega)
- [x] [TASK-024] Implementar models, providers, controllers e routers protegidos; integração real com formulário externo e AGHUX; notificações e regras de cancelamento/reagendamento. **Concluída no escopo desta entrega** quanto aos models/providers/controllers/routers da integração Forms → AGHUX. Notificações, cancelamento/reagendamento e o provider `AGHU` real **não foram implementados** e permanecem para entrega futura.
- [x] [TASK-026] Criar os modelos `forms_responses`, `webhook_nonces`, `solicitacoes`, `solicitacao_itens_exame`, `divergencias` e `alertas`, com a migração Alembic `c4f1a7d9e2b3` (revises `8a2efbe37bb6`).
- [x] [TASK-027] Definir `FormsProviderInterface` (Mock, Power Automate e `FORMS_API` reservado) e `AghuxProviderInterface` (`AghuxJsonProvider` sobre a fixture de 576 itens / 493 solicitações e `AghuProvider` reservado), com fábricas em `src/dependencies.py`.
- [x] [TASK-028] Proteger o webhook com HMAC-SHA256 sobre `timestamp . nonce . corpo_bruto`, cabeçalhos `X-SAE-Timestamp`, `X-SAE-Nonce` e `X-SAE-Signature`, janela `WEBHOOK_MAX_SKEW_SECONDS` e nonce único anti-replay; documentar a exceção pública ao default-private.
- [x] [TASK-029] Expor `POST /api/integracoes/forms/webhook`, `GET /api/integracoes/forms/eventos` e `POST /api/integracoes/forms/eventos/{responseId}/reprocessar`, com processamento em `BackgroundTasks`, idempotência e RBAC nos endpoints administrativos.
- [x] [TASK-030] Criptografar CPF/CNS com AES-GCM via `cryptography`, manter hashes HMAC para deduplicação, máscara nos últimos 4 dígitos e nenhum dado sensível em logs, auditoria ou respostas da API.
- [x] [TASK-031] Entregar a tela `/integracoes` no grupo **Sistema** (`AREA_GESTORA`/`ADMIN_TI`) para listar eventos e reprocessar falhas/duplicidades, mantendo o fallback de versão `v0.2.0` no frontend.
- [x] [TASK-032] Validar a entrega: 18 testes pytest (9 anteriores + 9 novos), `npm run build` e auditoria 11/11 via shim em memória.

## 5. Critérios de Verificação Global
- [x] `npm run build` conclui sem erros de tipo (`vue-tsc`) para o frontend.
- [x] Auditoria arquitetural: 11/11 (100%, EXCELENTE) com o comando via shim da Seção 3.
- [x] `uv run pytest` sem regressões: 18 testes aprovados (9 anteriores + 9 novos em `tests/test_integracao_forms.py`), cobrindo HMAC válido/inválido, skew, replay, idempotência, RBAC, reprocessamento, alerta sem correspondência no AGHUX e cripto.
- [x] Nenhuma mutação de tela sem registro correspondente no histórico simulado; as mutações da integração são gravadas em `audit_logs` com estado anterior/posterior, IP de origem e categoria.
- [x] Nenhum CPF/CNS inventado nos mocks ou nos provedores: o export AGHUX não contém esses campos e um formulário sem CPF/CNS não inventa valores; quando informados, são criptografados com AES-GCM, com hash HMAC para deduplicação e máscara `***` nos últimos 4 dígitos, nunca em claro em payload, auditoria, logs ou respostas da API.
- [x] Zero dependências novas em `frontend/package.json` nesta entrega; a única dependência backend adicionada é `cryptography>=42` (via `uv`), documentada em `06-arquitetura.md`.
