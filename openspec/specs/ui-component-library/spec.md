# ui-component-library Specification

## Purpose

Define o comportamento observável dos componentes reutilizáveis do frontend (botão, tabela, modal, badge, passos, abas, alerta e filtros), para que todas as telas do sistema os usem de forma consistente no tema visual do framework.

## Requirements

### Requirement: Variantes e tamanhos do botão
O botão SHALL oferecer as variantes `primary`, `secondary`, `info`, `success`, `warning`, `danger`, `default` e `outline`, e os tamanhos `sm` e `md` (padrão `md`), todos nas cores do tema "Paper".

#### Scenario: Botão secundário
- **WHEN** uma tela usa o botão com a variante `secondary`
- **THEN** o botão é exibido com o estilo secundário próprio, e não com o estilo `default`

#### Scenario: Botão pequeno
- **WHEN** uma tela usa o botão com o tamanho `sm`
- **THEN** o botão é exibido com altura, espaçamento e fonte menores que o tamanho `md`

#### Scenario: Botão de contorno
- **WHEN** uma tela usa a variante `outline`
- **THEN** o botão é exibido com fundo transparente, borda e texto na cor primária

### Requirement: Tipo padrão do botão
O botão SHALL ter o tipo `button` por padrão e só SHALL enviar formulário quando declarado explicitamente com o tipo `submit`.

#### Scenario: Botão sem tipo dentro de formulário
- **WHEN** o usuário clica em um botão sem tipo declarado dentro de um formulário (ex.: "Consultar AD" no cadastro de usuário)
- **THEN** apenas a ação do botão é executada e o formulário não é enviado

#### Scenario: Botão de envio
- **WHEN** o usuário clica em um botão declarado com tipo `submit`
- **THEN** o formulário é enviado

### Requirement: Botão em carregamento
O botão em estado de carregamento SHALL exibir um indicador de progresso, ficar desabilitado e manter sua largura.

#### Scenario: Ação em andamento
- **WHEN** o botão está em carregamento
- **THEN** um indicador giratório é exibido junto ao texto e cliques não disparam a ação

### Requirement: Compatibilidade da tabela
A tabela SHALL continuar exibindo os dados com o uso atual (lista de colunas com texto e chave e lista de itens), sem exigir alterações nas telas existentes.

#### Scenario: Uso existente
- **WHEN** a tela de exemplo de pacientes renderiza a tabela com colunas e itens, sem as novas opções
- **THEN** a tabela exibe os mesmos dados, colunas e ações de antes

### Requirement: Célula personalizada na tabela
A tabela SHALL permitir que a tela defina o conteúdo exibido em uma coluna específica (ex.: badge de status, nome com prontuário, link), mantendo o texto simples nas demais colunas.

#### Scenario: Coluna de status com badge
- **WHEN** a tela define um conteúdo próprio para a coluna "Status"
- **THEN** essa coluna exibe o conteúdo definido e as demais exibem o valor em texto

### Requirement: Linha clicável na tabela
A tabela SHALL permitir que a tela seja avisada do clique em uma linha, informando o item correspondente, e SHALL permitir acionar a linha pelo teclado (Enter) quando ela tiver foco.

#### Scenario: Clique na linha
- **WHEN** o usuário clica em uma linha de uma tabela com linhas clicáveis
- **THEN** a tela recebe o item da linha clicada

#### Scenario: Clique em ação dentro da linha
- **WHEN** o usuário clica em um botão da coluna "Ações" de uma linha clicável
- **THEN** apenas a ação do botão é executada, sem disparar o clique da linha

#### Scenario: Enter na linha
- **WHEN** uma linha clicável tem foco e o usuário pressiona Enter
- **THEN** a tela recebe o item da linha, como no clique

### Requirement: Destaque de linha na tabela
A tabela SHALL permitir que a tela indique quais linhas devem ser destacadas visualmente (ex.: casos urgentes), com uma marcação lateral e fundo na cor de perigo do tema.

#### Scenario: Linha urgente
- **WHEN** a tela indica que um item deve ser destacado
- **THEN** a linha desse item é exibida com marcação lateral e fundo de destaque

### Requirement: Paginação da tabela
A tabela SHALL permitir paginação com tamanho de página configurável, exibindo o intervalo atual e o total ("Exibindo 1–10 de 42") e controles de página anterior e próxima, desabilitados nos limites.

#### Scenario: Primeira página
- **WHEN** a tabela tem 42 itens e tamanho de página 10
- **THEN** são exibidos os itens 1 a 10, o texto "Exibindo 1–10 de 42" e o controle "anterior" fica desabilitado

#### Scenario: Última página
- **WHEN** o usuário avança até a última página
- **THEN** são exibidos os itens 41 e 42 e o controle "próxima" fica desabilitado

#### Scenario: Mudança dos dados
- **WHEN** a lista de itens muda (ex.: um filtro é aplicado) e a página atual deixa de existir
- **THEN** a tabela volta para a primeira página

#### Scenario: Sem paginação
- **WHEN** a tela não define tamanho de página
- **THEN** todos os itens são exibidos e os controles de paginação não aparecem

### Requirement: Carregamento e vazio na tabela
A tabela SHALL exibir um estado de carregamento quando indicado pela tela e SHALL exibir a mensagem de lista vazia definida pela tela, usando "Nenhum dado encontrado." quando nenhuma for definida.

#### Scenario: Carregando
- **WHEN** a tela indica que os dados estão sendo carregados
- **THEN** a tabela exibe um indicador de carregamento no lugar das linhas

#### Scenario: Vazio com mensagem própria
- **WHEN** não há itens e a tela definiu a mensagem "Nenhum caso encontrado para os filtros."
- **THEN** essa mensagem é exibida

### Requirement: Largura do modal
O modal SHALL oferecer as larguras `sm`, `md`, `lg` e `xl`, mantendo a largura atual como padrão, e SHALL permitir rolagem interna do conteúdo quando ele exceder a altura da tela.

#### Scenario: Modal largo
- **WHEN** uma tela abre o modal com largura `xl`
- **THEN** o modal ocupa a largura maior, limitada à largura da tela em dispositivos pequenos

#### Scenario: Conteúdo longo
- **WHEN** o conteúdo do modal é mais alto que a tela
- **THEN** o corpo do modal rola internamente e o cabeçalho e o rodapé continuam visíveis

### Requirement: Fechamento do modal
O modal SHALL fechar ao clicar fora, pela tecla Esc e pelo botão de fechar, e SHALL permitir que a tela desative o fechamento ao clicar fora para evitar a perda de dados digitados.

#### Scenario: Clique fora com fechamento desativado
- **WHEN** a tela desativou o fechamento ao clicar fora e o usuário clica no fundo escurecido
- **THEN** o modal permanece aberto

#### Scenario: Esc
- **WHEN** o modal está aberto e o usuário pressiona Esc
- **THEN** o modal fecha

### Requirement: Badge
O sistema SHALL oferecer um badge de texto curto com as variantes `default`, `primary`, `info`, `success`, `warning` e `danger`, com contraste legível em cada uma.

#### Scenario: Badge de urgência
- **WHEN** uma tela exibe o badge "URGENTE" com a variante `danger`
- **THEN** o badge aparece com fundo claro e texto escuro na tonalidade de perigo do tema

### Requirement: Indicador de passos
O sistema SHALL oferecer um indicador de passos que exibe a lista de passos com número e rótulo, distinguindo visualmente os passos concluídos, o passo atual e os passos futuros, e marcando o passo atual para leitores de tela.

#### Scenario: Passo atual
- **WHEN** o indicador recebe 4 passos e o passo atual é o 2
- **THEN** o passo 1 aparece como concluído, o 2 como atual e os passos 3 e 4 como futuros

### Requirement: Abas
O sistema SHALL oferecer abas que exibem um painel por vez, indicam a aba ativa, permitem trocar de aba por clique e pelas setas do teclado e podem exibir um contador ao lado do rótulo.

#### Scenario: Troca por clique
- **WHEN** o usuário clica na aba "Histórico"
- **THEN** a aba "Histórico" fica ativa e seu painel é exibido no lugar do anterior

#### Scenario: Troca por teclado
- **WHEN** uma aba tem foco e o usuário pressiona a seta para a direita
- **THEN** a próxima aba recebe foco e fica ativa

### Requirement: Alerta
O sistema SHALL oferecer um alerta em bloco com as variantes `info`, `success`, `warning` e `danger`, com ícone, título opcional e texto, podendo ser fechado quando a tela permitir.

#### Scenario: Alerta de perigo
- **WHEN** uma tela exibe um alerta `danger` com o título "Acionar equipe de plantão"
- **THEN** o alerta aparece com ícone e cores de perigo do tema e com o título em destaque

#### Scenario: Alerta fechável
- **WHEN** o alerta permite fechar e o usuário clica no botão de fechar
- **THEN** a tela é avisada para ocultar o alerta

### Requirement: Etiquetas de filtro
O sistema SHALL oferecer uma lista de etiquetas que mostra os filtros ativos ("Status: Recebido"), permite remover cada filtro individualmente e oferece a ação "Limpar filtros" quando houver ao menos um filtro ativo.

#### Scenario: Remover um filtro
- **WHEN** o usuário clica no botão de remover da etiqueta "Tipo: HP"
- **THEN** a tela é avisada para remover apenas o filtro "Tipo"

#### Scenario: Limpar todos
- **WHEN** há filtros ativos e o usuário clica em "Limpar filtros"
- **THEN** a tela é avisada para remover todos os filtros

#### Scenario: Sem filtros
- **WHEN** não há filtros ativos
- **THEN** nenhuma etiqueta nem a ação "Limpar filtros" são exibidas

### Requirement: Galeria de componentes
A página "Componentes" SHALL exibir um exemplo de cada componente e variante, incluindo os estados de hover, desabilitado, carregamento, vazio e paginação, para servir de referência às telas do sistema.

#### Scenario: Consulta da galeria
- **WHEN** o usuário acessa a página "Componentes"
- **THEN** são exibidos exemplos de botão (variantes, tamanhos, carregamento e desabilitado), tabela (célula personalizada, linha clicável, destaque, paginação, carregamento e vazio), modal (larguras), badge, passos, abas, alerta e etiquetas de filtro
