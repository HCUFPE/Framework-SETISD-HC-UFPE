# Design

## Context

Os ajustes tocam o layout, a recepção, o detalhe do caso e as devoluções. Tudo roda só no frontend com mocks (`frontend/src/services/ap/mock`). O que importa para a abordagem:

- O estado do assistente de recepção (`passo`, solicitação, conferência) fica na store Pinia `recepcao` e sobrevive à navegação. Por isso, clicar em "/recepcao" estando em "/recepcao" não muda a rota nem reinicia o passo (item 7).
- O campo do topo (`components/ap/CodeScanField.vue`) chama `casosStore.resolverCodigo()`, que hoje resolve solicitação pendente, caso, item, IHQ e devolução.
- O indicador do fluxo do caso (`components/ap/caso/FluxoCaso.vue`) fica dentro de um `div` com `overflow-x-auto` em `DetalheCaso.vue`, o que gera a barra de rolagem do print.
- O título do sistema vem de `GET /api/health` (`src/version.py`, `SYSTEM_TITLE`), com fallback em `frontend/src/config/version.ts` e em `frontend/index.html`.
- Já existem `tempoDecorrido()` e `horasDesde()` em `helpers/formato.ts`, e `Modal.vue` em `components/`.
- Ícones: Heroicons é o padrão do projeto. Lucide entra só para os ícones pedidos.

## Goals / Non-Goals

**Goals:**
- Implementar os 14 itens conforme as specs delta, reaproveitando componentes e helpers existentes.
- Manter a camada de serviços tipada, para a troca futura pela API.

**Non-Goals:**
- Alterar `docs/especificacao/` (decisão do usuário). A divergência sobre `recebido_por_nome` fica registrada na proposta.
- Migrar os demais ícones para o Lucide.
- Mudar a tela Consulta de casos ou aceitar parâmetros de URL nela.
- Mudar a leitura do passo 1 da recepção. Ela continua lendo o nº AGHU e avisando sobre solicitação recebida ou devolvida.

## Decisions

### D1. Ícones com `lucide-vue-next`, importados por ícone
Instalar `lucide-vue-next`, a versão Vue do Lucide (o `lucide-react` não serve em Vue), e importar só `PanelRight`/`PanelRightOpen` ou equivalente, `Scan` e `Search`, se preferível ao `MagnifyingGlassIcon`. O pacote suporta tree-shaking, então o bundle recebe só os ícones usados.
- O ícone `scan-square` não existe no Lucide. Usar `Scan` (moldura de leitura com cantos), o mais próximo do pedido.
- O ícone de busca do topo continua o `MagnifyingGlassIcon` do Heroicons, para manter o padrão. O item 3 só pede "apenas um ícone de busca".
- Alternativa descartada: só Heroicons. O Heroicons não tem ícone de painel lateral, e o usuário escolheu o Lucide.

### D2. Botão de recolher separado do título
No topo da sidebar ficam duas coisas:
- o bloco de identidade (ícone e nome, sem ação), com o nome em `break-words`, sem `truncate`;
- um botão quadrado com `PanelRight`, `aria-label` "Recolher menu" / "Expandir menu" e `aria-expanded`.

Com o menu recolhido (`md:w-20`), o nome some e o botão fica centralizado. O cabeçalho mobile continua com o `Bars3Icon`, que abre a gaveta, e mostra o nome com `truncate`, porque lá a largura é limitada.

### D3. Nome do sistema na fonte de verdade
Trocar `SYSTEM_TITLE` em `src/version.py`, o fallback em `config/version.ts` e o `<title>` de `frontend/index.html`. O build em `src/static/dist` é regenerado pelo build e não é editado à mão.

### D4. Busca global: nova operação de serviço, sem reaproveitar `resolverCodigo`
Criar `casoService.buscar(termo, limite)`, que devolve `{ itens, total }`, com a implementação no mock e o tipo em `services/ap/types.ts`. Ela compara número interno, prontuário e nome do paciente, sem diferenciar maiúsculas, minúsculas e acentos (normalização NFD). A ordem é: número interno exato primeiro, depois a data de entrada mais recente.
- O `CodeScanField.vue` passa a ser um combobox (`role="combobox"`, `aria-controls`, `aria-activedescendant` e `role="listbox"`/`option`), com debounce de cerca de 250 ms, mínimo de 2 caracteres, setas, Enter, Esc e fechamento ao perder o foco. O F2 é mantido. Faz sentido renomear o arquivo para `CaseSearchField.vue`/`BuscaCasoField.vue`, mas a decisão final fica para a implementação. Se houver renomeação, atualizar o import no layout.
- `resolverCodigo` e o tipo `ResolucaoCodigo` deixam de ser usados pelo topo. Se nada mais os usar, remover para não ficar código morto. A recepção usa `lerCodigo` da store `recepcao`, que não depende deles.
- Alternativa descartada: filtrar `casosStore.casos` no cliente. Isso acoplaria o layout ao carregamento completo da lista e não reflete como funcionará com a API.

### D5. Reinício da recepção pelo menu
No `DefaultLayout`, o item "Recepção de amostras" recebe um `@click` que chama `recepcaoStore.reiniciar()` sempre, esteja ou não na rota. A `RecepcaoAmostras.vue` observa `recepcao.passo` e, quando ele volta a 0, recarrega os pendentes e foca o campo, reaproveitando a lógica de `receberProxima`. O `reiniciar()` também limpa a mensagem de leitura e o `contextoNc` aberto (modal de não conformidade).
- Alternativa descartada: forçar a remontagem da view com `:key` na rota. O estado mora na store e continuaria lá.

### D6. Stepper só fora do passo 0
Em `RecepcaoAmostras.vue`, o `<Card>` do `Stepper` recebe `v-if="recepcao.passo > 0"`. O texto de orientação no topo continua.

### D7. Fila de tarefas em cards
O `DataTable` de `PassoLeitura.vue` é substituído por uma lista semântica (`<ul>`/`<li>`) dentro do mesmo `Card`:
- **cabeçalho:** "Para receber" com a contagem ("5 pendentes");
- **cada item:**
  - marcador de pendência (círculo vazio, decorativo);
  - `Badge` do tipo e nome do exame;
  - nº AGHU em `tabular-nums`;
  - material e origem;
  - tempo de espera com `tempoDecorrido()`. Acima de 2 h (`horasDesde() >= 2`), aparece em cor de alerta com ícone de relógio e o texto "atrasada" para leitores de tela;
  - botão primário "Iniciar recebimento" com seta, que chama a mesma `lerDaLista()`.
- **ordem:** CO primeiro, depois do mais antigo para o mais novo. A ordenação fica num `computed` da view, e o serviço fica intacto.
- **estado vazio:** ícone de check e "Nenhuma solicitação aguardando recebimento.", com a nota "Tudo em dia". Com o AGHU indisponível, continua a mensagem atual.
- **carregamento:** usa o `LoadingIndicator`/skeleton existente.
- **interação:** a linha inteira não é clicável, só o botão. Isso evita iniciar um recebimento sem querer. Os estados de hover, active e foco seguem o padrão `focus-ring`.
- **limite de 2 h:** é uma constante em `constants/ap.ts` (`HORAS_ALERTA_PENDENTE = 2`).
- **ajuste do seed:** hoje o seed gera pendentes em dias (`solicitadaHa`). Ele passa a ter pendentes de minutos e de poucas horas, para o destaque ficar visível. Um campo em horas ou minutos substitui ou complementa `solicitadaHa`.
- Alternativa descartada: manter a `DataTable` com "cara de fila". O usuário escolheu os cards.

### D8. Urgência automática para CO
Em `PassoComplemento.vue`, um `watch` no tipo de exame faz o seguinte:
- **ao entrar em CO:** define `urgente = 'SIM'`. Se o motivo estiver vazio, preenche com `MOTIVO_URGENCIA_CONGELACAO = 'Exame de congelação (intraoperatório)'` (constante em `constants/ap.ts`) e guarda que o texto é a sugestão;
- **ao sair de CO:** limpa `urgente`, sem valor padrão. O motivo só é limpo se ainda for exatamente a sugestão.

Para travar o campo, as opções do grupo "Urgente?" ficam com `disabled`, e o grupo mostra a nota "Automático para Congelação". O schema zod continua exigindo o motivo quando Sim. Isso também é aplicado no estado inicial: quando o tipo sugerido pelo AGHU já é CO, o `watch` roda com `immediate`.

### D9. Remoção de CMCE e "quem recebeu"
Remover `cmce` e `recebidoPorNome` de:
- `types/ap.ts` (`NaoConformidade`, `Devolucao` e o input de registro);
- o schema e os campos de `NaoConformidadeModal.vue`;
- a validação e a montagem do mock;
- o seed;
- a exibição em `DetalheCaso.vue` (aba Não conformidades);
- `RejeicoesDevolucoes.vue`. A coluna "Devolvido / recebido por" passa a "Devolvido por".

A descrição do evento no histórico deixa de citar "Recebido por". Busca no repositório por `cmce` e `recebidoPor` sem ocorrências no `frontend/src` serve de critério de aceite.

### D10. Situação da devolução por modal
`RejeicoesDevolucoes.vue`:
- a coluna "Situação" mostra um `Badge` com a cor de `SITUACOES_DEVOLUCAO`;
- uma nova coluna "Ações" (slot `#actions` da `DataTable`) tem um botão `outline` pequeno, com `PencilSquareIcon` e o rótulo acessível "Alterar situação da devolução de <data/caso>".

O novo componente `components/ap/AlterarSituacaoDevolucaoModal.vue` usa `Modal.vue`. Ele mostra, só leitura, natureza, caso ou solicitação, tipo e situação atual. O único campo editável é um grupo de rádio (ou select) com as situações. Os botões são "Cancelar" e "Salvar", e "Salvar" fica desabilitado enquanto a seleção for igual à atual. Ao salvar, chama `store.atualizarSituacao()`, que já audita e resolve a não conformidade. Depois mostra um toast e fecha.

### D11. Ações no cabeçalho do detalhe e fluxo sem rolagem
`DetalheCaso.vue`:
- **linha superior:** fica um único `flex flex-wrap items-center justify-between`. À esquerda vão número, copiar e selos. À direita vão as ações, na ordem Não conformidade → Cancelar caso → Imprimir (dropdown). A linha de metadados (tipo, paciente, material, entrada) desce para baixo dessa linha;
- **menu "Imprimir":** passa a abrir alinhado à direita (`right-0`), porque agora é o último botão;
- **fluxo do caso:** sai o `overflow-x-auto` do wrapper. Em `FluxoCaso.vue`, o contêiner das etapas usa `flex-wrap` com `gap-y`. Os conectores somem quando a etapa quebra de linha, ou se aceita conector no fim da linha. O `Stepper.vue` genérico já usa `flex-wrap` e não precisa mudar.

## Risks / Trade-offs

- **[Comportamento removido do topo]** Quem usava o leitor no campo do topo para abrir pendentes ou amostras perde esse atalho. → Mitigação: a recepção continua com leitura própria no passo 1, e o número interno impresso na etiqueta é encontrado pela busca.
- **[Spec de negócio divergente]** `docs/especificacao` ainda exige `recebido_por_nome`. → Mitigação: a divergência fica registrada na proposta. Na integração com a API, o backend não deve exigir o campo, ou a especificação deve ser revista com o usuário.
- **[Reinício sem confirmação]** Um clique no menu descarta a conferência preenchida. → Risco aceito pelo usuário (escolheu "voltar direto").
- **[Nova dependência]** `lucide-vue-next` acrescenta uma lib de ícones. → Impacto pequeno com tree-shaking. Registrar no `package.json` com versão fixa compatível.
- **[Conectores do fluxo ao quebrar linha]** Um traço solto no fim da linha pode parecer estranho. → Mitigação: validar visualmente em ~1024 px e em mobile com Playwright.

## Migration Plan

Não há migração de dados (frontend com mocks). Para o deploy, basta regenerar o build do frontend. O rollback é reverter o commit.
