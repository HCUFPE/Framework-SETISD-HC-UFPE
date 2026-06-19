# stores/

Estado global da aplicação, gerenciado com Pinia. Cada arquivo aqui é um store independente, focado em um domínio.

## Quando criar um store novo

Crie um store quando o estado precisa ser:
- Acessado por componentes que não têm relação direta entre si (não é pai/filho), **ou**
- Persistido entre navegações (ex: sessão do usuário), **ou**
- Compartilhado por múltiplas views ao mesmo tempo.

Se o estado é local de uma única view/componente, **não** crie um store — use `ref()`/`reactive()` direto no componente.

## Convenção de um store

```ts
export const useAlgumStore = defineStore('algum', () => {
  // state
  const algo = ref(...);

  // getters (computed)
  const algoDerivado = computed(() => ...);

  // actions
  function fazerAlgo() { ... }

  return { algo, algoDerivado, fazerAlgo };
});
```

- Usa a Composition API do Pinia (`defineStore` com função, não objeto de opções).
- Tudo que precisa ser acessado de fora do store deve estar no `return`.
- Side effects assíncronos (chamadas à API) ficam em `actions`, nunca direto na view — a view só chama a action e reage ao resultado.

## Stores existentes (papéis gerais, não amarrados ao domínio do produto)

- **Autenticação/sessão**: guarda token, dados do usuário logado, estado de "está logado", e expõe ações de login/logout/restauração de sessão. Qualquer lógica de "quem pode fazer o quê" (papéis, permissões) deve viver aqui ou em um store derivado dele — não duplicar em várias views.
- **UI global**: estados de interface que não pertencem a uma tela específica (ex: loading global, tema, sidebar aberta/fechada).

## Como adicionar um novo store

1. Crie `nomeDoDominio.ts` nesta pasta.
2. Siga a convenção acima (state / getters / actions / return).
3. Documente aqui, em 2-3 linhas, o que esse store guarda e por quê precisa ser global.