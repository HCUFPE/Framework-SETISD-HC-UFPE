# Autenticação e autorização do Sistema AP

## Estado atual

A autenticação usa um adapter de identidade. Neste ambiente, o adapter disponível é `MockIdentityProvider`, restrito a `development`, `test` e `testing`. Use as identidades fictícias da tela de login com a senha `demo`; `admin/admin` é compatibilidade de desenvolvimento. Não use dados nem credenciais reais.

A autorização vem do cadastro local SQLite (`usuario`, `perfil` e `usuario_perfil`). O login só emite token se a identidade autenticada também estiver cadastrada e ativa localmente. As permissões são calculadas no backend a partir dos perfis ativos; cada dependência `exigir_permissao(...)` consulta novamente o cadastro antes de autorizar uma operação. O conteúdo de grupos ou perfis enviado pelo cliente ou pelo provedor não concede permissões.

Ao iniciar com o adapter mock, identidades fictícias são cadastradas uma vez para desenvolvimento. Alterações locais de status e perfis existentes não são sobrescritas pela carga inicial. A identidade `sem-perfil` pode autenticar e consultar a própria identidade, mas não recebe acesso a operações protegidas.

`src/auth/authorization.py` define os nove códigos de perfil, o catálogo de permissões e a união explícita para múltiplos perfis. A migration `e24bc68129ad_add_local_user_profiles.py` cria as tabelas do cadastro. Execute `alembic upgrade head` para aplicar as migrations em uma instalação persistente.

## Integração institucional

Não há adapter institucional AD/LDAP, SSO ou OIDC nesta versão. `AUTH_PROVIDER=mock` é proibido em produção, e o startup falha se um provedor institucional ainda não implementado for selecionado. A configuração e o protocolo institucionais precisam ser definidos pela TI do HC antes de produção.

## Proteção das operações

As rotas FastAPI verificam as permissões no backend; guards e menus Vue apenas refletem as permissões retornadas por `GET /api/users/me`. Uma chamada direta sem autorização recebe HTTP 403, e uma chamada sem token válido recebe HTTP 401. Os grupos externos não são usados como fonte de privilégios.

## Recepção

A Recepção usa a API FastAPI/SQLite como fonte principal por `frontend/src/services/ap/http.ts`. O mock de navegador só é selecionado explicitamente em desenvolvimento para testes isolados; não há fallback silencioso da API para o mock. Recebimentos, vínculos IHQ e não conformidades são persistidos pelo backend com autoria, auditoria e permissões correspondentes. Etiquetas e fichas são pré-visualizadas e impressas no navegador, sem chamada de API, histórico ou `AuditLog`.

## Provisionamento

A interface de administração de usuários/perfis ainda não está disponível. Até que ela seja implementada e aprovada pelo HC, novos usuários e alterações de perfis precisam ser provisionados por um processo administrativo controlado no banco local.
