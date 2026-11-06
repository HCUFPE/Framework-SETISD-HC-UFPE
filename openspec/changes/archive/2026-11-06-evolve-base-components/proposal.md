# Proposal

## Why

O fluxo de recepção (recepção de amostras, consulta de casos, rejeições e devoluções e detalhe do caso) precisa de tabelas paginadas com células ricas, badges de status/urgência, passos, abas, alertas e filtros, e a biblioteca de componentes do framework hoje só cobre o básico (`Button`, `Card`, `DataTable`, `Modal`). Além disso, elementos clicáveis não dão retorno visual consistente: desde o Tailwind CSS 4 o botão nativo usa o cursor padrão (seta), e vários elementos não têm estado de hover, clique ou foco por teclado. Evoluir a base antes do fluxo de recepção evita que cada tela crie a sua própria variação.

## What Changes

- Padronizar o retorno de interação de todo elemento clicável: cursor de mão, estado de hover, estado de clique (pressionado), foco visível por teclado e cursor de "não permitido" quando desabilitado. Aplicar aos componentes existentes (`Button`, `Modal`, `ProfileDropdown`, links do menu lateral, cards clicáveis da página inicial, botões de ação de `Configuracoes.vue` e o botão de mostrar senha do `Login.vue`).
- `Button`: tamanhos (`sm`, `md`), variantes `secondary` e "contorno" (outline), e tipo padrão `button` em vez de `submit`. Isso corrige o botão "Consultar AD" em `Configuracoes.vue`, que hoje envia o formulário ao ser clicado.
- `DataTable`: conteúdo de célula personalizável por coluna, clique em linha, destaque de linha, paginação no cliente, estado de carregamento e mensagem de vazio configurável, mantendo o uso atual (`headers` + `items`) funcionando sem alteração.
- `Modal`: largura configurável e opção de não fechar ao clicar fora (sem alterar o comportamento padrão atual).
- Novos componentes no tema "Paper": `Badge`, `Stepper`, `Tabs`, `Alert` e `FilterChips` (etiquetas de filtro removíveis com "Limpar filtros").
- Atualizar a galeria `/componentes` (`Exemplos.vue`) com exemplos de cada componente e estado, servindo de documentação viva.

Sem mudanças incompatíveis: os usos atuais dos componentes continuam com o mesmo resultado visual e funcional, exceto a correção intencional do `type` padrão do `Button`.

## Capabilities

### New Capabilities
- `ui-interaction-feedback`: retorno visual e de cursor que todo elemento clicável da interface deve oferecer (hover, clique, foco por teclado e estado desabilitado).
- `ui-component-library`: comportamento observável dos componentes reutilizáveis do frontend (botão, tabela, modal, badge, passos, abas, alerta e filtros).

### Modified Capabilities
<!-- Nenhuma: não há specs existentes em openspec/specs/. -->

## Impact

- Código: `frontend/src/index.css`, `frontend/src/components/{Button,DataTable,Modal,ProfileDropdown}.vue`, novos `frontend/src/components/{Badge,Stepper,Tabs,Alert,FilterChips}.vue`, `frontend/src/layouts/DefaultLayout.vue`, `frontend/src/views/{Exemplos,Home,Configuracoes,Login,Pacientes}.vue`.
- Dependências: nenhuma nova; usa Vue 3, Tailwind CSS 4 e Heroicons já instalados.
- Backend e APIs: sem impacto.
- Próximo change (fluxo de recepção) depende deste.
