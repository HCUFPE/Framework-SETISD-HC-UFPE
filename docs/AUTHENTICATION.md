# Autenticação e autorização do Sistema AP

## Estado atual

Autenticação identifica a pessoa; autorização aplica os perfis e permissões locais definidos em `src/auth/authorization.py`. O frontend recebe a identidade e as permissões por `GET /api/users/me`. Tokens JWT preservam a identidade normalizada, não os grupos do provedor como fonte de privilégios.

O Adapter ativo nesta etapa é `MockIdentityProvider`. Selecione uma identidade fictícia na tela de login e use a senha `demo`; `admin/admin` permanece como compatibilidade de desenvolvimento para o usuário Coordenação/Administrador. A identidade `sem-perfil` valida o comportamento de negação padrão. Não use dados ou credenciais reais.

`AUTH_PROVIDER=mock` só é permitido em `ENV=development`, `test` ou `testing`. Em produção, a aplicação falha ao iniciar com o provedor mock. Não há integração institucional nesta versão. A equipe de TI do HC deverá implementar `IdentityProvider`, definir como validar a identidade institucional e mapear um identificador estável; protocolo, claims, fluxo de sessão e gestão de perfis ainda serão decisões institucionais.

## Perfis e permissões

`src/auth/authorization.py` contém os nove identificadores de perfil, o catálogo de permissões e a união explícita para usuários com múltiplos perfis. Dependências FastAPI usam `exigir_permissao(...)`; identidade autenticada sem concessão recebe HTTP 403. Ausência de token recebe HTTP 401. Grupos vindos de provedores externos não autorizam ações.

As concessões de operações atuais derivam dos atores associados aos casos de uso em `docs/especificacao/03-casos-uso.md`. Permissões sem ator/operação claramente associado ficam negadas. Alterar a situação da devolução e gerir usuários não está concedido a perfil algum nesta implementação. As permissões de trabalho do Citotécnico em etapas futuras permanecem pendentes de validação SAP/HC; neste catálogo o perfil só tem consulta, conforme os casos de consulta comuns.

## Limite importante da Recepção

Os serviços de Recepção ainda estão implementados como mocks em memória no navegador. Guards e ações ocultas no Vue melhoram a interface, mas não são uma barreira de segurança. Até que cada operação de domínio seja transferida para um endpoint FastAPI protegido, esse estado local não deve ser tratado como dado persistente nem como fluxo pronto para produção. O backend desta etapa protege os endpoints de dados que já existem; ele não cria nem simula endpoints de negócio da Recepção.

O mock de usuários não é uma ferramenta de provisionamento. A tela antiga de gestão de usuários permanece indisponível; atribuições institucionais dependem de governança aprovada pelo HC.
