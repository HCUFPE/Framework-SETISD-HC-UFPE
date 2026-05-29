# Especificação de Requisitos

## 1. Requisitos Funcionais (RF)

| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| RF001 | Autenticação LDAP/AD | Login via LDAP/AD do HC com emissão de JWT de curta duração e refresh token HttpOnly. | Essencial |
| RF002 | Fila de Atendimento | Listagem de pacientes do dia com status, tipo de entrada, tempo de espera e ações de transição. | Essencial |
| RF003 | Briefing Clínico | Visão pré-consulta com alertas ativos, linha do tempo de consultas, última antropometria e padrão de condutas. | Essencial |
| RF004 | Formulário de Consulta | Registro digital da consulta com timer, dados antropométricos, anamnese, exame físico por sistema, marcos de desenvolvimento, M-CHAT-R (para 16–30 meses), diagnóstico CID-10/SID, procedimentos e encaminhamentos. | Essencial |
| RF005 | Exportação AGHU | Geração de texto estruturado para copiar e colar na evolução do AGHU; geração de ficha de encaminhamento imprimível. | Essencial |
| RF006 | Caderneta Digital | Histórico longitudinal de crescimento: curvas de peso, altura e IMC com percentis. | Alta |
| RF007 | Dashboard Gerencial | KPIs operacionais: consultas realizadas, tempo médio, taxa de encaminhamentos, formulários incompletos, alertas populacionais, CIDs mais frequentes, efetividade de encaminhamentos. | Alta |
| RF008 | Alertas Populacionais | Geração automática de alertas por categoria (peso, marco, encaminhamento, falta, negligência) com nível crítico ou atenção. | Alta |
| RF009 | Registro de Dados Externos | Inclusão de dados de atendimentos realizados fora do HC (UBS, clínicas) com rastreabilidade de origem obrigatória. | Média |
| RF010 | Gestão de Usuários | Cadastro e RBAC de usuários baseado nos grupos do AD (médico_hc, médico_satélite, recepção, gestão). | Média |

---

## 2. Requisitos Não Funcionais (RNF)

| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF001 | Segurança | JWT de 15 minutos + refresh token HttpOnly com rotação. Sem segredos no código — uso obrigatório de `.env`. |
| RNF002 | LGPD | Auditoria de acesso a dados sensíveis. Soft delete obrigatório (`deleted_at`). Sem exclusão física de registros. |
| RNF003 | Autenticação | LDAP3 contra o AD do HC. Grupos do AD mapeados para roles do sistema. |
| RNF004 | Integração AGHU | Exportação via texto estruturado (copy-paste). Integração via Provider dedicado quando API estiver disponível. |
| RNF005 | Performance | Resposta de API em até 500ms para listas paginadas. Timer de consulta visível em tempo real. |
| RNF006 | Disponibilidade | Fallback para CSV em desenvolvimento; PostgreSQL em produção. |

---

## 3. Detalhamento SDD (CARE)

### [CARE-RF001] Autenticação LDAP/AD

* **Context:** Servidor LDAP do HC configurado. Credenciais de serviço em variáveis de ambiente (`.env`). Backend rodando com `ldap3` e `PyJWT`.
* **Action:** Endpoint `POST /api/login` recebe `username` e `password` via form. Autentica contra o AD via `ldap3`. Em sucesso, emite JWT (15min) e, se `remember_me=true`, persiste refresh token HttpOnly no banco (`refresh_tokens`).
* **Result:** JWT retornado no body; refresh token em cookie HttpOnly. Código 401 em falha de credenciais. Grupos do AD incluídos no payload JWT.
* **Evaluation:** Testar com credencial válida, inválida e com `remember_me`. Verificar que o cookie é HttpOnly e que o JWT expira em 15min.

---

### [CARE-RF002] Fila de Atendimento

* **Context:** Pacientes agendados para o dia, obtidos do AGHU ou CSV de desenvolvimento.
* **Action:** Endpoint `GET /api/pacientes` retorna lista com `id`, `name`, `birthDate`, `age`, `ageInMonths`, `record`. Frontend monta `QueueEntry` com `status`, `entryType`, `waitTime` e `faltas`.
* **Result:** Lista renderizada com badge de status e tipo de entrada. Transição de status gera registro no banco.
* **Evaluation:** Verificar que os 4 tipos de entrada são exibidos corretamente e que a transição de status persiste.

---

### [CARE-RF003] Briefing Clínico

* **Context:** Médico seleciona paciente na fila antes de iniciar o atendimento.
* **Action:** Tela exibe: dados do paciente (nome, idade, prontuário), alertas ativos categorizados, linha do tempo das últimas consultas (HC + externos), padrão de condutas (CIDs frequentes, encaminhamentos sem retorno, internações), últimos dados antropométricos com sparkline de peso.
* **Result:** Médico tem contexto completo antes de entrar na consulta. Botão "Iniciar Atendimento" ativa timer e redireciona para o formulário.
* **Evaluation:** Verificar que alertas críticos são exibidos com ícone `AlertOctagon` (vermelho) e alertas de atenção com `AlertTriangle` (âmbar). Verificar que consultas externas aparecem diferenciadas na linha do tempo.

---

### [CARE-RF004] Formulário de Consulta

* **Context:** Paciente com atendimento iniciado (timer ativo). Médico autenticado.
* **Action:** Formulário em abas: (1) Antropometria — peso, altura, perímetro cefálico, IMC calculado automaticamente e percentil estimado; (2) Anamnese — queixa principal, alimentação (select), sono (select com alerta para ronco/apneia), higiene; (3) Exame Físico — chips selecionáveis por sistema (9 sistemas), status Normal/Alterado, campos condicionais para fontanelas (≤18 meses) e reflexos primitivos (≤12 meses); (4) Marcos do Desenvolvimento — tabela por faixa etária com janela de avaliação; (5) M-CHAT-R — 20 questões, apenas para 16–30 meses, encaminhamento automático se risco médio ou alto; (6) Encaminhamentos — especialidade, procedimento, prioridade (Eletivo/Prioritário/Urgente), justificativa. Diagnóstico (CID-10 principal + até 5 secundários + SID) fixo fora das abas.
* **Result:** Consulta registrada. Texto estruturado gerado para exportação ao AGHU. Ficha de encaminhamento gerada por especialidade.
* **Evaluation:** Verificar cálculo automático de IMC, percentil estimado, lógica M-CHAT-R (score ≤2 = baixo, 3–7 = médio, ≥8 = alto), encaminhamento automático ao completar M-CHAT com risco não-baixo. Verificar que CID-10 é obrigatório para encaminhamentos.

---

### [CARE-RF007] Dashboard Gerencial

* **Context:** Usuário com role `gestão` autenticado.
* **Action:** Tela exibe KPIs (cards), gráfico de barras de consultas por tipo de entrada por semana, gráfico de linha de tempo médio vs. meta (45min), gráfico horizontal de CIDs mais frequentes, tabela de efetividade de encaminhamentos por especialidade, tabela de alertas populacionais filtrável por categoria.
* **Result:** Visão consolidada da operação pediátrica com filtro de período (7/30/90 dias).
* **Evaluation:** Verificar que alertas de negligência disparam destaque vermelho. Verificar que taxa de retorno de encaminhamentos < 50% aparece em vermelho, 50–70% em âmbar e ≥70% em verde.
