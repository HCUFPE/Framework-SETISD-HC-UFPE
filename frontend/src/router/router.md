# router/

Define as rotas da aplicação e controla o acesso a cada uma.

## Responsabilidade desta pasta

- Mapear cada URL (path) para um componente de página (view).
- Definir, via `meta`, características de cada rota: layout a ser usado, se exige autenticação, se exige um papel/permissão específico, etc.
- Rodar guards de navegação (`beforeEach`) que decidem se a navegação pode acontecer.

## Estrutura de uma rota

```ts
{
  path: '/algo',
  name: 'NomeDaRota',
  component: AlgumaView,
  meta: {
    layout: 'NomeDoLayout',   // opcional — qual layout envolve essa página
    requiresAuth: true,       // opcional — exige usuário logado
    roles: ['recepcao'],      // opcional — exige papel(is) específico(s), se aplicável
  },
}
```

`meta` é livre — qualquer chave nova adicionada aqui precisa ser tratada manualmente no guard (`beforeEach`) ou em `App.vue`, não tem efeito por si só.

## Guard de navegação (`beforeEach`)

Roda antes de toda troca de rota. É o lugar central para regras de "pode ou não pode entrar nessa página":
- Lê o `meta` da rota de destino.
- Consulta o(s) store(s) relevante(s) (ex: store de autenticação) para checar permissão.
- Decide: deixa passar (`next()`) ou redireciona (`next({ name: 'OutraRota' })`).

Toda regra de acesso baseada em papel/perfil de usuário deve ser centralizada aqui (ou num helper chamado por aqui), e não duplicada dentro de cada view.

## Como adicionar uma nova rota

1. Crie a view em `views/`.
2. Importe o componente aqui.
3. Adicione a entrada em `routes` com `path`, `name`, `component`.
4. Defina o `meta` necessário (layout, auth, papéis).
5. Se a regra de acesso for nova (ex: um novo tipo de papel), atualize o `beforeEach` para tratá-la.

## Como adicionar um novo tipo de restrição de acesso

Não crie `if`s soltos nas views para isso. Sempre que possível, resolva em duas camadas:
- **Router (`beforeEach`)**: bloqueia a navegação antes mesmo de a página carregar (ex: redireciona pra login/erro).
- **View**: trata casos finos de UI (ex: esconder um botão específico), reaproveitando o mesmo dado de permissão do store — nunca reimplementando a regra.