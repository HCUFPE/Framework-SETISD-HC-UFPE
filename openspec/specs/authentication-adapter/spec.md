# authentication-adapter Specification

## Purpose
Isolar a autenticação de desenvolvimento atrás de um contrato estável de identidade, preparando a integração institucional sem escolher ou implementar seu protocolo.

## Requirements

### Requirement: Provedor de identidade substituível

O sistema SHALL obter a identidade autenticada por uma interface de provedor configurada. Módulos e regras de autorização SHALL consumir uma identidade normalizada por dependência e SHALL NOT depender diretamente da implementação concreta ou protocolo de autenticação.

#### Scenario: Identidade fornecida pelo Adapter

- **WHEN** um usuário conclui autenticação por um provedor configurado
- **THEN** o provedor retorna uma identidade normalizada com identificador estável e atributos de apresentação opcionais
- **AND** autorização local resolve perfis e permissões separadamente dessa identidade

### Requirement: Mock restrito a desenvolvimento e testes

O provedor mock SHALL ser selecionado explicitamente e SHALL estar disponível somente em ambientes de desenvolvimento e testes. A configuração SHALL impedir inicialização em produção com o provedor mock.

#### Scenario: Mock em desenvolvimento

- **WHEN** ambiente de desenvolvimento seleciona uma identidade de teste cadastrada
- **THEN** o provedor autentica essa identidade fictícia e retorna sua identidade normalizada
- **AND** o cliente não pode inventar atributos ou perfis no pedido de autenticação

#### Scenario: Mock em produção

- **WHEN** ambiente de produção está configurado para usar provedor mock
- **THEN** a aplicação falha ao inicializar
- **AND** não emite tokens autenticados por mock

### Requirement: Protocolo institucional não presumido

O contrato SHALL documentar os dados e responsabilidades esperados do futuro provedor institucional sem definir protocolo, endpoint, claims, fluxo de credenciais ou mecanismo de sessão. AD/LDAP, SSO, OIDC e SAML SHALL NOT ser implementados por esta mudança.

#### Scenario: Implementação futura pelo HC

- **WHEN** TI do HC integrar autenticação institucional futuramente
- **THEN** poderá implementar o contrato de provedor e mapear a identidade institucional para a identidade normalizada
- **AND** regras de autorização e módulos não precisarão depender do protocolo utilizado
