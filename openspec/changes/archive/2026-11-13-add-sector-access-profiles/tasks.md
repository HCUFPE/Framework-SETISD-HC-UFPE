# Tasks

## 1. Confirmar política e contratos

- [x] 1.1 Definir catálogo inicial de permissões estáveis e manter sem concessão operações sem associação explícita nos casos de uso.
- [x] 1.2 Configurar o Adapter mock explicitamente e bloquear seu uso em produção.

## 2. Identidade e autorização no backend

- [x] 2.1 Refatorar o provedor atual atrás do contrato de Adapter, normalizando identidade e preservando JWT/refresh existentes sem dependência de protocolo institucional.
- [x] 2.2 Implementar catálogo dos nove perfis, resolução de múltiplos perfis e permissões explícitas com 401/403 e negação por padrão.
- [x] 2.3 Expor identidade/perfis/permissões efetivos em `/api/users/me`; remover autorização por grupos do provedor.
- [x] 2.4 Criar identidades mock fictícias por perfil e sem perfil, selecionáveis apenas em desenvolvimento/testes; impedir seleção arbitrária e uso em produção.
- [x] 2.5 Proteger endpoints existentes e operações de Recepção expostas no backend; usar dependências por router/operação e nunca confiar em ocultação de UI.
- [x] 2.6 Registrar autor autenticado e auditoria em mutações usando o helper existente; não aceitar autor do cliente.

## 3. Recepção e frontend

- [x] 3.1 Migrar as operações disponíveis de Recepção para serviços HTTP e persistência backend; impressão é local ao navegador e a associação IHQ será automática em mecanismo futuro.
- [x] 3.2 Atualizar Pinia para identidade e permissões; adicionar guards de permissão às rotas e ocultar ações/menu indisponíveis.
- [x] 3.3 Tratar respostas 401/403 em navegação e mutações sem apresentar sucesso falso; preservar interceptadores Axios.
- [x] 3.4 Confirmar que nenhuma tela, endpoint ou permissão operacional de módulo futuro foi introduzida.

## 4. Verificação

- [x] 4.1 Testar catálogo de nove perfis, usuário sem perfil, múltiplos perfis, credenciais inválidas e bloqueio do mock em produção.
- [x] 4.2 Testar permissões positivas e negativas no backend, incluindo chamada direta aos endpoints de Recepção e acesso sem token; `tests/test_reception_api.py` e `tests/test_sector_access_profiles.py` passaram.
- [x] 4.3 Testar que o cliente não consegue forjar perfis/permissões no login e verificar autoria e conteúdo de auditoria das mutações. A alteração de associações de usuários é fora desta mudança, que não oferece gestão de perfis.
- [x] 4.4 Revisar guards de rotas e controles condicionais por permissão no frontend; as chamadas diretas continuam protegidas no backend. `vue-tsc` e build passaram.
- [x] 4.5 Executar `npx vue-tsc --noEmit`, a suíte Pytest, `npm run build` e `python audit_framework.py .`. TypeScript, build e Pytest (41 testes) passaram. O auditor reportou 10/11 porque não há associação RBAC persistida no APP_DB; a exceção foi aceita para esta mudança, sem implementar autenticação institucional.

## Acceptance Criteria

- Os nove identificadores de perfil existem, sem acesso funcional fictício a módulos não implementados.
- O servidor concede somente permissões explícitas do catálogo vigente; perfil ausente ou operação sem concessão é negado. O catálogo pode evoluir por módulo sem exigir uma matriz global completa para concluir esta mudança.
- Usuário mock pode ser trocado em ambiente de desenvolvimento/testes e mock não inicia em produção.
- A camada de negócio depende da identidade normalizada, não do protocolo ou dos grupos do provedor.
- Operações da Recepção protegidas recusam chamadas diretas sem permissão; a interface reflete os mesmos direitos.
- Mutação auditável identifica o usuário autenticado e não permite forjar o autor via requisição.
- Nenhum protocolo institucional é escolhido ou implementado nesta mudança.
