# Design

## Context

O frontend separa os contratos em frontend/src/services/ap/types.ts das implementações mock em frontend/src/services/ap/mock/. As stores e views de Recepção, busca, detalhe e devoluções consomem esses serviços; frontend/src/services/ap/index.ts seleciona hoje os mocks, apoiados por frontend/src/mocks/ap/db.ts e seed.ts. O banco do navegador é volátil e não pode ser a fonte oficial de uma mutação protegida.

O backend já inicializa o banco local SQLite APP_DB, usa SQLAlchemy assíncrono, Alembic e a arquitetura Router → Controller → Provider → Resource. Há routers de autenticação, administração, saúde e pacientes, mas não há endpoints nem modelos de domínio da Recepção. src/auth/authorization.py contém as permissões e a dependência exigir_permissao; src/helpers/audit_helper.py e src/models/audit_log.py registram usuário, categoria, ação, recurso, estados serializados e IP. O helper realiza commit na sessão, portanto a mutação e a auditoria devem usar a mesma sessão e não pode haver commit intermediário antes do registro.

As regras funcionais permanecem em docs/especificacao/ e nas specs sample-reception, case-search, case-detail e nonconformity-return da mudança add-sector-access-profiles. Os mocks são referência para os comportamentos já prototipados, sem prevalecer sobre esses documentos. Em especial, a lista de casos não deve abrir operações das etapas futuras.

## Goals / Non-Goals

**Goals:** tornar persistente no servidor o estado das operações atuais; preservar a experiência e os contratos do frontend; centralizar autorização e autoria no backend; manter dados fictícios de solicitação disponíveis apenas em desenvolvimento/testes; permitir substituição futura do provedor de solicitações sem acoplar controllers ao AGHU.

**Non-Goals:** migrar telas para o backend; integrar com o AGHU; implementar outros setores; criar novos fluxos, regras clínicas ou permissões; criar um segundo mecanismo de autenticação, sessão ou autorização.

## Decisions

### 1. API e camadas

Adicionar um router privado sob /api/ap e manter a separação existente: Router valida HTTP e aplica Depends de identidade/permissão; Controller executa as regras e orquestra a unidade de trabalho; Provider implementa consultas e gravações; Resource entrega a sessão APP_DB. Os controllers dependem de interfaces de provider, não de SQLite, fixture ou AGHU.

Os caminhos propostos são:

| Operação do serviço atual | Endpoint proposto | Permissão do catálogo atual |
|---|---|---|
| listarPendentes, contarPendentes, lerSolicitacao | GET /api/ap/solicitacoes/pendentes, GET /api/ap/solicitacoes/pendentes/contagem, GET /api/ap/solicitacoes/{codigo} | casos:consultar |
| listar, obter, buscar | GET /api/ap/casos, GET /api/ap/casos/{numeroInterno}, GET /api/ap/casos/busca?termo=&limite= | casos:consultar |
| buscarElegiveisIhq | GET /api/ap/casos/elegiveis-ihq?termo= | consulta auxiliar mantida sem operação de vínculo manual; associação IHQ será automática em mecanismo futuro a definir |
| confirmarEntrada | POST /api/ap/recebimentos | recepcao:receber |
| vincularIhq | sem operação manual nesta mudança | a associação de solicitação IHQ ao caso será automática; mecanismo e gatilho ainda serão definidos pelo HC |
| cancelar | POST /api/ap/casos/cancelamento com numeroInterno e motivo no corpo | casos:cancelar |
| registrarAcionamentoPlantao | POST /api/ap/casos/acionamentos-plantao com numeroInterno no corpo | recepcao:acionar_plantao |
| registrar | POST /api/ap/nao-conformidades | recepcao:registrar_nao_conformidade |
| listarDevolucoes | GET /api/ap/devolucoes | devolucoes:consultar, concedida a Recepcionista SAP e Coordenação/Administrador após validação SAP/HC |
| atualizarSituacao | PATCH /api/ap/devolucoes/{id}/situacao | devolucoes:alterar_situacao, concedida a Recepcionista SAP e Coordenação/Administrador |
| AuditoriaService.listar | GET /api/ap/auditoria | auditoria:consultar |

Rotas estáticas de casos devem ser declaradas antes da rota dinâmica por número. Os caminhos podem ser ajustados durante a implementação por convenção do projeto, desde que o contrato e a cobertura de operações permaneçam equivalentes. Não expor uma operação sem dependência de permissão explícita; para os itens pendentes, responder 403 e não alterar estado até aprovação e inclusão formal no catálogo central.

### 2. Compatibilidade do contrato frontend

As implementações HTTP devem continuar satisfazendo AghuService, CasoService, NaoConformidadeService e AuditoriaService. Manter nomes, tipos e formas de retorno usados pelas stores e views, incluindo union de leitura da solicitação, paginação/limite da busca, retorno detalhado da devolução e o par caso/IHQ. Usar aliases Pydantic/serialização para conservar o JSON esperado pelos tipos TypeScript.

As assinaturas existentes que recebem Responsavel podem ser preservadas nesta etapa para não quebrar stores e views, mas a implementação HTTP não deve enviar esse valor como autoria confiável. O servidor obtém o responsável do token e monta os campos de autoria das respostas a partir da identidade normalizada. A interface de serviço pode remover o argumento em uma mudança posterior separada, se desejado.

ServiceError continua recebendo status e detail; a implementação Axios deve converter erros HTTP para esse formato e preservar os interceptadores de frontend/src/services/api.ts. Respostas de erro do backend seguem {"detail": "mensagem"}. Manter os códigos funcionais existentes quando identificados nos mocks: 400 para campos obrigatórios/inválidos, 404 para registro inexistente, 409 para conflito de estado, 422 para regra de elegibilidade e 503 para provedor de solicitações indisponível. 401 e 403 são reservados para autenticação e autorização.

### 3. Regras e limites funcionais

O Controller deve reproduzir as regras existentes: solicitação única e aguardando recebimento; conferência completa; quantidade inteira positiva; procedimento obrigatório; justificativa quando urgente; número interno único por tipo/ano; vínculo IHQ a caso existente elegível com confirmação de prontuário divergente; cancelamento de caso ativo com motivo; acionamento de plantão somente uma vez e apenas para congelação; registro de não conformidade nos contextos existentes; atualização de situação de devolução conforme os estados já definidos; pesquisa textual normalizada, ordenação e limites atuais.

Ao confirmar recebimento, persistir status, número e tipo do caso, dados de entrada, responsável, etapa inicial, itens de material produzidos na Recepção, conferência e histórico. A associação entre solicitação IHQ e caso será automática; o gatilho e o mecanismo ainda não estão definidos e não há operação manual nesta mudança. Impressão física continua no navegador e não gera evento de histórico ou auditoria. Não adicionar operações de macroscopia, processamento, IHQ técnico, microscopia/laudo ou arquivo.

### 4. Modelos e persistência

Usar APP_DB e modelos SQLAlchemy locais, com migração Alembic. Persistir somente o subconjunto necessário ao comportamento já existente: representação das solicitações fictícias e sua situação local; caso AP; conferência; itens de material gerados no recebimento; vínculo de exame IHQ recebido; histórico de caso; não conformidade e devolução. Usar AuditLog existente para a trilha, sem duplicar tabela de auditoria. Alinhar nomes e chaves a docs/especificacao/04-modelo-dados.md, especialmente SOLICITACAO_AGHU, CASO_AP, CONFERENCIA_RECEBIMENTO, ITEM_MATERIAL, HISTORICO_CASO, NAO_CONFORMIDADE e DEVOLUCAO.

Adicionar chaves estrangeiras, restrições de unicidade e índices necessários para impedir solicitação recebida duas vezes, código de caso duplicado e vínculo de devolução órfão. Gravação da mudança de estado, histórico e auditoria deve ser coerente em uma unidade transacional. A geração do número interno deve continuar única sob requisições concorrentes; a implementação deve usar restrição persistente e tratamento/repetição de conflito, não apenas consultar a lista e incrementar em memória.

O seed atual do navegador serve como fonte dos dados fictícios de desenvolvimento e deve ser reproduzido integralmente no APP_DB: 29 solicitações, 19 casos, 20 conferências, 3 não conformidades e 3 devoluções. A carga é idempotente e não sobrescreve estado operacional em cada inicialização. Os registros continuam sendo demonstração fictícia; não representam dados do AGHU. Casos, conferências, materiais, não conformidades e devoluções passam a ter estado oficial no APP_DB.

### 5. Provedor mock de solicitações

Criar uma interface de leitura de solicitações e um provedor de desenvolvimento/testes sustentado pela fixture persistida no APP_DB. O provedor deve reproduzir a disponibilidade simulada usada hoje pelos serviços, inclusive a resposta 503 quando configurado como indisponível. A troca do provedor fica na composição de dependências, seguindo o padrão de src/dependencies.py.

O provedor fixture deve ser selecionável somente em ambiente de desenvolvimento/testes. Se for selecionado em produção, a aplicação deve falhar fechada na inicialização ou recusar essas consultas com erro explícito; nunca deve servir seed fictício como dado institucional nem cair silenciosamente para ele. Preservar o comportamento atual: listar e ler solicitação falham com 503 quando o provedor está indisponível; contar pendentes retorna a contagem do estado local disponível, sem simular uma consulta ao AGHU. Nenhuma conexão ou escrita no AGHU é parte desta mudança. A implementação institucional futura deverá ser outra implementação da interface e permanece sem protocolo definido.

### 6. Autorização e identidade

Reutilizar auth_handler.decode_token, a identidade normalizada e exigir_permissao de add-sector-access-profiles. Não armazenar credenciais/sessões paralelas e não confiar em autor, usuário ou perfil enviado no corpo, query string ou cabeçalho criado pelo frontend. O cliente pode continuar enviando campos de compatibilidade, mas o servidor os ignora para autoria.

Aplicar casos:consultar às leituras já cobertas pelo catálogo, recepcao:receber ao recebimento principal, recepcao:registrar_nao_conformidade ao registro de não conformidade, recepcao:acionar_plantao ao acionamento de plantão, casos:cancelar ao cancelamento e auditoria:consultar à consulta da auditoria. Não transformar a permissão de consulta em permissão de mutação.

Não há vínculo IHQ iniciado por usuário: a associação será automática, com mecanismo a definir pelo HC. A impressão não exige endpoint nem permissão própria; o acesso ao caso continua protegido por casos:consultar. A consulta e a atualização de situação das devoluções usam, respectivamente, devolucoes:consultar e devolucoes:alterar_situacao, concedidas a Recepcionista SAP e Coordenação/Administrador conforme validação SAP/HC.

Todas as rotas AP, inclusive GET, são privadas. Sem token válido, responder 401; com identidade autenticada sem a permissão exigida, responder 403 sem retornar dados restritos nem produzir efeitos. Mais de um perfil continua resolvido pela união explícita já definida no RBAC central.

### 7. Auditoria e autoria

Registrar cada mutação funcional por src/helpers/audit_helper.py e AuditLog, incluindo confirmação, cancelamento, plantão, não conformidade e alteração de situação. Usar identidade autenticada como usuario; categoria NEGOCIO_CLINICO; ação e recurso estáveis; estados anterior e novo relevantes; IP de origem obtido no servidor. Nunca confiar em IP ou autor do payload. Não registrar evento de impressão nem copiar dados clínicos completos para o log quando bastarem os campos alterados.

Usar a mesma AsyncSession para mutação, histórico e auditoria e não executar commit antes de registrar auditoria, pois o helper existente realiza o commit. Falha ao gravar a auditoria deve fazer rollback da operação associada. Para consultas de auditoria, exigir auditoria:consultar e não permitir alteração/exclusão de registros pela API desta mudança.

### 8. Transição do frontend

Criar serviços HTTP sob os contratos atuais e fazer a seleção de frontend/src/services/ap/index.ts usar o backend como origem normal. Manter os mocks de frontend somente para testes ou desenvolvimento isolado explicitamente selecionado; não permitir que uma falha HTTP silenciosamente volte a executar mutações em memória. Manter as telas, componentes, stores e navegação Vue. A pré-visualização e a impressão física são executadas no navegador, sem chamada de registro ao backend.

Usar o estado de identidade/permissões já exposto pela mudança de perfis para ocultar ações sem permissão, e tratar 401/403 sem exibir sucesso falso. A pré-visualização e a impressão física são executadas pelo navegador, sem chamada de registro ao backend. Em qualquer caso, o servidor continua sendo a barreira efetiva para operações de domínio.

## Risks / Trade-offs

- O gatilho e o mecanismo da associação automática IHQ ainda serão definidos pelo HC e ficam fora desta mudança. A consulta e a alteração de situação de devoluções foram validadas para Recepcionista SAP e Coordenação/Administrador.
- O escopo adiciona persistência para um domínio antes mantido em memória. Migrações e concorrência do identificador interno precisam ser verificadas antes de substituir os mocks como origem oficial.
- Os dados de solicitações são fictícios durante o desenvolvimento. A operação em produção depende de futura implementação institucional do provedor; esta mudança não constitui integração com o AGHU.
- O contrato do AuditLog existente faz commit da sessão. A implementação deve preservar a atomicidade sem introduzir commits intermediários.

## Open Questions

- SAP/HC ainda deve confirmar quais perfis podem consultar, pelo código da solicitação, dados de solicitações já recebidas ou devolvidas. Isso é separado da lista de devoluções, validada para Recepcionista SAP e Coordenação/Administrador.
- A fixture adotada reproduz o seed completo que já existia em frontend/src/mocks/ap/seed.ts, preservando os dados de demonstração visíveis antes da migração dos serviços para HTTP.
