# reception-api Specification

## Purpose
Define a API FastAPI e o estado persistente do servidor para as operações já disponíveis no módulo de Recepção, com autorização central, autoria autenticada e compatibilidade com os serviços do frontend.

## Requirements

### Requirement: API de domínio para as operações atuais

O backend SHALL expor operações protegidas para listar, contar e localizar solicitações e grupos de exames; listar, obter e buscar casos; confirmar recebimento por grupo; manter o vínculo manual de IHQ a um caso elegível como contingência quando o AGHU não fornecer o vínculo; registrar acionamento de plantão e não conformidade; listar devoluções; atualizar sua situação; e consultar auditoria. Quando o AGHU já fornecer o vínculo, esse é o fluxo ideal. Solicitações são identificadas por `<codigoSolicitacao>:<tipoExame>`. A API SHALL cumprir os contratos de `frontend/src/types/ap.ts` e `src/schemas/reception.py`.

#### Scenario: Contratos existentes atendidos pela API

- **WHEN** uma store ou view invoca um dos métodos atuais de AghuService, CasoService, NaoConformidadeService ou AuditoriaService
- **THEN** a implementação HTTP retorna o mesmo formato de domínio esperado pelo contrato
- **AND** a interface, navegação e componentes Vue permanecem no frontend

#### Scenario: Impressão física local

- **WHEN** o usuário imprime etiquetas ou ficha de trabalho
- **THEN** o navegador gera a saída física sem chamada de API, registro em histórico ou `AuditLog`

### Requirement: Regras de negócio e estado persistido

O servidor SHALL validar e executar as regras já presentes em docs/especificacao/ e nas specs sample-reception, case-search, case-detail e nonconformity-return. Mutações SHALL atualizar o estado oficial no APP_DB, incluindo os registros relacionados de histórico e conferência quando aplicável. O servidor SHALL NOT aceitar no recebimento ou na devolução uma transição incompatível com o estado atual.

#### Scenario: Recebimento válido

- **WHEN** um grupo `<codigoSolicitacao>:<tipoExame>` está aguardando recebimento e a requisição contém os dados obrigatórios do tipo
- **THEN** o servidor persiste caso ou vínculo IHQ, materiais do grupo, conferência, estado e histórico
- **AND** os demais grupos da solicitação permanecem independentes e podem continuar pendentes

#### Scenario: Validação ou conflito de estado

- **WHEN** uma requisição viola validação existente ou tenta alterar uma solicitação/caso em estado incompatível
- **THEN** o servidor responde com erro {"detail": "..."} e código compatível com a categoria do erro
- **AND** não persiste uma mutação parcial

#### Scenario: Persistência entre requisições

- **WHEN** uma mutação é concluída e uma nova sessão consulta o registro
- **THEN** a resposta contém o estado persistido no servidor, sem depender do estado em memória do navegador

### Requirement: Provedor fictício de solicitações somente em desenvolvimento

O backend SHALL fornecer solicitações fictícias por um provedor de desenvolvimento/testes substituível pela interface de provider. O provedor SHALL permitir simular indisponibilidade com erro 503. O sistema SHALL NOT usar fixture como dado do AGHU em produção, realizar conexão real com AGHU nesta mudança ou alternar silenciosamente para o mock quando uma fonte falhar.

#### Scenario: Consulta no ambiente de desenvolvimento

- **WHEN** o ambiente de desenvolvimento/testes seleciona o provedor fictício
- **THEN** a API lê solicitações fictícias do APP_DB inicializadas por fixture idempotente
- **AND** alterações operacionais não são sobrescritas a cada inicialização

#### Scenario: Fixture selecionada em produção

- **WHEN** a aplicação está em produção e a configuração seleciona o provedor fictício
- **THEN** a inicialização falha fechada ou as operações dependentes são recusadas com erro explícito
- **AND** nenhum dado fictício é apresentado como dado institucional

### Requirement: Autorização por operação no backend

Toda rota de domínio SHALL exigir identidade autenticada e permissão explícita do catálogo add-sector-access-profiles. A autorização SHALL ser aplicada também a chamadas HTTP diretas, SHALL negar por padrão permissões ausentes e SHALL NOT confiar em controles visuais do frontend. Consultar SHALL NOT implicar permissão para mutar.

O login SHALL exigir também um usuário local cadastrado e ativo em `usuario`; as permissões SHALL vir das associações ativas em `usuario_perfil` e `perfil`, nunca de claims do cliente.

#### Scenario: Consulta com permissão

- **WHEN** uma identidade autenticada possui casos:consultar e solicita uma leitura de solicitação ou caso coberta por essa permissão
- **THEN** o servidor responde com os dados permitidos pelo contrato atual

#### Scenario: Recebimento sem permissão

- **WHEN** uma identidade sem recepcao:receber chama diretamente a operação de confirmação de recebimento
- **THEN** o servidor responde 403
- **AND** não cria caso, material, conferência ou histórico

#### Scenario: Consultar devoluções como Recepcionista SAP

- **WHEN** uma identidade com a permissão devolucoes:consultar lista as devoluções
- **THEN** o servidor retorna a lista persistida
- **AND** Recepcionista SAP e Coordenação/Administrador recebem essa permissão validada
- **AND** a permissão não autoriza alteração da situação

#### Scenario: Consulta de devoluções sem permissão

- **WHEN** uma identidade autenticada sem devolucoes:consultar lista as devoluções
- **THEN** o servidor responde 403 e não retorna dados

#### Scenario: Vínculo manual IHQ de contingência autorizado

- **WHEN** o AGHU não forneceu o vínculo e uma identidade com `recepcao:receber` vincula manualmente um grupo IHQ a um caso elegível, confirmando uma divergência de prontuário quando houver
- **THEN** o backend persiste o vínculo, a conferência e o histórico
- **AND** não cria um caso principal para a IHQ

#### Scenario: Atualização de situação permitida

- **WHEN** Recepcionista SAP ou Coordenação/Administrador atualiza a situação de uma devolução
- **THEN** o servidor persiste a situação e atualiza a não conformidade associada conforme as regras existentes
- **AND** registra identidade autenticada, estado anterior e novo, IP e histórico do caso quando houver

#### Scenario: Atualização sem permissão

- **WHEN** outro perfil autenticado tenta atualizar diretamente a situação de uma devolução
- **THEN** o servidor responde 403 e não altera o estado

#### Scenario: Chamada sem token

- **WHEN** uma chamada a qualquer rota AP chega sem identidade autenticada válida
- **THEN** o servidor responde 401
- **AND** não retorna dados de domínio nem altera estado

#### Scenario: Identidade com múltiplos perfis

- **WHEN** a identidade autenticada tem mais de um perfil
- **THEN** a rota usa a união explícita de permissões resolvida pelo mecanismo central
- **AND** nenhuma permissão adicional é inferida nesta API

### Requirement: Autoria e auditoria das mutações

Cada mutação bem-sucedida SHALL registrar identidade autenticada, categoria, ação, recurso, estado anterior e novo e IP de origem no mecanismo AuditLog existente. O backend SHALL NOT aceitar autor ou IP enviados pelo cliente como fonte confiável. Falha de auditoria SHALL impedir que a mutação associada seja confirmada.

#### Scenario: Autor enviado pelo cliente

- **WHEN** a requisição inclui Responsavel ou usuário diferente da identidade autenticada
- **THEN** o registro de domínio e a auditoria usam a identidade do token
- **AND** o valor do cliente não altera autoria

#### Scenario: Auditoria de mudança de estado

- **WHEN** uma mutação altera caso, solicitação, conferência ou devolução, ou registra acionamento de plantão
- **THEN** a auditoria contém categoria NEGOCIO_CLINICO, ação e recurso identificáveis, estados relevantes anterior/novo e IP obtido no servidor
- **AND** a mutação, histórico e log são confirmados na mesma unidade transacional

#### Scenario: Falha ao persistir auditoria

- **WHEN** a gravação da trilha de auditoria falha durante uma mutação
- **THEN** o servidor faz rollback do estado associado
- **AND** responde erro sem indicar sucesso

#### Scenario: Consulta de auditoria sem permissão

- **WHEN** um usuário sem auditoria:consultar chama diretamente a consulta de auditoria
- **THEN** o servidor responde 403 e não retorna eventos

### Requirement: Adaptação HTTP sem duplicar autenticação

O frontend SHALL implementar os contratos de serviço atuais por HTTP usando o cliente Axios existente. A identidade, os perfis e as permissões SHALL vir do mecanismo de autenticação existente. Falhas de rede ou de autorização SHALL NOT executar silenciosamente uma mutação no mock local.

#### Scenario: Resposta de autorização negada

- **WHEN** uma chamada HTTP recebe 401 ou 403
- **THEN** o serviço preserva status e detail para a store/view tratar
- **AND** a interface não apresenta a mutação como concluída

#### Scenario: Mock frontend isolado

- **WHEN** testes ou desenvolvimento isolado selecionam explicitamente uma implementação mock do frontend
- **THEN** ela não é escolhida automaticamente como fallback da API
- **AND** o estado do navegador não é apresentado como estado persistente oficial

### Requirement: Verificação por perfil, persistência e chamadas diretas

A implementação SHALL possuir testes de API e provider para casos permitidos e negados por perfil, identidade ausente, validação de domínio, persistência entre sessões, concorrência de recebimento e consistência da auditoria. Os testes SHALL chamar endpoints diretamente sem depender da UI.

#### Scenario: Cobertura de todos os perfis

- **WHEN** os testes executam as rotas com identidades mockadas de cada um dos nove perfis, além de usuário sem perfil e usuário com múltiplos perfis
- **THEN** operações já concedidas obedecem exatamente à permissão resolvida pelo catálogo
- **AND** Citotécnico, usuário sem perfil e demais perfis sem a permissão não obtêm acesso por presunção

#### Scenario: Chamada direta sem permissão

- **WHEN** um teste chama diretamente um endpoint de mutação com token válido sem a permissão requerida
- **THEN** recebe 403 e verifica que estado, histórico e auditoria permanecem sem alteração

#### Scenario: Auditoria e persistência

- **WHEN** uma mutação permitida é chamada com identidade mockada
- **THEN** uma sessão subsequente observa a mudança persistida e o log com identidade autenticada, estados anterior/novo e IP
