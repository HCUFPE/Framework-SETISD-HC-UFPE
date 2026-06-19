# components/

Componentes de UI reutilizáveis — blocos visuais sem lógica de negócio, usados por várias views/layouts.

## Estrutura de pastas

Cada componente (ou grupo de componentes muito relacionados) vive na sua própria subpasta, nomeada em PascalCase ou kebab-case (manter consistência com o resto do projeto):

```
components/
    └──Button/
        └──Button.vue
```

Se um componente precisar de subcomponentes auxiliares que não fazem sentido fora dele (ex: `ModalHeader`, `ModalFooter` usados só dentro de `Modal`), eles entram dentro da mesma pasta do componente pai:

```
Modal/
    ├──Modal.vue
    ├──ModalHeader.vue
    └──ModalFooter.vue
```

Se um componente tiver lógica reutilizável separada da view (ex: um composable específico dele), também pode entrar na mesma pasta:

```
DataTable/
    ├──DataTable.vue
    └──useDataTableSort.ts
```

## Responsabilidade de um componente nesta pasta

- Receber dados/comportamento via `props` e `emits` — não buscar dados de API nem acessar stores diretamente (exceção: componentes que são inerentemente ligados a um store, como um dropdown de perfil do usuário logado — nesse caso, documentar isso no próprio componente).
- Ser agnóstico de onde é usado. Um componente daqui não deve saber "em qual página está" ou ter lógica de negócio específica de uma feature.
- Cobrir variações via props (ex: `variant`, `size`) em vez de criar um componente novo pra cada variação visual.

## O que NÃO entra aqui

- Componentes que só fazem sentido dentro de uma página específica e não serão reaproveitados — esses ficam dentro da própria pasta da view ou numa subpasta dedicada (ex: `views/NomeDaPagina/components/`), não em `components/`.
- Lógica de chamada à API (isso é de `services/`).
- Lógica de rota/navegação além do básico (ex: um link interno é ok; redirecionamento condicional complexo não).

## Convenção de um componente

```vue
<template>
  <!-- markup -->
</template>

<script setup lang="ts">
// props tipadas
interface Props {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}
const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
});

// emits explícitos
const emit = defineEmits<{
  click: [event: MouseEvent];
}>();
</script>
```

- Sempre tipar props e emits (TypeScript + `defineProps`/`defineEmits`).
- Usar `withDefaults` para valores padrão em vez de lógica condicional dentro do template.
- Expor slots (`<slot />`, `<slot name="header" />` etc.) para conteúdo flexível em vez de multiplicar props para cada pedaço de conteúdo.

## Como adicionar um componente novo

1. Verifique se já existe algo parecido (variante de um componente existente) antes de criar um novo do zero.
2. Crie a subpasta em `components/NomeDoComponente/`.
3. Crie `NomeDoComponente.vue` dentro dela, seguindo a convenção acima.
4. Se precisar de subcomponentes/composables exclusivos dele, coloque na mesma pasta.
5. Use nas views/layouts importando diretamente: `import NomeDoComponente from '@/components/NomeDoComponente/NomeDoComponente.vue'`.

## Quando migrar um componente "local" para esta pasta

Se um componente criado dentro de uma view específica passa a ser usado em uma segunda página, mova-o para `components/` nesse momento — não antes (evita abstração prematura) e não depois (evita duplicação de código).

