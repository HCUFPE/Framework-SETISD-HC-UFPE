# Especificação de Requisitos

## 1. Requisitos Funcionais (RF)
| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :---: |
| RF001 | Autenticação | Login via LDAP/AD do hospital. (RN-06) | Essencial |
| RF004 | Validação Automática | Checagem dos dados após o recebimento do formulário externo, gerando alertas que indicam erros, divergências ou campos incorretos. | Essencial |
| RF005 | Fila Priorizada | Inserção de toda solicitação em fila centralizada, ordenada automaticamente por prioridade. (RN-02) | Essencial |
| RF006 | Critérios de Priorização | Cadastro e atualização das regras de priorização pela Área Gestora. | Essencial |
| RF007 | Conferência com AGHUX | Comparação dos dados do formulário com o cadastro do AGHUX, destacando divergências. (RN-04) | Essencial |
| RF008 | Validação e Assinatura | Correção e validação dos dados pelo operador, com assinatura eletrônica em cada ação. (RN-06) | Essencial |
| RF009 | Bloqueio de Duplicidade | Bloqueio de solicitações duplicadas e de agendamentos conflitantes para o mesmo paciente. (RN-05) | Essencial |
| RF010 | Contato com Paciente | Registro do contato para confirmar data e horário com o paciente (aceite, recusa ou sem resposta), depois da marcação. Sem confirmação em 24 horas, o agendamento é cancelado e a vaga liberada. (RN-07) | Essencial |
| RF011 | Efetivação do Agendamento | Marcação da solicitação recebida na agenda local antes do contato com o paciente, para garantir a vaga, sem exigir aceite prévio; divergências pendentes continuam bloqueando (RN-04). (RN-07) | Essencial |
| RF012 | Alteração de Fila | Alteração da ordem da fila pela Área Gestora, exigindo justificativa formal. (RN-03) | Importante |
| RF013 | Histórico e Auditoria | Consulta ao histórico completo de cada solicitação (quem fez, o quê e quando). (RN-08) | Essencial |
| RF014 | Painel de Gestão | Painel em tempo real com solicitações pendentes, tempo médio de validação, exames agendados, gargalos e taxa de erro. | Importante |
| RF016 | Controle de Acesso | Perfis de acesso (Área Gestora, Operador, Gestão/Coordenação) com permissões distintas. | Essencial |
| RF017 | Cancelamento e Reagendamento | Cancelamento ou remarcação de exame já efetivado, com justificativa e retorno da vaga à fila. | Desejável |
| RF018 | Recebimento de Dados Externos | Recebimento dos dados preenchidos pelo paciente em formulário externo e criação da solicitação na fila. | Essencial |
| RF019 | Notificação ao Paciente | Notificação do paciente, pelo meio de contato registrado, quando houver inconsistência nos dados enviados. | Essencial |

### 📌 Legenda de Níveis de Prioridade:
- **Essencial (Alta):** Funcionalidade indispensável para o funcionamento básico da aplicação. Sem ela, o sistema não pode ir para produção (ex: autenticação, cadastros base).
- **Importante (Média):** Funcionalidade que agrega valor significativo ao negócio e melhora o fluxo de trabalho, mas cuja ausência temporária não impede a operação mínima (ex: relatórios, filtros avançados).
- **Desejável (Baixa):** Funcionalidade complementar, melhoria estética ou recurso secundário que pode ser implementado em sprints futuras (ex: temas visuais, atalhos de teclado).

## 2. Requisitos Não Funcionais (RNF)
| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF001 | Criptografia | Tokens JWT assinados com HS256 e Cookies HttpOnly para Refresh Tokens. |
| RNF002 | LGPD / Auditoria | Trilha de auditoria obrigatória (antes/depois) em tabela `audit_logs` para mutações. |
| RNF003 | Segurança HTTP | Middleware de Security Headers (anti-cache `no-store`, `X-Frame-Options: DENY`, anti-XSS). |
| RNF004 | Governança Segredos | Proibição de hardcode e validação de env vars na inicialização (`src/config.py`). |
| RNF005 | Imutabilidade | Registros da trilha de auditoria são somente de inserção: sem edição ou exclusão. (RN-08) |
| RNF006 | Integração | Integração com o AGHUX para consulta de dados cadastrais e registro do agendamento, com tratamento de indisponibilidade. |
| RNF007 | Desempenho | Painel de gestão atualizado em tempo real; telas da fila com resposta em até 3 segundos em uso normal. |
| RNF008 | Privacidade | Coleta mínima de dados pessoais e acesso restrito por perfil, conforme a LGPD. |
| RNF009 | Usabilidade | Interface com validação do operador em poucos cliques. |

## 3. Detalhamento SDD (CARE)
Para cada requisito, a implementação deve seguir o padrão:

### [CARE-RF001] Autenticação LDAP
* **Context (Contexto)**: Servidor LDAP configurado e credenciais de serviço disponíveis.
* **Action (Ação)**: Criar middleware de autenticação que consulte o AD.
* **Result (Resultado)**: Token JWT gerado após sucesso; Código 401 em falha.
* **Evaluation (Avaliação)**: Executar `npm test tests/auth.spec.ts` (deve passar com 100% de sucesso).

### [CARE-RF004] Validação Automática
* **Context (Contexto)**: Solicitação recebida e regras de validação definidas.
* **Action (Ação)**: Criar serviço que verifique formato, obrigatoriedade e coerência dos campos após o envio.
* **Result (Resultado)**: Alertas gerados e vinculados à solicitação, indicando cada campo com erro.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_validacao.py` (deve passar com 100% de sucesso).

### [CARE-RF005] Fila Priorizada
* **Context (Contexto)**: Critérios de priorização cadastrados (RF006) e solicitação validada.
* **Action (Ação)**: Criar serviço que calcule a prioridade e insira a solicitação na fila única; criar endpoint GET `/api/fila` ordenado por prioridade.
* **Result (Resultado)**: Fila retornada em ordem de prioridade; solicitações de mesma prioridade ordenadas por data de envio.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_fila.py` (deve passar com 100% de sucesso).

### [CARE-RF006] Critérios de Priorização
* **Context (Contexto)**: Usuário autenticado com perfil de Área Gestora.
* **Action (Ação)**: Criar endpoints de cadastro e atualização das regras de priorização.
* **Result (Resultado)**: Regras persistidas com versionamento; Log de auditoria criado; Código 403 para outros perfis.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_criterios.py` (deve passar com 100% de sucesso).

### [CARE-RF007] Conferência com AGHUX
* **Context (Contexto)**: Integração com o AGHUX configurada e solicitação aberta pelo operador.
* **Action (Ação)**: Criar serviço que compare cada campo do formulário com o cadastro do AGHUX.
* **Result (Resultado)**: Lista de divergências retornada e destacada na tela; falha de integração tratada sem perda da solicitação.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_aghux_conferencia.py` (deve passar com 100% de sucesso).

### [CARE-RF008] Validação e Assinatura Eletrônica
* **Context (Contexto)**: Operador autenticado com divergências listadas.
* **Action (Ação)**: Criar endpoints de correção e validação que exijam a assinatura eletrônica do operador.
* **Result (Resultado)**: Alterações persistidas com autor, data/hora e valores antes/depois; validação bloqueada enquanto houver divergência sem tratamento.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_validacao_operador.py` (deve passar com 100% de sucesso).

### [CARE-RF009] Bloqueio de Duplicidade
* **Context (Contexto)**: Solicitações e agendamentos existentes do paciente.
* **Action (Ação)**: Criar verificação de duplicidade (paciente + exame) e de choque de horário.
* **Result (Resultado)**: Código 409 com o motivo do bloqueio; nenhuma solicitação duplicada persistida.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_duplicidade.py` (deve passar com 100% de sucesso).

### [CARE-RF010] Contato com Paciente
* **Context (Contexto)**: Solicitação validada sem divergências pendentes.
* **Action (Ação)**: Criar endpoint POST `/api/solicitacoes/:id/contatos` para registrar data, canal e resultado do contato.
* **Result (Resultado)**: Contato registrado no histórico; solicitação atualizada conforme o retorno (aceite, recusa ou sem resposta).
* **Evaluation (Avaliação)**: Executar `pytest tests/test_contato.py` (deve passar com 100% de sucesso).

### [CARE-RF011] Efetivação do Agendamento
* **Context (Contexto)**: Aceite do paciente registrado e integração com o AGHUX disponível.
* **Action (Ação)**: Criar endpoint de confirmação que registre o agendamento no AGHUX.
* **Result (Resultado)**: Solicitação com status "Agendada"; Log de auditoria criado; Código 422 se não houver aceite registrado.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_agendamento.py` (deve passar com 100% de sucesso).

### [CARE-RF012] Alteração de Fila
* **Context (Contexto)**: Usuário autenticado com perfil de Área Gestora e solicitação na fila.
* **Action (Ação)**: Criar endpoint de alteração de posição que exija o campo de justificativa.
* **Result (Resultado)**: Nova ordem persistida com justificativa e autor registrados; Código 400 sem justificativa; Código 403 para outros perfis.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_fila_alteracao.py` (deve passar com 100% de sucesso).

### [CARE-RF013] Histórico e Auditoria
* **Context (Contexto)**: Tabela `audit_logs` criada e ações do processo sendo registradas.
* **Action (Ação)**: Criar endpoint GET `/api/solicitacoes/:id/historico` para consulta da trilha completa.
* **Result (Resultado)**: Histórico retornado em ordem cronológica; tentativas de edição ou exclusão de registros rejeitadas.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_auditoria.py` (deve passar com 100% de sucesso).

### [CARE-RF014] Painel de Gestão
* **Context (Contexto)**: Solicitações e agendamentos registrados; usuário com perfil de Gestão ou Área Gestora.
* **Action (Ação)**: Criar endpoint GET `/api/painel/indicadores` e tela com os indicadores da seção 8 do documento de negócio.
* **Result (Resultado)**: Indicadores atualizados em tempo real; acesso somente de leitura.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_painel.py` e `npm test tests/painel.spec.ts` (deve passar com 100% de sucesso).

### [CARE-RF016] Controle de Acesso por Perfil
* **Context (Contexto)**: Perfis e permissões definidos na seção 6 do documento de negócio.
* **Action (Ação)**: Criar middleware de autorização que valide o perfil em cada rota.
* **Result (Resultado)**: Acesso liberado apenas às rotas do perfil; Código 403 nos demais casos.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_rbac.py` (deve passar com 100% de sucesso).

### [CARE-RF017] Cancelamento e Reagendamento
* **Context (Contexto)**: Exame efetivado e rito de cancelamento definido (ponto de decisão 6).
* **Action (Ação)**: Criar endpoint de cancelamento/remarcação que exija justificativa.
* **Result (Resultado)**: Mudança registrada no histórico; vaga devolvida à fila.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_cancelamento.py` (deve passar com 100% de sucesso).

### [CARE-RF018] Recebimento de Dados Externos
* **Context (Contexto)**: Formulário externo configurado para enviar as respostas e token de integração disponível.
* **Action (Ação)**: Criar endpoint POST `/api/solicitacoes/importacao` que receba os dados do formulário externo e crie a solicitação.
* **Result (Resultado)**: Solicitação persistida com status "Recebida" e inserida na fila; Código 401 sem token válido; Código 400 para dados malformados.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_importacao.py` (deve passar com 100% de sucesso).

### [CARE-RF019] Notificação ao Paciente
* **Context (Contexto)**: Solicitação com inconsistência detectada (RF004 ou RF007) e meio de contato registrado.
* **Action (Ação)**: Criar serviço que envie ao paciente uma mensagem indicando os dados a corrigir.
* **Result (Resultado)**: Notificação registrada no histórico; falha de envio registrada e sinalizada ao operador.
* **Evaluation (Avaliação)**: Executar `pytest tests/test_notificacao.py` (deve passar com 100% de sucesso).
