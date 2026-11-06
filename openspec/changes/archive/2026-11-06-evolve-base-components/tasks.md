# Tasks

## 1. Base de estilo e interação

- [x] 1.1 Adicionar em `frontend/src/index.css` os tokens `paper-secondary` e as versões `-soft`/`-strong` de primary, info, success, warning e danger; verificar com um build temporário (`npx vite build --outDir <tmp>`) que as classes `bg-paper-danger-soft` e `text-paper-danger-strong` aparecem no CSS gerado
- [x] 1.2 Adicionar em `index.css` a regra `@layer base` de cursor (pointer para clicáveis habilitados, not-allowed para desabilitados) e a utilidade `focus-ring`; verificar no navegador que um `<button>` nativo qualquer exibe o cursor de mão
- [x] 1.3 Corrigir no `LoadingIndicator.vue` a classe `bg-opacity-50` (sintaxe do Tailwind 3) para `bg-black/50`; verificar que o fundo do carregamento fica semitransparente

## 2. Button

- [x] 2.1 Reescrever as props do `Button.vue` (variant tipada com `secondary` e `outline`, `size` sm/md, `type` com padrão `button`, `loading`, `disabled`) com estados de hover, estado pressionado, `focus-ring` e spinner de carregamento; verificar com `npx vue-tsc --noEmit`
- [x] 2.2 Conferir com `grep -n "<Button" frontend/src` que todo botão de envio declara `type="submit"`, remover as classes que sobrescrevem a cor em `Login.vue` e verificar manualmente que o login envia, que "Consultar AD" em Configurações não envia o formulário e que "Incluir Usuário" envia
- [x] 2.3 Adicionar à galeria (`Exemplos.vue`) as variantes, os tamanhos, o carregamento e o estado desabilitado do botão; verificar visualmente em `/componentes` o hover, o clique, o foco por Tab e o cursor de cada um

## 3. DataTable

- [x] 3.1 Adicionar ao `DataTable.vue` os slots `cell-<chave>`, a prop `clickable` com evento `row-click` (clique e Enter, sem disparo a partir da célula de ações), a prop `highlight`, `loading` e `emptyText`; verificar com `vue-tsc` e que `/exemplo` (Pacientes) continua igual
- [x] 3.2 Adicionar ao `DataTable.vue` a paginação no cliente (`pageSize`, rodapé "Exibindo X–Y de N", anterior/próxima desabilitados nos limites, volta à página 1 quando a página deixa de existir); verificar na galeria com 42 itens e tamanho 10
- [x] 3.3 Adicionar à galeria os exemplos da tabela (célula com badge, linha clicável com toast, linha destacada, paginação, carregamento e vazio com mensagem própria); verificar cada cenário da spec `ui-component-library` sobre tabela em `/componentes`

## 4. Modal

- [x] 4.1 Adicionar ao `Modal.vue` as props `size` (padrão `lg`) e `closeOnBackdrop` (padrão `true`), a rolagem interna do corpo e `aria-label`/`focus-ring`/estado pressionado no botão de fechar; verificar que os modais de Configurações e da galeria mantêm a largura atual
- [x] 4.2 Adicionar à galeria os exemplos de larguras, conteúdo longo e fechamento por clique fora desativado; verificar Esc, botão de fechar e clique fora em `/componentes`

## 5. Componentes novos

- [x] 5.1 Criar `Badge.vue` com as variantes da spec e adicionar o exemplo na galeria; verificar o contraste do texto em cada variante
- [x] 5.2 Criar `Alert.vue` (variantes, ícone, título, `dismissible`/`dismiss`) e adicionar o exemplo na galeria; verificar o fechamento do alerta fechável
- [x] 5.3 Criar `Stepper.vue` (concluído, atual com `aria-current="step"`, futuro) e adicionar na galeria um exemplo de 4 passos com botões para avançar e voltar; verificar os três estados visuais
- [x] 5.4 Criar `Tabs.vue` (`v-model`, contador, papéis ARIA, setas do teclado, slot por painel) e adicionar o exemplo na galeria; verificar a troca por clique e pelas setas
- [x] 5.5 Criar `FilterChips.vue` (eventos `remove` e `clear`, oculto sem chips) e adicionar na galeria um exemplo ligado a filtros fictícios; verificar a remoção individual, "Limpar filtros" e o estado sem filtros

## 6. Elementos clicáveis existentes

- [x] 6.1 Aplicar hover, estado pressionado e `focus-ring` aos links e botões do `DefaultLayout.vue` (menu, botão móvel, cabeçalho recolhível) e ao `ProfileDropdown.vue` (botão de perfil e "Sair"); verificar com mouse e Tab
- [x] 6.2 Aplicar hover, estado pressionado e `focus-ring` aos cards de `Home.vue`, aos botões de ícone de `Configuracoes.vue` e ao botão de mostrar senha de `Login.vue`; verificar com mouse e Tab

## 7. Verificação integrada

- [x] 7.1 Rodar `npx vue-tsc --noEmit` em `frontend/` sem erros, `npx vite build --outDir <diretório temporário>` com sucesso e `python audit_framework.py .` com 11/11 (100%)
- [x] 7.2 Percorrer o roteiro manual: Login (envio e mostrar senha), Início (cards), Componentes (todos os exemplos), Exemplo/Pacientes (tabela e botões `sm`), Configurações (Consultar AD, incluir, editar e ativar usuário) e menu lateral recolhido e no celular; registrar no resumo da entrega qualquer desvio encontrado
