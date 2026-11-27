# Especificação de Requisitos

## 1. Requisitos Funcionais (RF)

| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :---: |
| **RF001** | Autenticação Corporativa e RBAC | Permitir login interno via AD/LDAP Ebserh (ou Mock em desenvolvimento) com autorização por perfis locais (`ADMINISTRADOR`, `GESTOR_CENTRAL`, `MARCADOR`, `CONSULTA`) e consulta prévia ao AD na tela de Configurações. | Essencial |
| **RF002** | Leitura de Solicitações do AGHU (Multi-Provedor) | Consultar solicitações de exames do AGHU em modo **somente leitura** via camada Provider desacoplada (`CSV` em desenvolvimento com base no arquivo oficial do Drive; `PostgreSQL` em produção com SQL nativo), identificando o paciente por `prontuario` e `codigo_solicitacao` (sem exigir CPF obrigatório). | Essencial |
| **RF003** | Importação e Higienização da Planilha do Google Forms | Permitir o upload/importação da planilha exportada pelo Google Forms (CSV/XLSX) **sem modificar o arquivo original**, cruzando automaticamente cada registro com o AGHU para: (a) validar existência do `codigo_solicitacao`; (b) sinalizar divergência entre o exame escolhido no Forms e o pedido médico real no AGHU; (c) detectar duplicidades (múltiplos envios do paciente ou múltiplos médicos solicitando o mesmo exame); e (d) sinalizar exames já agendados/realizados. | Essencial |
| **RF004** | Busca Ativa por Prontuário para Correção de Erros | Permitir que a marcadora pesquise no espelho do AGHU pelo número do `prontuario` ou nome do paciente quando o `codigo_solicitacao` preenchido no Forms for inválido, vinculando manualmente a solicitação correta à fila sem perder a rastreabilidade. | Essencial |
| **RF005** | Fila de Marcação com Priorização Clínica Determinística | Exibir a fila de exames higienizada e ordenada automaticamente por um **score determinístico e explicável** (exibindo o motivo da posição), baseado nos pesos configuráveis (padrão inicial: Oncologia → Transplante → Nefrologia/Hemodiálise → Vulneráveis [gestantes, crianças/Pediatria, idosos] → Rotina), afinidade entre clínica solicitante e exame, e proximidade da data de retorno. | Essencial |
| **RF006** | Filtros Operacionais e Filtro Geográfico de Urgência | Permitir filtrar a fila por exame, unidade executora/solicitante, clínica solicitante, status operacional, busca por prontuário/solicitação e **filtro geográfico por município/região (Capital, RMR, Interior / TFD)** acionável para vagas de última hora (amanhã/depois de amanhã), sem alterar o score de prioridade clínica. | Essencial |
| **RF007** | Motor de Alertas de Conflito, Preparo e Janela de Retorno | Analisar automaticamente exames pendentes/agendados do mesmo paciente e emitir alertas visuais para: (a) combinações incompatíveis (mesmo dia ou interferência de preparo, ex: colonoscopia × sangue; ressonância × oftalmologia); (b) janelas de retorno (ex: espirometria até 10 dias antes; INR até 72h); (c) antecedência mínima de preparo; e (d) particularidades clínicas (ex: diabéticos cedo para jejum; alerta mamografia +40 anos). | Essencial |
| **RF008** | Monitoramento de Confirmação em 24h e Controle de Status | Permitir atualizar o ciclo de vida interno de cada solicitação seguindo o fluxo ideal validado em 06/11 (`Na Fila` → `Aguardando Confirmação 24h` → `Confirmado / Agendado no AGHU` ou `Sem Resposta 24h / Cancelado`), calculando automaticamente o vencimento das 24 horas para liberação da vaga, registrando data/hora agendada no AGHU, orientações de preparo enviadas e observações internas. | Essencial |
| **RF009** | Cadastro Configurável de Regras de Exames e Pesos | Disponibilizar interface administrativa (para `ADMINISTRADOR` e `GESTOR_CENTRAL`) para criar, editar e desativar (soft delete) sem alteração de código: (a) pesos e grupos de prioridade clínica; (b) regras por exame (preparo, antecedência mínima, janela de retorno, exigência de jejum, faixa etária); e (c) matriz de incompatibilidades entre exames (par A × B + intervalo mínimo em dias). | Essencial |
| **RF010** | Painel Gerencial de Indicadores (KPIs) | Exibir dashboard em tempo real com métricas gerenciais: volume da fila por exame/unidade, tempo médio de espera e resposta, taxa de confirmação no prazo de 24h, taxa de solicitações duplicadas ou divergentes barradas na higienização e distribuição geográfica/TFD. | Importante |

### 📌 Legenda de Níveis de Prioridade
- **Essencial (Alta):** Funcionalidade indispensável para o MVP e entrada em produção.
- **Importante (Média):** Funcionalidade de alto valor gerencial que complementa a operação principal.
- **Desejável (Baixa):** Melhoria complementar para sprints futuras.

---

## 2. Requisitos Não Funcionais (RNF)

| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| **RNF001** | Segurança & Sessão | Tokens JWT assinados (HS256) com Refresh Tokens em Cookies `HttpOnly` e auto-renovação transparente via interceptador Axios. |
| **RNF002** | LGPD & Auditoria | Trilha de auditoria imutável (`audit_logs`) obrigatória em todas as mutações (status da fila, importações, edição de regras/pesos, gestão de usuários), registrando `usuario`, `categoria`, `dados_anteriores`, `dados_novos` e `ip_origem`. Proibido Hard Delete (usar `deleted_at`). |
| **RNF003** | Segurança HTTP | Middleware obrigatório de Security Headers (`nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Cache-Control: no-store, no-cache`, `Pragma: no-cache`) e *Default-Private Router Pattern* em todos os roteadores clínicos. |
| **RNF004** | Governança de Segredos | Proibição total de hardcode de credenciais; validação centralizada em `src/config.py` e placeholders em `.env.example`. |
| **RNF005** | Somente Leitura no AGHU | Proibição absoluta de operações de escrita (`INSERT`, `UPDATE`, `DELETE`) no PostgreSQL do AGHU; toda persistência da aplicação ocorre exclusivamente no SQLite local (`data/app.db`). |
| **RNF006** | Determinismo e Explicabilidade | Dado o mesmo conjunto de solicitações e a mesma tabela de pesos, o algoritmo de priorização deve produzir exatamente a mesma ordem e retornar os motivos explícitos da pontuação de cada item. |
| **RNF007** | Conformidade Arquitetural | Aderência de 100% aos 11 pilares do `Framework-SETISD-HC-UFPE` (`audit_framework.py`), versionamento SemVer (`vX.Y.Z`) visível no rodapé e suíte automatizada `pytest`. |
| **RNF008** | Resiliência e Monitoramento | Endpoint público `GET /api/health` compatível com Zabbix mantendo status saudável mesmo em modo desenvolvimento offline (sem PostgreSQL AGHU conectado). |

---

## 3. Detalhamento SDD (CARE)

### [CARE-RF002] Leitura Multi-Provedor do AGHU (`CSV` ↔ `PostgreSQL`)
* **Context (Contexto):** O hospital bloqueia acesso direto ao PostgreSQL durante o desenvolvimento; o arquivo `consulta_aghu_exames.sql` e o CSV anonimizado do Drive definem as 12 colunas reais (`prontuario`, `nome`, `telefone`, `cidade`, `estado`, `codigo_solicitacao`, `data_solicitao`, `unidade_solicitante`, `codigo_exame`, `nome_exame`, `id_funcionario`, `nome_funcionario`).
* **Action (Ação):** Implementar `ExameProviderInterface`, `ExameCsvProvider` (com normalização das linhas com aspas duplas do CSV do Drive e tratamento de `prontuario` nulo) e `ExamePostgresProvider` (executando SQL puro em `src/providers/sql/exames/`), injetados via fábrica `get_exame_provider(STRATEGY)` em `src/dependencies.py`.
* **Result (Resultado):** Endpoints protegidos retornam as solicitações normalizadas de forma idêntica tanto em `STRATEGY = "csv"` quanto em `STRATEGY = "postgres"`.
* **Evaluation (Avaliação):** Testes `pytest` validam leitura dos registros do CSV oficial, busca por `codigo_solicitacao` e busca ativa por `prontuario`, com 100% de aprovação.

### [CARE-RF003] Importação e Higienização `Forms × AGHU`
* **Context (Contexto):** Pacientes continuam enviando pedidos via Google Forms; a planilha exportada pode conter erros de código, exame divergente do pedido médico e duplicidades.
* **Action (Ação):** Criar endpoint `POST /api/importacoes/forms` protegido por autenticação que faz o parsing de CSV/XLSX, cruza cada linha com o `ExameProviderInterface` (AGHU) e grava em `acompanhamento_fila` o resultado da higienização (`VALIDA`, `DIVERGENCIA_EXAME`, `SOLICITACAO_NAO_ENCONTRADA`, `DUPLICADA`), registrando auditoria (`NEGOCIO_CLINICO`).
* **Result (Resultado):** Relatório de importação retornado com contadores (importadas, duplicadas, divergentes, não encontradas) e itens válidos disponíveis imediatamente na fila.
* **Evaluation (Avaliação):** Teste automatizado envia CSV sintético contendo 1 pedido válido, 1 duplicado, 1 com exame divergente e 1 com código inexistente; todos os 4 cenários devem ser classificados corretamente e auditados em `audit_logs`.

### [CARE-RF005] Motor de Priorização Clínica Configurável
* **Context (Contexto):** Tabelas locais `regras_prioridade` e `acompanhamento_fila` populadas no SQLite.
* **Action (Ação):** Implementar serviço/controller puro que calcula o `score_prioridade` e lista `motivos_prioridade` a partir dos pesos cadastrados em `regras_prioridade` (Oncologia, Transplante, Hemodiálise/Nefrologia, Vulneráveis, afinidade especialidade × exame, proximidade do retorno e tempo de espera como desempate).
* **Result (Resultado):** `GET /api/exames/fila` retorna a fila ordenada de forma determinística com `score_prioridade` e `motivos_prioridade` preenchidos, respeitando filtros opcionais (incluindo município/região para urgências).
* **Evaluation (Avaliação):** Testes unitários comprovam que: (1) Oncologia supera rotina mesmo com solicitação mais recente; (2) alterar um peso via `PUT /api/regras/prioridades/{id}` altera a ordenação imediatamente sem reiniciar o servidor; (3) aplicar filtro geográfico não altera o score clínico dos itens.

### [CARE-RF007] Detector de Conflitos, Preparo e Janelas de Retorno
* **Context (Contexto):** Tabelas `regras_exames` e `incompatibilidades_exames` configuradas no SQLite.
* **Action (Ação):** Ao listar a fila ou abrir o detalhe de uma solicitação, cruzar os demais exames do mesmo `prontuario` contra `incompatibilidades_exames` e validar a data alvo contra `regras_exames` (ex: espirometria ≤ 10 dias antes do retorno; INR ≤ 72h; antecedência mínima de preparo).
* **Result (Resultado):** API devolve lista estruturada de `alertas` (`INCOMPATIBILIDADE`, `JANELA_RETORNO`, `ANTECEDENCIA_PREPARO`, `JEJUM_CLINICO`, `DUPLICIDADE`) exibidos como badges na interface Vue 3.
* **Evaluation (Avaliação):** Testes unitários validam detecção de par incompatível (colonoscopia + sangue), estouro de janela de espirometria (>10 dias / pós-retorno) e alerta de INR (>72h).

### [CARE-RF008] Monitoramento de Confirmação em 24h e Status Interno
* **Context (Contexto):** Alinhamento de 06/11 define que a confirmação de disponibilidade do paciente em até 24h ocorre **antes** da marcação definitiva no AGHU.
* **Action (Ação):** Criar endpoint `PATCH /api/exames/fila/{id}/status` para transitar entre estados (`NA_FILA`, `AGUARDANDO_CONFIRMACAO_24H`, `CONFIRMADO_AGENDADO_AGHU`, `SEM_RESPOSTA_24H`, `CANCELADO`), salvando `contato_iniciado_em`, `prazo_confirmacao_em` (+24h), `data_agendada_aghu`, `preparo_orientado` e registrando `dados_anteriores` / `dados_novos` em `audit_logs`.
* **Result (Resultado):** Itens com prazo de 24h vencido são destacados automaticamente na interface para liberação da vaga ao próximo da fila.
* **Evaluation (Avaliação):** Teste valida transição completa de status, cálculo exato de `+24h`, detecção de expiração e persistência do log em `audit_logs` com IP e usuário.

### [CARE-RF009] Gestão Configurável de Regras e Pesos
* **Context (Contexto):** Requisito obrigatório do SETISD (Tiago Ferrão) para evitar regras hardcoded.
* **Action (Ação):** Expor endpoints CRUD (`GET/POST/PUT/DELETE` com soft delete) em `/api/regras/prioridades`, `/api/regras/exames` e `/api/regras/incompatibilidades`, restritos a perfis `ADMINISTRADOR` e `GESTOR_CENTRAL`, com auditoria categoria `CONFIGURACAO`.
* **Result (Resultado):** Gestores atualizam pesos, preparos e incompatibilidades diretamente pela tela Vue 3, refletindo de imediato na fila.
* **Evaluation (Avaliação):** Testes validam bloqueio `403` para perfil `CONSULTA`, sucesso `200/201` para `GESTOR_CENTRAL`/`ADMINISTRADOR`, soft delete (`deleted_at` preenchido, sem `DELETE` SQL) e registro em `audit_logs`.
