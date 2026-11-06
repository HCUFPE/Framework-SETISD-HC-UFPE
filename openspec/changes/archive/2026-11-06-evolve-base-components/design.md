# Design

## Context

- Os componentes ficam em `frontend/src/components/` e usam `<script setup lang="ts">` com tema Tailwind CSS 4 definido em `frontend/src/index.css` (`@theme`, cores `paper-*`). O `tailwind.config.js` não é lido pelo Tailwind 4 e não deve ser usado para tokens.
- O Tailwind CSS 4 removeu o `cursor: pointer` padrão de `<button>`. Hoje nenhum componente o reaplica, então botões aparecem com a seta.
- Usos atuais que precisam continuar funcionando: `DataTable` em `Pacientes.vue` (colunas + itens + slot `actions`); `Button` em todas as views (inclusive `size="sm"`, que hoje é ignorado, e `variant="secondary"`, que hoje cai em `default`); `Modal` em `Exemplos.vue` e `Configuracoes.vue` (largura fixa `max-w-lg`).
- Todos os botões que enviam formulário já declaram `type="submit"` (`Login.vue`, `Exemplos.vue`, `Configuracoes.vue`). O único `Button` sem `type` dentro de formulário é "Consultar AD" (`Configuracoes.vue:165`), que hoje envia o formulário por engano.
- O frontend não tem executor de testes automatizados.

## Goals / Non-Goals

**Goals:**
- Retorno de interação consistente em todo elemento clicável, aplicado uma vez na base e reforçado nos componentes.
- APIs de componentes pequenas, tipadas e compatíveis com os usos atuais.
- Componentes acessíveis por teclado (foco visível, Enter nas linhas, setas nas abas, `aria-current` nos passos).

**Non-Goals:**
- Paginação, ordenação ou filtragem no servidor: a tabela pagina apenas a lista recebida.
- Ordenação por coluna e seleção de linhas (não exigidas pelo fluxo de recepção).
- Trocar a identidade visual: continua o tema "Paper" e a fonte Nunito.
- Introduzir biblioteca de componentes de terceiros.

## Decisions

### 1. Cursor e foco definidos na camada base do CSS
Adicionar em `index.css` uma regra `@layer base` que aplica `cursor: pointer` a `button`, `[role="button"]`, `[role="tab"]`, `a[href]`, `summary` e `label[for]` habilitados, e `cursor: not-allowed` aos desabilitados (`:disabled`, `[aria-disabled="true"]`). Também criar a classe utilitária `focus-ring` (`focus-visible:` com anel na cor `paper-primary`), usada pelos componentes.
- **Por quê:** é a recomendação oficial do Tailwind 4 para restaurar o cursor e cobre de uma vez os elementos que não usam o `Button`.
- **Alternativa descartada:** colocar `cursor-pointer` elemento a elemento. É fácil esquecer em telas novas.
- Hover e estado pressionado continuam por componente (`hover:` e `active:`), porque dependem da cor de cada variante.

### 2. Tokens de cor suaves e fortes
Acrescentar ao `@theme` versões `-soft` (fundo claro) e `-strong` (texto escuro) para `primary`, `info`, `success`, `warning` e `danger`, além de `secondary`. Badge, alerta e destaque de linha usam `bg-paper-<v>-soft text-paper-<v>-strong`.
- **Por quê:** as cores atuais (ex.: `#eb5e28`, `#f3bb45`) não têm contraste suficiente como texto sobre fundo claro. Os pares soft/strong garantem leitura sem sair da paleta.
- **Alternativa descartada:** opacidade (`bg-paper-danger/15`) com o texto na cor base. O contraste do texto continua baixo.

### 3. `Button`
- Props: `variant` (união tipada, inclui `secondary` e `outline`), `size` (`sm` | `md`, padrão `md`), `type` (`button` | `submit` | `reset`, padrão `button`), `loading`, `disabled`.
- O carregamento mostra um spinner SVG inline antes do texto, e o botão fica desabilitado.
- Estados: `hover:` na cor `-hover`, `active:` com escurecimento e leve redução de escala, e `focus-ring`.
- **Por quê do padrão `button`:** evita envios acidentais e corrige o bug do "Consultar AD". Os envios existentes já são explícitos.

### 4. `DataTable`
- Mantém as props `headers` e `items` e o slot `actions`.
- Adiciona:
  - Slots dinâmicos `cell-<chave>` com `{ item, value }`, para conteúdo personalizado por coluna (ex.: `#cell-status`).
  - Prop `clickable` e evento `row-click(item)`. Com `clickable`, a linha recebe `tabindex="0"`, cursor, hover e Enter. A célula de ações usa `@click.stop`.
  - Prop `highlight?: (item) => boolean`, que aplica borda esquerda e fundo `paper-danger-soft`.
  - Prop `pageSize?: number`. Sem ela, não há paginação. Com ela, o estado da página é interno, há rodapé "Exibindo X–Y de N" e botões anterior/próxima, e um `watch` em `items` volta para a página 1 quando a página atual deixa de existir.
  - Props `loading` e `emptyText` (padrão "Nenhum dado encontrado.").
- **Alternativa descartada:** controlar a página pela view (`v-model:page`). Fica para quando houver paginação no servidor; o fluxo de recepção usa dados mockados.

### 5. `Modal`
- Props novas: `size` (`sm` | `md` | `lg` | `xl`, padrão `lg`, que equivale ao `max-w-lg` atual) e `closeOnBackdrop` (padrão `true`).
- O corpo ganha `max-h` relativo à tela com `overflow-y-auto`, e cabeçalho e rodapé ficam fixos.
- O botão de fechar ganha `aria-label`, `focus-ring` e estado `active:`.

### 6. Componentes novos (props essenciais)
- `Badge`: `variant`, slot padrão para o texto, `size` opcional.
- `Stepper`: `steps: { label: string }[]`, `current: number` (índice 0). Indica concluído (ícone de check), atual (`aria-current="step"`) e futuro. É apenas exibição, não navega.
- `Tabs`: `tabs: { key, label, count? }[]` e `v-model` com a chave ativa. Usa `role="tablist"`/`tab`/`tabpanel`, setas esquerda/direita e slot `#<key>` por painel.
- `Alert`: `variant`, `title?`, `dismissible?`, evento `dismiss`, ícone Heroicons por variante e slot padrão para o texto.
- `FilterChips`: `chips: { key, label }[]`, eventos `remove(key)` e `clear`. Não renderiza nada sem chips.

### 7. Ajustes nos elementos clicáveis existentes
Aplicar hover, estado pressionado e foco em:
- `DefaultLayout.vue`: links do menu, botão do menu móvel e cabeçalho que recolhe o menu.
- `ProfileDropdown.vue`.
- Os cards clicáveis de `Home.vue`.
- Os botões de ícone de `Configuracoes.vue`.
- O botão de mostrar senha de `Login.vue`.

O cursor já vem da regra base. Remover de `Login.vue` as classes que sobrescrevem a cor do botão secundário (`bg-gray-500 hover:bg-gray-600`), já que a variante `secondary` passa a existir.

### 8. Verificação sem executor de testes
A verificação será:
- `npx vue-tsc --noEmit`;
- `npx vite build` com saída em diretório temporário, para não sujar `src/static/dist`;
- `python audit_framework.py .` com 100%;
- roteiro manual na galeria `/componentes` e nas telas existentes (Pacientes, Configurações, Login).

- **Alternativa considerada:** adicionar Vitest + Vue Test Utils. É uma dependência nova não documentada em `06-arquitetura.md`. Fica como decisão separada do time.

## Risks / Trade-offs

- [O tipo padrão `button` muda o comportamento de algum `Button` sem `type` usado como envio] → Mitigação: o levantamento mostrou que todos os envios declaram `type="submit"`. A tarefa de verificação reconfere com busca no código e testa Login e Configurações.
- [A regra base de cursor altera elementos de terceiros (ex.: botões do vue-toastification)] → Efeito desejado (cursor de mão em botões); sem impacto funcional.
- [Paginação interna se perde ao recriar o componente] → Aceitável para dados mockados. Revisar quando houver paginação no servidor.
- [Novos tokens de cor ampliam o tema] → Ficam documentados na galeria e seguem a nomenclatura `paper-*` existente.
- [Sem testes automatizados, regressões visuais dependem do roteiro manual] → A galeria cobre cada variante e estado, e o roteiro fica listado nas tarefas.
