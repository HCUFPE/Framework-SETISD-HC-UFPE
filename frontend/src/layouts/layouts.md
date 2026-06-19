# layouts/

"Cascas" visuais que envolvem as páginas. Um layout define estrutura (sidebar, header, área de conteúdo, etc.) mas não o conteúdo da página em si — isso vem da view, renderizada dentro do layout via `<router-view />`.

## Como funciona a escolha de layout

A escolha de qual layout usar para cada rota é resolvida no componente raiz (`App.vue`), com base no `meta.layout` definido em `router/`. Se uma rota não define `meta.layout`, cai num layout padrão.

```ts
// App.vue (exemplo do mecanismo, não do layout final)
const layout = computed(() => {
  return route.meta.layout === 'NomeX' ? LayoutX : LayoutPadrao;
});
```

## Convenção de um layout

- Recebe nenhuma prop obrigatória — lê o necessário de stores (ex: se mostra ou não certos itens de navegação com base em permissão do usuário).
- Sempre contém um `<router-view />` (ou slot equivalente) onde a página atual é injetada.
- Não deve conter lógica de negócio — só estrutura visual e navegação.

## Como adicionar um novo layout

1. Crie o arquivo aqui (ex: `NomeLayout.vue`).
2. Garanta que ele tem um `<router-view />` (ou `<slot />`, dependendo de como `App.vue` está implementado).
3. Registre-o no `computed` de `App.vue`.
4. Use `meta: { layout: 'NomeLayout' }` nas rotas que devem usá-lo.

## Quando criar um layout novo vs. reaproveitar

Crie um novo layout quando a **estrutura** muda (ex: tem sidebar ou não, tem header ou não). Se a estrutura é a mesma e só muda conteúdo/estilo de uma seção, isso é responsabilidade da view ou de um componente dentro do layout existente — não justifica um layout novo.