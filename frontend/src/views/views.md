# views/

Páginas da aplicação. Cada arquivo aqui corresponde a uma rota registrada em `router/`. É aqui que a lógica específica de cada tela vive — composição de componentes, chamadas a stores/services, regras de exibição daquela página específica.

## Responsabilidade de uma view

- Buscar/preparar os dados que a página precisa (via stores e/ou `services/`).
- Compor a página usando os componentes reutilizáveis de `components/` (não recriar inputs, botões, tabelas, modais do zero).
- Tratar estados de carregamento/erro específicos daquela tela.
- Aplicar regras de exibição específicas do papel/permissão do usuário, quando necessário (reaproveitando o que já vem do store de sessão — não reimplementando a regra de permissão).

## O que NÃO deve estar numa view

- Lógica de autenticação/token (isso é do store de sessão + `services/api.ts`).
- Definição de quais rotas existem ou layout a usar (isso é do `router/` + `App.vue`).
- Estilo de componentes base (botão, card, tabela) — isso é de `components/`. A view só usa, não redefine.

## Convenção de nomenclatura e organização

- Um arquivo por página/rota, nome em PascalCase, mesmo nome usado em `name` da rota.
- Se uma página específica cresce muito (formulários grandes, várias seções), extraia subcomponentes para uma subpasta dentro de `components/` (ex: `components/nomeDaFeature/`), e mantenha a view como "orquestradora" — ela monta o fluxo, mas a complexidade de UI fica nos componentes.

## Como adicionar uma nova view

1. Crie o arquivo em `views/NomeDaPagina.vue`.
2. Registre a rota correspondente em `router/index.ts` (path, name, component, meta necessário).
3. Reaproveite componentes existentes de `components/` antes de criar novos.
4. Se precisar de dados da API, use (ou crie) a função correspondente em `services/`.
5. Se precisar de estado compartilhado entre páginas, use (ou crie) o store correspondente em `stores/` — não duplique estado local que já existe globalmente.