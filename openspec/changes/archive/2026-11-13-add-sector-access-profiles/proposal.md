# Proposal

## Why

O Sistema AP já oferece autenticação JWT no backend e uma experiência de Recepção no Vue, mas não associa a identidade autenticada a perfis locais nem aplica autorização às operações. O login mock atual aceita somente `admin/admin`; no frontend, os serviços de Recepção operam em memória e não consultam permissões. A mudança estabelece uma política de acesso verificável desde já e um contrato de identidade que permita substituir o mecanismo de autenticação depois, sob governança do HC.

## What Changes

- Separar autenticação (obter identidade por provedor configurado) de autorização (resolver perfis e permissões da aplicação), negando acesso por padrão.
- Definir os nove perfis de negócio e um catálogo explícito de permissões para as operações existentes. O catálogo poderá evoluir junto com cada módulo; operações futuras não recebem acesso antecipado.
- Aplicar autorização efetiva no servidor às capacidades que já existem na Recepção; a interface Vue refletirá as permissões, sem ser a barreira de segurança.
- Oferecer identidades mockadas selecionáveis somente em desenvolvimento/testes e falhar a inicialização em produção se o provedor mock estiver configurado.
- Preparar uma interface de provedor de identidade (Adapter) sem implementar nem escolher AD/LDAP, SSO, OIDC, SAML ou outro protocolo institucional.
- Registrar identidade e ações protegidas para auditoria conforme os mecanismos existentes.
- Não criar fluxos de negócio, telas ou rotas para os demais setores.

## Capabilities

### New Capabilities
- `sector-access-control`: perfis, permissões, resolução e enforcement no backend e apresentação correspondente na Recepção.
- `authentication-adapter`: contrato estável de identidade e seleção segura do provedor de autenticação.

### Modified Capabilities
- `sample-reception`: restringir ações existentes da Recepção de acordo com permissões explícitas, incluindo chamadas diretas ao backend.
- `case-search`: controlar consulta e ações existentes de casos por permissão, sem inferir acesso a etapas futuras.
- `nonconformity-return`: controlar registro e atualização de devoluções conforme permissões validadas.
- `case-detail`: controlar consulta e cancelamento existentes de caso conforme permissões validadas.

## Impact

- Backend: `src/auth/`, `src/dependencies.py`, `src/routers/`, configuração, auditoria e testes. O repositório atualmente só tem routers genéricos de autenticação/admin/paciente; as operações de Recepção estão em serviços mock no frontend, portanto o enforcement de servidor requer expor no backend as operações existentes antes de protegê-las.
- Frontend: `stores/auth.ts`, `router/index.ts`, layout e views/serviços de Recepção passam a consumir identidade/permissões e ocultar ações indisponíveis.
- Governança: matriz de permissões permanece explícita e auditável; a atribuição definitiva de perfis institucionais não é concedida a administradores locais de desenvolvimento.
- Fora de escopo: implementar módulos futuros, gestão institucional de contas, AD/LDAP ou qualquer protocolo de autenticação do HC.
