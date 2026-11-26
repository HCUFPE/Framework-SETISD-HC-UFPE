# SPEC.md - Contrato de Desenvolvimento (SDD) — SAE-HC

## 1. Visão Geral e Resultados Esperados
Este documento é a **ÚNICA fonte de verdade** para a orquestração do desenvolvimento do Sistema de Agendamento de Exames do HC-UFPE (SAE-HC). Toda implementação deve ser rastreável até um requisito de `02-requisitos.md` e validada contra os critérios desta seção.

### Objetivos de Alto Nível
- [ ] Fila única de solicitações, ordenada automaticamente por critérios de priorização versionados (RF005/RF006, RN-02/RN-03).
- [ ] Tela de trabalho da Central de Marcação com conferência contra o AGHUX, assinatura eletrônica e registro de contato (RF007/RF008/RF010/RF011).
- [ ] Painel gerencial em tempo real com os cinco indicadores de negócio e relatórios (RF014).
- [ ] Administração de critérios de priorização e da equipe com perfis locais validados no AD (RF006/RF016).
- [ ] Trilha de auditoria imutável para toda mutação (RF013, RNF002/RNF005).

### Entrega atual (F0 a F9 — v0.7.0)
Escopo aprovado: **frontend navegável com dados simulados** alimentados pelo export real do AGHUX (576 itens agrupados em 493 solicitações) e por 30 solicitações simuladas recentes, **backend da integração Microsoft Forms → AGHUX** (v0.2.0), **gestão de agendamentos com calendário, vagas locais, remarcação, sugestão automática e distância até o hospital** (v0.3.0), **a rotina da Central de Marcação** (v0.4.0), **o refinamento da simulação e da governança de vagas** (v0.5.0), **o redesenho da gestão de vagas** (v0.6.0) e, agora, **propostas de agendamento como cards arrastáveis no calendário com drag-and-drop para ajuste de horário**: seleção de exames em uma linha no topo, calendário inferior com seleção de dia, inclusão/remoção arbitrária de vagas com horários, cópia de configurações entre semanas e simulação corrigida para não lotar vagas já preenchidas. O cenário de demonstração está reancorado em `25/11/2026 16:05`. A versão é `v0.7.0` (`src/version.py` e fallback em `frontend/src/config/version.ts`); **nenhuma tag de produção foi criada nesta entrega**.

A integração adota a abordagem híbrida (Forms → Power Automate → webhook assinado), persiste eventos e solicitações no banco local com criptografia de CPF/CNS e trilha de auditoria, e expõe a tela administrativa `/integracoes`. A v0.4.0 mantém o FullCalendar v6 (mês/semana, ocupação por vaga, arrastar para remarcar) e acrescenta: colunas padrão `#`, `Prioridade`, `Paciente / Prontuário`, `Unidade solicitante`, `Exame(s)`, `Status` e `Tempo na fila`, com menu de exibição persistido no navegador e filtro por unidade solicitante; no painel da solicitação, apenas os dados já cadastrados no AGHUX, com divergências pendentes em seção condicional e o botão **Efetuar marcação**; no calendário, nenhuma solicitação é listada na abertura — a busca ocorre sob demanda, o exame da solicitação é filtro duro de disponibilidade e o clique em um dia abre os horários para marcação direta. A simulação dos próximos 30 dias gera propostas que reservam vaga, mas só se tornam agendamentos `ATIVO` após confirmação do operador; recusa, sem resposta ou não confirmação encaminham para `AGUARDANDO_REAGENDAMENTO`. Na v0.5.0 a simulação passa a contabilizar a ocupação gerada no próprio loop (capacidade, exame compatível, mesmo paciente e distribuição entre dias) e publica as propostas em formato de fila, ordenadas por pontuação, tempo de espera e protocolo, com os campos `#`, `Prioridade`, `Paciente / Prontuário`, `Unidade solicitante`, `Exame(s)`, `Status`, `Tempo na fila` e horário proposto. A Chefia da Central passa a ter as mesmas permissões de administração de vagas da Área Gestora, podendo criar/editar unidade, exame, horário, capacidade e situação da vaga. Na v0.6.0 o gestor de vagas é reorganizado em uma linha de exames no topo e um calendário inferior com seleção de dia; a lista do dia permite acrescentar, editar e remover vagas (soft delete, bloqueado quando há agendamento ativo ou proposta), e a cópia semanal replica dia da semana, unidade, exame, horário, capacidade e situação de origem para destino, ignorando vagas já existentes. Remoção e cópia são operações do backend com RBAC e auditoria `CONFIGURACAO`; a tela consome os mesmos contratos tanto em mocks quanto na API real.

Vagas e ocupação são **configuração local** no SQLite; o provider do AGHU real segue reservado e **nenhum agendamento é prometido no AGHU**. `ATIVO` e `PROPOSTO` ocupam vaga e bloqueiam choque do mesmo paciente. A distância usa OpenStreetMap (Nominatim + OSRM), sem chave paga, com cache, timeout e `User-Agent`; o endereço do formulário é dado sensível, criptografado em repouso e nunca exposto em logs, auditoria ou respostas da API — a tela mostra apenas cidade/UF e distância em km.

Os contratos HTTP implantados estão em `05-interfaces.md`; os demais contratos de domínio permanecem documentados para entregas seguintes. As telas operacionais (Fila, Painel, Relatórios, Critérios e Equipe) continuam usando o adaptador de mocks, controlado por `VITE_USE_MOCKS` (`frontend/.env.example`, documentado em `06-arquitetura.md`). A sugestão automática segue a decisão da gestão: prioridade clínica e vagas como critérios principais, compatibilidade e tempo de espera na sequência, e distância apenas como desempate — nunca substituindo prioridade.

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
- Proteger toda rota de dados com `Depends(auth_handler.decode_token)` no roteador; a única exceção pública é `POST /api/integracoes/forms/webhook`, protegida por HMAC-SHA256, timestamp e nonce. No frontend, declarar `meta.roles` e tratar a autorização no backend como fonte de verdade, inclusive nas rotas administrativas de vagas e nas mutações de agendamento.
- Registrar mudanças de critérios, perfis e solicitações via `registrar_auditoria()` com `dados_anteriores`, `dados_novos`, `ip_origem` e categoria.
- Executar o auditor de conformidade ao final de cada entrega. O script `audit_framework.py` possui um defeito conhecido na função `colorize()` (`ENDC` não qualificado) que **não deve ser corrigido nesta entrega**; executá-lo por shim em memória:
  `python -c "import audit_framework as a; a.ENDC=''; a.FrameworkAuditor('.').run()"`

**A IA NÃO DEVE:**
- Criar dependências externas não documentadas em `06-arquitetura.md`. Na v0.6.0 as **únicas dependências npm autorizadas** continuam sendo os cinco pacotes FullCalendar v6 (`core`, `vue3`, `daygrid`, `timegrid`, `interaction`); nenhum pacote premium ou outra biblioteca de calendário é permitida. O backend **não adiciona pacote**: `httpx>=0.27` já faz parte do projeto. Gráficos do painel seguem em SVG/CSS.
- Implementar exclusão física de registros (usar `deleted_at`).
- Burlar o sistema RBAC; esconder controles no frontend nunca substitui a validação no backend.
- Alterar manualmente a prioridade individual de solicitações na tela do operador (RN-02); exceções são exclusivas da Área Gestora e exigem justificativa (RN-03).
- Corrigir `audit_framework.py`, `src/main.py` ou demais arquivos de infraestrutura sem instrução explícita neste `SPEC.md`.
- Prometer recursos não implementados: agendamento real no AGHU, provider `FORMS_API` funcional ou tag de produção. `FORMS_API` e `AGHU` são apenas pontos de extensão reservados; a v0.6.0 registra reservas, confirmações e configuração de vagas operacionais no banco local e não envia marcação ao AGHUX.
- Expor endereço completo do paciente (CEP, logradouro, número, complemento, bairro) em resposta, auditoria ou log, ou inventar coordenadas/distância quando o provedor de geocoding falhar.

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

### Fase 4 — Backend de integração (concluída na v0.2.0)
- [x] [TASK-024] Implementar models, providers, controllers e routers protegidos; integração real com formulário externo e AGHUX; notificações e regras de cancelamento/reagendamento. **Concluída no escopo da v0.2.0** quanto aos models/providers/controllers/routers da integração Forms → AGHUX. Notificações, cancelamento/reagendamento e o provider `AGHU` real **não foram implementados** nessa versão; cancelamento/reagendamento são entregues na Fase 5, e notificações e o provider `AGHU` permanecem para entrega futura.
- [x] [TASK-026] Criar os modelos `forms_responses`, `webhook_nonces`, `solicitacoes`, `solicitacao_itens_exame`, `divergencias` e `alertas`, com a migração Alembic `c4f1a7d9e2b3` (revises `8a2efbe37bb6`).
- [x] [TASK-027] Definir `FormsProviderInterface` (Mock, Power Automate e `FORMS_API` reservado) e `AghuxProviderInterface` (`AghuxJsonProvider` sobre a fixture de 576 itens / 493 solicitações e `AghuProvider` reservado), com fábricas em `src/dependencies.py`.
- [x] [TASK-028] Proteger o webhook com HMAC-SHA256 sobre `timestamp . nonce . corpo_bruto`, cabeçalhos `X-SAE-Timestamp`, `X-SAE-Nonce` e `X-SAE-Signature`, janela `WEBHOOK_MAX_SKEW_SECONDS` e nonce único anti-replay; documentar a exceção pública ao default-private.
- [x] [TASK-029] Expor `POST /api/integracoes/forms/webhook`, `GET /api/integracoes/forms/eventos` e `POST /api/integracoes/forms/eventos/{responseId}/reprocessar`, com processamento em `BackgroundTasks`, idempotência e RBAC nos endpoints administrativos.
- [x] [TASK-030] Criptografar CPF/CNS com AES-GCM via `cryptography`, manter hashes HMAC para deduplicação, máscara nos últimos 4 dígitos e nenhum dado sensível em logs, auditoria ou respostas da API.
- [x] [TASK-031] Entregar a tela `/integracoes` no grupo **Sistema** (`AREA_GESTORA`/`ADMIN_TI`) para listar eventos e reprocessar falhas/duplicidades, mantendo o fallback de versão `v0.2.0` no frontend.
- [x] [TASK-032] Validar a entrega: 18 testes pytest (9 anteriores + 9 novos), `npm run build` e auditoria 11/11 via shim em memória.

### Fase 5 — Gestão de agendamentos, calendário e distância (v0.3.0)
- [x] [TASK-033] Decidir as quatro premissas com a gestão: vagas em configuração local, distância via OSM/Nominatim+OSRM, calendário com FullCalendar e sugestão por prioridade + vagas + compatibilidade + espera, com distância como desempate. Nenhuma tag de produção.
- [x] [TASK-034] Criar a migração Alembic `e7c1a9d4b3f2` (revises `c4f1a7d9e2b3`) e os models `agenda_slots`, `agendamentos`, `contatos_paciente` e `paciente_enderecos`, com `deleted_at`, índices e `solicitacoes.paciente_chave` derivado por HMAC.
- [x] [TASK-035] Definir `SlotProviderInterface` (`LocalSlotProvider`, `AghuSlotProvider` reservado) e `DistanceProviderInterface` (`OpenStreetMapDistanceProvider`, `MockDistanceProvider` somente em testes), com fábricas em `src/dependencies.py`, cache, timeout e `User-Agent` configuráveis.
- [x] [TASK-036] Implementar validação de divergências, registro de contato e as regras de agendar/remarcar/cancelar do controller: aceite prévio (RN-07), divergências tratadas (RN-04), sem choque para o mesmo paciente (RN-05), capacidade da vaga local, justificativa obrigatória, devolução de vaga na mesma transação e auditoria `NEGOCIO_CLINICO` com IP e antes/depois.
- [x] [TASK-037] Implementar a sugestão automática: filtros duros de vaga livre, data futura, compatibilidade de exame/unidade e ausência de conflito; score `0..100` com pesos `35/15/20/20/10` configuráveis por ambiente, distância apenas como desempate.
- [x] [TASK-038] Expor os endpoints protegidos de calendário, histórico/busca de paciente, sugestões, mutações e administração de vagas, com RBAC no backend (`COORDENACAO` somente leitura; `GLO-SEC-HCPE-SETISD` equiparado a `ADMIN_TI`).
- [x] [TASK-039] Entregar a tela `/agendamentos` com FullCalendar (mês/semana), ocupação por vaga, painel do paciente com histórico, remarcação por arrastar ou botão (sempre com justificativa), modal de sugestões e gestão de vagas para Área Gestora/Admin TI, preservando os interceptadores do Axios e os componentes reutilizáveis.
- [x] [TASK-040] Ampliar `FORMS_FIELD_MAP` com apelidos de endereço, criptografar CEP/logradouro/número/complemento/bairro em `paciente_enderecos`, calcular distância até o hospital e garantir que nenhum campo de endereço apareça em logs, auditoria ou respostas da API. Sem endereço no formulário, nenhuma distância é inventada.
- [x] [TASK-041] Validar a entrega: 33 testes pytest (18 anteriores + 15 novos em `tests/test_agendamentos.py`), `npm run build`, importador AGHUX, auditoria 11/11 via shim em memória e bump da versão para `v0.3.0`.

### Fase 6 — Rotina da Central de Marcação e propostas (v0.4.0)
- [x] [TASK-041] Reorganizar `/fila` com as colunas padrão `#`, `Prioridade`, `Paciente / Prontuário`, `Unidade solicitante`, `Exame(s)`, `Status` e `Tempo na fila`; menu `Colunas` com caixas de seleção persistidas em `localStorage` e filtro adicional por unidade solicitante (RF005/RF007).
- [x] [TASK-043] Substituir a "Conferência" campo a campo por "Dados cadastrados no AGHUX": somente campos presentes no export, divergências pendentes em seção condicional e botão **Efetuar marcação** que leva ao calendário com solicitação e busca preenchidas (RF007/RF010).
- [x] [TASK-044] Ajustar `/agendamentos` para não listar solicitações na abertura: busca sob demanda, exame específico como filtro duro das vagas/sugestões, clique no dia com popup de horários e marcação direta, com pré-condições validadas no backend (RN-04/RN-05/RN-07/RN-09).
- [x] [TASK-045] Simular os próximos 30 dias com propostas `PROPOSTO` passíveis de confirmação em um clique, não confirmação com justificativa, remarcação/cancelamento, novos status de solicitação, RBAC e auditoria; estender a suíte para 38 testes, validar build/importador/auditoria e atualizar a versão para `v0.4.0`.

### Fase 7 — Fila de propostas e disponibilidade pela Chefia (v0.5.0)
- [x] [TASK-046] Corrigir a simulação dos mocks e do backend para contabilizar cada proposta gerada antes de escolher a vaga seguinte, respeitando capacidade, compatibilidade do exame, choque do mesmo paciente e distribuição entre dias.
- [x] [TASK-047] Publicar/as consumir as propostas pendentes no formato da fila de marcação (`PropostaAgendamentoFila`), ordenadas por prioridade, espera e protocolo, com os novos endpoints `GET /api/agendamentos/propostas` e o campo `propostas` na simulação.
- [x] [TASK-048] Permitir que `CHEFIA` crie e edite vagas (unidade, exame, horário, capacidade e situação) no backend e na tela `/agendamentos`, mantendo auditoria `CONFIGURACAO`; estender a suíte para 41 testes e atualizar a versão para `v0.5.0`.

### Fase 8 — Redesenho da gestão de vagas (v0.6.0)
- [x] [TASK-049] Reorganizar `GestorVagas.vue` com uma linha superior de seleção de exames e um calendário FullCalendar v6 inferior para selecionar o dia, preservando os interceptadores do Axios e os componentes reutilizáveis do framework (RF009/RF012).
- [x] [TASK-050] Permitir acrescentar e remover vagas arbitrariamente na data selecionada, com horário, unidade, exame, capacidade e situação; a remoção usa `DELETE /api/admin/agenda/slots/{id}` com soft delete, bloqueio para vagas ocupadas e auditoria `CONFIGURACAO` (RN-03/RF006/RF013).
- [x] [TASK-051] Implementar `POST /api/admin/agenda/copiar-semana` para replicar as vagas de uma semana para outra (mesmo dia da semana, horário, unidade, exame, capacidade e situação), de forma idempotente e com auditoria `CONFIGURACAO`; expor a operação também nos mocks e na tela (RF012/RF013).
- [x] [TASK-052] Estender a suíte para 47 testes, cobrindo remoção e cópia semanal com RBAC/auditoria, validar `npm run build`, importador, auditoria arquitetural e atualizar a versão para `v0.6.0` sem criar tag.
- [x] [TASK-053] Criar `scripts/gerar_solicitacoes_simuladas.py` para acrescentar 30 solicitações fictícias e determinísticas com datas de 16 a 25/11/2026, preservadas pelo importador do CSV; reancorar `referenciaEm`, a agenda simulada e os textos das telas nessa data (RF001/RF005/RF009).
- [x] [TASK-054] Corrigir simulação para não lotar vagas já preenchidas e exibir propostas de agendamento como cards arrastáveis no calendário com drag-and-drop para ajuste de horário; implementar `POST /api/agendamentos/{id}/mover` (somente `PROPOSTO`, exame compatível, capacidade e conflito do paciente), o adaptador de mocks `moverPropostaAgendamento` e a ação na store; estender a suíte para 51 testes (RF005/RF006/RF013).
- [x] [TASK-055] Edição em lote na fila de marcação: `POST /api/agendamentos/lote` altera o status de vários agendamentos de uma só vez, com justificativa única obrigatória, todos os status elegíveis, RBAC restrito a `CHEFIA`, `AREA_GESTORA` / `GESTÃO`, `ADMIN_TI` e `GLO-SEC-HCPE-SETISD`, auditoria `NEGOCIO_CLINICO` por item, confirmação via modal e popup temporário com opção de reverter no frontend; estender a suíte para 55 testes (RF005/RF013).
- [x] [TASK-056] Regras de negócio da Fila de Marcação: novo status `NAO_CONFIRMADO`; verificação automática de 24h (`AGUARDANDO_CONFIRMACAO` → `NAO_CONFIRMADO`, agendamento → `CANCELADO`) ao carregar a fila; ações da coluna "Ação" por status (RECEBIDA=Agendar, PENDENTE_CORRECAO=nenhuma, AGUARDANDO_CONTATO=nenhuma, AGUARDANDO_CONFIRMACAO=Cancelar, NAO_CONFIRMADO=Cancelar, AGUARDANDO_REAGENDAMENTO=Agendar/Cancelar, AGENDADA=Reagendar/Cancelar); endpoints `GET /api/fila`, `POST /api/solicitacoes/{id}/agendar`, `POST /api/solicitacoes/{id}/cancelar`, `POST /api/solicitacoes/{id}/reagendar`; abertura da solicitação por clique na linha (botão "Abrir" removido da coluna Ação).
- [x] [TASK-057] Corrigir o agendamento de solicitações `RECEBIDA` (RN-07 / ponto de decisão 11): `agendar_da_fila` deixa de exigir aceite prévio e status pós-contato, mantendo o bloqueio por divergência pendente (RN-04); no calendário, "Marcar paciente" de uma solicitação recebida usa `POST /api/solicitacoes/{id}/agendar`; o botão "Agendar" da fila leva ao calendário com a solicitação selecionada em vez de pedir o ID da vaga; o botão "Buscar solicitação" deixa de enviar o evento de clique como termo. Três testes novos em `tests/test_agendamentos.py`.

## 5. Critérios de Verificação Global
- [x] `npm run build` conclui sem erros de tipo (`vue-tsc`) para o frontend.
- [x] Auditoria arquitetural: 11/11 (100%, EXCELENTE) com o comando via shim da Seção 3.
- [x] `uv run pytest` sem regressões: **55 testes aprovados**, cobrindo HMAC válido/inválido, skew, replay, idempotência, RBAC, reprocessamento, alerta sem correspondência no AGHUX, cripto, capacidade, conflito do mesmo paciente, transições de contato, simulação de propostas distribuída e ordenada por prioridade, confirmação/não confirmação, movimento de proposta com validação de vaga/exame/RBAC, edição em lote de status com RBAC, justificativa única e auditoria por item, simulação com múltiplos exames por solicitação e campo `deFora` para vagas insuficientes, remarcação/cancelamento com devolução de vaga, sugestão com exame específico, criação/edição/remoção de vagas pela Chefia, cópia semanal idempotente, geração reproduzível do cenário recente, cards de proposta com drag-and-drop, busca sem PHI e não exposição de endereço.
- [x] Nenhuma mutação de tela sem registro correspondente no histórico simulado; as mutações da integração e da agenda são gravadas em `audit_logs` com estado anterior/posterior, IP de origem e categoria (`NEGOCIO_CLINICO` para agendamentos e propostas, `CONFIGURACAO` para vagas).
- [x] Nenhum CPF/CNS inventado nos mocks ou nos provedores: o export AGHUX não contém esses campos e um formulário sem CPF/CNS não inventa valores; quando informados, são criptografados com AES-GCM, com hash HMAC para deduplicação e máscara `***` nos últimos 4 dígitos, nunca em claro em payload, auditoria, logs ou respostas da API. O mesmo vale para o endereço do formulário, cifrado em `paciente_enderecos` e nunca devolvido pela API.
- [x] Dependências explicitamente autorizadas e documentadas em `06-arquitetura.md`: `cryptography>=41` no backend e os cinco pacotes FullCalendar v6 no frontend. Nenhuma outra dependência foi adicionada; `httpx>=0.27` já estava no projeto.
- [x] Agendamentos `ATIVO` e propostas `PROPOSTO` respeitam capacidade da vaga local e bloqueiam choque do mesmo paciente; execuções sucessivas da simulação não reaproveitam vagas já reservadas por propostas, as linhas geradas são distribuídas entre dias e a fila de propostas segue a ordem de prioridade. Toda remarcação/cancelamento exige justificativa e devolve a vaga anterior na mesma transação, e somente a confirmação do operador transforma uma proposta em agendamento ativo.
- [x] A Chefia da Central cria, edita, remove e copia entre semanas a disponibilidade de exames/vagas com auditoria `CONFIGURACAO`, sem elevar `COORDENACAO` nem permitir acesso anônimo às rotas administrativas; a remoção preserva o histórico por soft delete e bloqueia vagas com agendamentos ativos ou propostas.
- [x] A fila expõe as sete colunas padrão e permite mostrar/ocultar colunas arbitrariamente; o painel da solicitação mostra apenas dados do AGHUX e esconde a seção de divergências quando não há pendências; o calendário não lista solicitações antes da busca e usa o exame específico como filtro duro.
- [x] Importador AGHUX segue gerando 576 itens → 493 solicitações sem CPF/CNS e preserva as 30 solicitações simuladas de `scripts/gerar_solicitacoes_simuladas.py` (semente fixa, datas de 16 a 25/11/2026, sem CPF/CNS/endereço); o calendário em mocks usa `referenciaEm` apenas para demonstração, sem inventar endereço ou distância real.
