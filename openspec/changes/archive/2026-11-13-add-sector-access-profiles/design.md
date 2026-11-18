# Design

## Context

`src/auth/auth.py` concentra `AuthHandler`, uma interface e implementações mock/AD que são selecionadas implicitamente pela presença de `AD_URL`. O mock só autentica `admin/admin`; o JWT expõe atributos e grupos de diretório, e `/api/users/me` retorna essa identidade. A proteção existente é autenticação JWT em routers, e `/api/admin/admin-only-data` usa um grupo AD. Não há resolução local de perfis RBAC. No frontend, Pinia mantém um único usuário e `isAdmin` consulta grupo AD; rotas exigem login, mas não perfil. Recepção, consulta, detalhe, devoluções e mutações são serviços mock em memória, sem backend de domínio. A arquitetura de serviços do frontend separa contrato e implementação mock; `src/helpers/audit_helper.py` e o modelo `AuditLog` já existem.

Os documentos de negócio definem nove atores em `03-casos-uso.md`, RF009 em `02-requisitos.md` e regras de autorização em `00-validacao-negocio.md` (RN-03). Os casos de uso associam atores a operações, mas não exigem uma matriz global completa antes da implementação dos módulos. O catálogo cobre as operações existentes e evolui junto com cada setor; nenhuma permissão de módulo inexistente é concedida antecipadamente.

## Goals / Non-Goals

**Goals:** identidade desacoplada do protocolo; autorização central no servidor; negação por padrão; múltiplos perfis por usuário; capacidades preparadas para os nove papéis; aplicação às operações atuais da Recepção; identificação de usuário consistente para auditoria; mock restrito a desenvolvimento/testes.

**Non-Goals:** integração institucional, provisionamento real de contas, interface administrativa de RBAC, telas/endpoints de negócio dos outros setores, decisões não confirmadas da matriz.

## Decisions

### 1. Adapter de identidade, sem antecipar protocolo

Definir contrato de provedor que autentica credenciais e devolve uma identidade normalizada e estável (identificador institucional opaco, nome para exibição e atributos opcionais). O `MockIdentityProvider` implementa o contrato; o ponto de composição seleciona provedor por configuração explícita. Os módulos recebem a identidade autenticada por dependência FastAPI, não importam nem consultam o Adapter. O formato do identificador e a verificação institucional ficam para acordo com TI. Não transportar grupos de autenticação como permissões da aplicação.

`ENV=production` combinado com provedor mock deve impedir inicialização. Provedor institucional não é implementado nesta mudança; a implantação produtiva permanece bloqueada até configuração/entrega do provedor oficial.

### 2. RBAC simples e deny-by-default

Representar permissões como identificadores estáveis `recurso:ação` (por exemplo, consulta, execução, alteração, aprovação), associadas a perfis; identidade pode resolver mais de um perfil e recebe a união das permissões explícitas. Ausência de identidade autenticada resulta em 401; identidade sem perfil ou sem permissão requerida resulta em 403. Rotas privadas permanecem protegidas por padrão e operações mutáveis verificam permissão no backend. Não usar o perfil Coordenação/Administrador como curinga implícito nem conceder permissões de setores futuros.

A fonte inicial da política será um catálogo versionado no código/configuração, pois ainda não existe modelo de usuários/RBAC no banco local nem tela administrativa de usuários. Persistência e administração definitivas dependem de decisão institucional e ficam fora desta mudança. O adaptador de autorização deverá permitir troca da fonte sem alterar os módulos.

### 3. Catálogo de perfis e limites da matriz

Registrar os identificadores: `RECEPCIONISTA`, `PROFISSIONAL_MACROSCOPIA`, `TECNICO_PROCESSAMENTO`, `TECNICO_IHQ`, `MEDICO_RESIDENTE`, `PATOLOGISTA_PRECEPTOR`, `CITOTECNICO`, `TECNICO_ARQUIVO`, `COORDENACAO_ADMINISTRADOR`.

Permissões de módulos inexistentes permanecem não atribuídas e sem endpoints. Para a Recepção, os casos de uso e as decisões confirmadas orientam o catálogo inicial das operações existentes. Não é necessário consolidar a matriz completa de todos os setores para concluir esta mudança: o catálogo será ampliado ou ajustado junto com cada módulo. Operações ainda inexistentes permanecem sem permissão; em especial, nenhuma permissão de triagem ou parecer do Citotécnico é presumida antes da definição dessas operações.

### 4. Mock selecionável e usuário sem privilégio mágico

Disponibilizar um conjunto pequeno de identidades fictícias, uma para cada papel e uma sem perfil, por configuração/documentação de desenvolvimento/teste; cada login mock emitirá identidade previsível e não aceitará identidade arbitrária enviada pelo cliente. O seletor não será exposto em produção. `admin/admin` legado deve ser tratado como identidade de teste explícita e não obter acesso total por grupo AD; compatibilidade/remoção será verificada na implementação. A seleção não será um mecanismo duplicado de sessão: reutiliza JWT e endpoints atuais, alterando a origem da identidade.

### 5. Enforcement nas operações reais e integração de UI

Como Recepção ainda não possui endpoints de domínio, primeiro criar no backend apenas as operações equivalentes às funcionalidades já entregues e fazer os serviços do frontend consumirem esses endpoints. Cada endpoint declara permissão requerida; autorização não fica somente em guards de rota ou botões. Consultas e ações de interface usam a mesma resposta de identidade/permissões. O frontend oculta opções não autorizadas e lida com 403, mas a resposta do servidor é decisiva. As abas de módulos futuros podem continuar informativas/sem ação, sem que a presença visual implique acesso funcional.

### 6. Auditoria

As mutações protegidas usam usuário autenticado como autor, sem aceitar identificador de ator do payload. Ações relevantes registram categoria e estados anterior/novo através do helper existente. Mudanças futuras de atribuição de perfis também devem ser auditáveis; esta proposta não introduz gestão institucional de atribuições.

## Risks / Trade-offs

- A matriz disponível nos documentos é narrativa/parcial. O catálogo atual cobre as operações implementadas e pode evoluir por módulo; operações sem concessão explícita continuam negadas até que seu comportamento e acesso sejam definidos.
- Trazer operações atualmente em memória para endpoints muda a fronteira de persistência e exige definir o armazenamento das operações existentes. O desenho deve preservar o contrato de domínio dos serviços, sem ampliar os fluxos de negócio.
- O mock nunca serve como identidade de produção; a troca institucional exige que TI implemente o Adapter e defina identificador/claims, sem assumir protocolo.
- A associação definitiva de perfis a usuários institucionais e sua fonte governada em produção ficam fora desta mudança e sob responsabilidade do TI do HC. Esta proposta cobre identidades mockadas para desenvolvimento/testes e a estrutura central de permissões.
- O auditor do framework permanece em 10/11 porque esta mudança não persiste associações RBAC no APP_DB. A equipe aceitou essa exceção de escopo; isso não representa integração institucional nem habilita o mock em produção.
