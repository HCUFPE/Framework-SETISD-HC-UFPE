# utils/

Funções puras e utilitárias, sem estado e sem dependência de Vue (não usam `ref`, `computed`, nem acessam stores). Se a função precisa de estado que persiste entre chamadas (ex: um contador), ela não pertence aqui — vai para `stores/` (ver exemplo do `examSequence.ts`).

## Responsabilidade desta pasta

- Transformação e formatação de dados (datas, strings, códigos, números).
- Funções que recebem parâmetros e retornam um valor, sem efeitos colaterais.
- Lógica reaproveitável em múltiplas views/components que não justifica um composable nem um store.

## O que NÃO entra aqui

- Funções que dependem de estado global ou precisam ser reativas — isso é `stores/`.
- Chamadas à API — isso é `services/`.
- Lógica de UI/Vue (lifecycle hooks, `ref`, `computed`, templates) — isso é `components/` ou um composable dedicado.

## Arquivos atuais

- **examCode.ts** — Formata e deriva os códigos de identificação dos exames (padrão `PREFIXO-SEQUENCIAL/ANO.SEMESTRE`, ex: `HP-0001/26.1`). Não gera o número sequencial em si (isso é responsabilidade do `stores/examSequence.ts`) — só formata e deriva códigos a partir de um sequencial já existente. Útil quando um exame "nasce" de outro (ex: IHQ pedido a partir de um HP já registrado) e precisa manter o mesmo sequencial, só trocando o prefixo.

## Convenção de uma função utilitária

```ts
/**
 * Descreve o que a função faz, em 1 linha.
 * Inclui um exemplo de uso se o formato de saída não for óbvio.
 */
export function nomeDaFuncao(param: Tipo): TipoRetorno {
  // ...
}
```

- Sempre tipada (TypeScript), sem `any` solto.
- Sempre com comentário JSDoc quando o nome da função não deixar claro o formato exato da saída (datas, códigos, strings formatadas) — quem usa a função não deveria precisar abrir o arquivo pra saber o que ela devolve.
- Funções pequenas e focadas em uma única transformação. Se a função está fazendo duas coisas (ex: gerar E formatar), considere separar em duas funções, como fizemos com `examCode.ts` (gerar fica no store, formatar fica aqui).

## Como adicionar uma nova função utilitária

1. Verifique se já existe um arquivo do mesmo domínio (ex: outra função relacionada a códigos de exame vai em `examCode.ts`, não num arquivo novo).
2. Se for um domínio novo, crie um arquivo dedicado (`nomeDoDominio.ts`), não um arquivo genérico `helpers.ts`/`misc.ts` — fica difícil de achar depois.
3. Exporte funções nomeadas (`export function`), não um objeto único com vários métodos.
4. Documente aqui, na lista de "Arquivos atuais", o que a função faz e por que ela existe — principalmente se ela reflete uma regra de negócio específica (como o reset semestral do `examCode.ts`), não só uma transformação genérica.