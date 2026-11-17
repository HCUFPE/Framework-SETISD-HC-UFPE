# sector-access-control Specification

## Purpose
Define autorização por perfis para o Sistema AP, com enforcement no backend e apresentação coerente das permissões nas funcionalidades existentes.

## Requirements

### Requirement: Catálogo de perfis sem concessão implícita

O sistema SHALL reconhecer os perfis `RECEPCIONISTA`, `PROFISSIONAL_MACROSCOPIA`, `TECNICO_PROCESSAMENTO`, `TECNICO_IHQ`, `MEDICO_RESIDENTE`, `PATOLOGISTA_PRECEPTOR`, `CITOTECNICO`, `TECNICO_ARQUIVO` e `COORDENACAO_ADMINISTRADOR`. A existência de um perfil SHALL NOT implicar disponibilidade de módulo ou acesso a recursos sem permissão explícita.

#### Scenario: Perfil de setor futuro

- **WHEN** um usuário autenticado possui somente perfil de um setor ainda não implementado
- **THEN** o usuário não recebe acesso funcional a rotas ou operações inexistentes desse setor
- **AND** o sistema não cria telas nem fluxos de negócio para esse perfil

#### Scenario: Usuário sem perfil

- **WHEN** uma identidade autenticada não tem perfil associado
- **THEN** o sistema identifica a identidade como autenticada
- **AND** nega por padrão qualquer operação protegida sem permissão explícita

### Requirement: Permissões centralizadas e deny-by-default

O backend SHALL resolver permissões explícitas a partir de um ou mais perfis e verificar autorização em cada operação protegida. Uma identidade sem a permissão requerida SHALL receber 403. Coordenação/Administrador SHALL NOT receber curinga implícito.

#### Scenario: Operação sem concessão

- **WHEN** um usuário autenticado chama diretamente uma operação sem permissão resolvida
- **THEN** o servidor responde 403
- **AND** não executa a operação

#### Scenario: Identidade não autenticada

- **WHEN** uma chamada protegida chega sem identidade válida
- **THEN** o servidor responde 401
- **AND** não executa a operação

#### Scenario: Mais de um perfil

- **WHEN** uma identidade possui mais de um perfil válido
- **THEN** o sistema resolve a união das permissões explicitamente associadas a esses perfis
- **AND** não infere permissões além dessa união

### Requirement: Catálogo explícito e evolutivo de permissões

O catálogo SHALL conceder somente permissões explícitas para operações existentes e SHALL distinguir consulta, execução, alteração e aprovação quando esses fluxos forem implementados. O catálogo SHALL evoluir junto com cada módulo; uma matriz global completa SHALL NOT bloquear a conclusão desta mudança. Operações ainda inexistentes SHALL permanecer sem endpoint e sem concessão.

#### Scenario: Operação futura sem concessão

- **WHEN** um módulo futuro introduz uma operação ainda não incluída no catálogo
- **THEN** o backend nega a operação por padrão até que ela seja definida e receba uma permissão explícita
- **AND** a falta de uma matriz global completa não bloqueia os módulos já implementados

#### Scenario: Consulta de devoluções pela Recepção

- **WHEN** uma identidade possui o perfil `RECEPCIONISTA` ou `COORDENACAO_ADMINISTRADOR`
- **THEN** o catálogo concede `devolucoes:consultar` para listar rejeições e devoluções existentes
- **AND** concede `devolucoes:alterar_situacao` para atualizar sua situação
- **AND** outros perfis não recebem essas permissões por consequência da consulta de casos

### Requirement: Interface coerente com autorização efetiva

O frontend SHALL usar as permissões resolvidas para ocultar ações e opções indisponíveis e SHALL tratar respostas 401/403. A ocultação no frontend SHALL NOT substituir a autorização no backend.

#### Scenario: Ação sem permissão na Recepção

- **WHEN** o usuário não possui permissão para uma ação existente da Recepção
- **THEN** a interface não oferece essa ação
- **AND** chamada direta correspondente continua sendo recusada pelo backend

### Requirement: Auditoria vinculada à identidade

Mutação protegida auditável SHALL registrar a identidade autenticada como autor, categoria apropriada e estados anterior/novo conforme o mecanismo existente. O backend SHALL NOT aceitar do cliente o autor da auditoria.

#### Scenario: Autor forjado no payload

- **WHEN** uma requisição de mutação inclui um autor diferente da identidade autenticada
- **THEN** a auditoria permanece vinculada à identidade autenticada
- **AND** o campo fornecido pelo cliente não altera a autoria
