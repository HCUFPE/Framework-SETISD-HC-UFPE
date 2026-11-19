# SPEC.md - Contrato de Desenvolvimento (SDD)

## 1. Visão Geral e Resultados Esperados
Este documento é a ÚNICA fonte de verdade para a orquestração do desenvolvimento. O objetivo é construir o sistema de acompanhamento de exames da Anatomia Patológica do HC-UFPE, seguro e em conformidade com a LGPD. O sistema lê dados do AGHU sem gravar nele e substitui a planilha de controle, o livro de protocolo e as pranchetas.

### Objetivos de Alto Nível
- [x] Autenticação via LDAP/AD (fornecida pelo framework).
- [x] Trilha de auditoria nas mutações (fornecida pelo framework e usada nas features).
- [x] Receber e conferir amostras na Recepção, com nº interno gerado pelo sistema.
- [ ] Controlar perfis de acesso por função (RBAC local).
- [ ] Acompanhar o exame em todas as etapas, com filas e encaminhamento entre setores.
- [ ] Oferecer gravação assistida no AGHU, sempre feita pelo usuário.
- [ ] Oferecer consulta de status, painel de urgências e indicadores.

## 2. Contexto do Projeto (Documentação Imutável)
As definições detalhadas estão distribuídas nos seguintes documentos:
- [Validação e Fluxo de Negócio](00-validacao-negocio.md) (Fase 0 - Negócio)
- [Visão](01-visao.md)
- [Requisitos](02-requisitos.md)
- [Casos de Uso](03-casos-uso.md)
- [Modelo de Dados](04-modelo-dados.md)
- [Interfaces](05-interfaces.md)
- [Arquitetura](06-arquitetura.md)
- [Glossário](07-glossario.md)

Em caso de conflito, prevalece o [`AGENTS.md`](../../AGENTS.md).

## 3. Limites de Escopo e Guardrails (Anti-Patterns)
**A IA DEVE:**
- Seguir rigorosamente o Modelo de Dados definido em `04-modelo-dados.md`.
- Implementar testes em Pytest, na pasta `tests/`, para cada funcionalidade nova.
- Tratar o AGHU como somente leitura (RN-01).
- Chamar a aplicação de "sistema". "SAP" é o nome do serviço do hospital, não do software.

**A IA NÃO DEVE:**
- Criar dependências externas ou bibliotecas que não estejam no framework.
- Implementar exclusão física de registros (usar Soft Delete).
- Burlar o sistema de RBAC (Role-Based Access Control).
- Alterar a estrutura do framework; as features são acrescentadas pelos pontos de extensão de `docs/GUIA_DESENVOLVIMENTO.md`.

## 4. Task Breakdown (Plano de Implementação)
### Fase 1: Infraestrutura e Dados
- [x] [TASK-001] Autenticação LDAP/AD com Mock em desenvolvimento (RF001, framework).
- [x] [TASK-002] Ambiente de auditoria de logs (framework).
- [ ] [TASK-003] RBAC local com os perfis por função (RF002).

### Fase 2: Recebimento na Recepção
- [x] [TASK-004] Modelo de dados e migração do recebimento (`04-modelo-dados.md`).
- [x] [TASK-005] Leitura da solicitação por CSV no layout da `vw_solicitacao`; leitura direta no AGHU implementada, ainda não executada no banco real (`05-interfaces.md`).
- [x] [TASK-006] Busca pelo código lido ou digitado e tela única de conferência (RF003).
- [x] [TASK-007] Checklist obrigatório, único por recebimento (RF004, ajustado).
- [x] [TASK-008] Não conformidade e devolução, sem consumir nº interno (RF005).
- [x] [TASK-009] Nº interno por tipo e ano, gerado em transação (RF006, RNF013).
- [x] [TASK-010] Registro de usuário, data e hora em cada operação (RNF007) e auditoria das mutações.
- [x] [TASK-011] Trocar o CSV fictício pelo layout real exportado do AGHU, com bancada por `codigo_lab`, regra de status por item e parser da etiqueta.
- [x] [TASK-011A] Dar destino no modelo aos campos da planilha da recepção e do registro de rejeição.
- [x] [TASK-011B] Lista inicial paginada de solicitações e detalhes com todas as colunas da view.

### Fase 3: Próximas Features da Recepção
- [ ] [TASK-012] Dados complementares (RF007). Antecipados no recebimento: urgência, clínica e nº de peças. Faltam a classificação de faturamento, a edição posterior e os casos fora de HP e CO.
- [ ] [TASK-013] Etiquetas internas e ficha de trabalho (RF008, RF009).
- [ ] [TASK-014] Exame externo (RF010, RF011).
- [ ] [TASK-015] Gravação assistida no AGHU (RF012).
- [ ] [TASK-016] Encaminhamento entre setores e filas (RF013, RF014).
- [ ] [TASK-017] Responsável e edição concorrente (RF028).

## 5. Critérios de Verificação Global
- [ ] 100% de cobertura em rotas de autenticação.
- [ ] Zero vulnerabilidades críticas no lint de segurança.
- [ ] Conformidade total com os esquemas JSON/OpenAPI.
- [x] Conformidade de 100% no auditor do framework (`audit_framework.py`) ao fim da Fase 2.

## 6. Pendências
### A validar com a equipe do hospital
- **Etiqueta:** formato real, e se o código da solicitação passará de 7 dígitos. Hoje, 8 dígitos são recusados.
- **Bancada 207:** confirmar as siglas CITO, COLUT e COUT2. CITO nunca traz descrição no AGHU.
- **Status:** validar a regra adotada (recebe AC, EC, CO, AE e PE; bloqueia EX, LI e CA). Ela está na tabela `status_item_aghu`.
- **View:** schema, tipos das colunas e permissão de leitura da `vw_solicitacao`.
- **Identificação:** a view só traz iniciais, e parte dos Pacientes Externos não tem prontuário. Nesses casos, sobram as iniciais e a data de nascimento para conferir o frasco.
- **Médico solicitante:** não está na view. Hoje é digitado na não conformidade e não existe no recebimento.
- **CMCE:** quando o número é obrigatório.
- **A/E da planilha:** o sistema guarda `origem`. Ambulatório = A e Internação = E são suposição; falta definir Cirurgia e Paciente Externo.
- **Clínica de Paciente Externo:** se a recepção deve informá-la.
- **Procedimento:** como registrar em solicitações com duas siglas na mesma bancada, e se ele pode ser sugerido a partir da sigla.
- **Referência da IHQ ao HP:** hoje é opcional. Definir se será obrigatória (RF022).
- **Lacunas em `numero_amostra`:** confirmar se vêm do filtro de laboratórios da view.
- **Go-live:** de qual número cada sequência parte, para continuar a planilha.
- **Se o HP vindo da congelação herda o número da CO.** Hoje, cada bancada tem o seu número.
- **Amostra que chega depois de o exame ter nº interno:** hoje recebe 409, e a inclusão tardia não existe.
- **Trava de dados incompletos (ponto de decisão nº 2 de `00-validacao-negocio.md`):** adotada a trava para status e prontuário e o preenchimento para o material vazio, sem alerta gravado no AGHU.

### Técnicas
- **RBAC local:** a documentação descreve perfis em tabela local, mas o código usa grupos do AD. O perfil `RECEPCAO` depende dessa feature.
- **Matrícula (RN-06):** o recebimento registra o login do AD, pois a matrícula não está disponível no Mock.
- **Auditoria não atômica:** `registrar_auditoria()` faz commit próprio. Se ela falhar depois do commit do negócio, a resposta é 500 e o exame já existe; ao bipar de novo, a tela mostra o nº existente.
- **Framework, fora do alcance das features:**
  - `audit_framework.py:39` quebra com `NameError: ENDC`.
  - `alembic upgrade head` falha em banco vazio: `df72b10ec0f3` não cria a tabela, e `8a2efbe37bb6` tenta removê-la.
  - `alembic/env.py` exige `SQLITE_DSN`, ausente do `.env.example`, e não importa os modelos, o que impede o autogenerate.
  - `audit_logs` não tem migração; a tabela nasce do `create_all` no startup.
  - A versão em `src/version.py` não foi alterada por esta feature.
- **Leitura direta do AGHU:** `SolicitacaoPostgresProvider`, inclusive a lista paginada, foi testado com uma sessão simulada, não com o banco real. `STRATEGY` continua em `csv`.
- **Lista sem filtro na tela:** mostra todas as solicitações, com a situação e o nº interno. A API mantém o parâmetro `somente_recebiveis`, que a tela não usa. Filtrar por situação exigiria cruzar o AGHU com o banco local.
- **Divergências com `02-requisitos.md`, que não foi alterado:** RF004 e CARE-RF004 falam em checklist por amostra, e o sistema usa um único checklist por recebimento, a pedido da equipe. RF005 lista 5 motivos, e o sistema usa os 14 da planilha. A urgência e o nº de peças do RF007 foram antecipados para o recebimento.
- **Dados reais:** `data/vw_solicitacao_atualizado.csv` tem dados de pacientes e fica fora do Git. Os testes usam `data/solicitacoes_aghu_exemplo.csv`, com dados inventados.
- **Documentos com escrita no AGHU fora da Recepção:** UC014 e UC025 ainda descrevem integração de escrita, contrariando RN-01 e RF012. `01-visao.md` e `00-validacao-negocio.md` citam alerta automático no AGHU.
- **Divergência em `06-arquitetura.md`:** o guardrail pede `.spec.ts` para controllers; prevalece o `AGENTS.md` (Pytest).
