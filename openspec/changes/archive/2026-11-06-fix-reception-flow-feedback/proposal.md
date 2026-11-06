# Proposal

## Why

O usuário revisou o que foi entregue nos changes `evolve-base-components` e `add-reception-flow` e listou 14 ajustes de usabilidade e de escopo. Alguns são defeitos: o menu não volta à tela inicial da recepção, e o fluxo do caso mostra uma barra de rolagem. Outros simplificam o fluxo: o campo do topo só busca casos, saem campos que a recepção não usa e a lista de pendentes passa a ser uma fila de tarefas. Corrigir agora evita que esses padrões se espalhem para as próximas etapas.

## What Changes

- **Menu lateral**: a seção "Temporário" passa a se chamar "Outros" e recebe os itens Início (no começo) e Configurações (no fim). O recolhimento/expansão passa a ser feito por um botão próprio com o ícone `PanelRight` (Lucide). Clicar no nome do sistema deixa de recolher o menu. O nome do sistema passa a ser "Sistema de Gestão Integrada de Serviços de Anatomia Patológica" (sidebar, cabeçalho mobile, `/api/health` e título da aba).
- **Ícones**: adoção do pacote `lucide-vue-next`, restrita aos ícones pedidos. O Heroicons continua sendo o padrão.
- **BREAKING (comportamento)**: o campo global do topo deixa de ler códigos. Ele não abre mais solicitações pendentes do AGHU, códigos de amostra/IHQ nem avisa sobre solicitações devolvidas. Passa a buscar **exclusivamente casos cadastrados** por nº interno, prontuário ou nome do paciente, com lista de resultados. O ícone passa a ser só o de busca, e o F2 é mantido.
- **Recepção de amostras**:
  - o passo de leitura usa o ícone `Scan` (Lucide) no lugar do QR Code;
  - o indicador de passos sai da tela inicial (passo de leitura) e continua nos demais passos;
  - a tabela de solicitações pendentes vira uma **fila de tarefas em cards** ("Para receber"), com contador, tempo de espera e o botão "Iniciar recebimento" (antes "Ler etiqueta");
  - com o exame Congelação (CO), "Urgente?" fica em Sim e travado. O motivo continua obrigatório e vem preenchido com uma sugestão editável;
  - clicar em "Recepção de amostras" no menu sempre volta à tela inicial, descartando o recebimento em andamento.
- **Detalhe do caso**: as ações ficam na mesma linha do número e dos selos, na ordem "Não conformidade", "Cancelar caso" e "Imprimir". O indicador do fluxo do caso não exibe mais barra de rolagem.
- **Não conformidade / devolução**: saem os campos "Nº CMCE (opcional)" e "Quem recebeu na unidade de origem". Os dois somem dos formulários, das exibições, dos tipos e dos mocks.
- **Rejeições e devoluções**: a coluna "Situação" passa a ser só leitura (selo). Uma nova coluna de ação abre um modal que altera **apenas** a situação. A edição direta na tabela é retirada.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `app-navigation`: botão dedicado para recolher o menu, nome do sistema e retorno à tela inicial da recepção pelo menu.
- `code-scan`: o campo global passa a ser uma busca de casos cadastrados. A leitura de solicitações, itens, IHQs e devoluções sai.
- `sample-reception`: indicador de passos fora da tela inicial, fila de tarefas de pendentes com "Iniciar recebimento" e urgência automática para Congelação.
- `case-detail`: posição e ordem das ações no cabeçalho e indicador do fluxo sem rolagem.
- `nonconformity-return`: remoção do nº CMCE e de "quem recebeu na origem", e edição da situação por modal.

## Impact

- **Frontend**: `layouts/DefaultLayout.vue`, `components/ap/CodeScanField.vue`, `views/ap/RecepcaoAmostras.vue`, `components/ap/recepcao/PassoLeitura.vue` e `PassoComplemento.vue`, `views/ap/DetalheCaso.vue`, `components/ap/caso/FluxoCaso.vue`, `components/ap/NaoConformidadeModal.vue`, `views/ap/RejeicoesDevolucoes.vue` (com um novo modal de situação), `stores/casos.ts`, `stores/recepcao.ts`, `types/ap.ts`, `mocks/ap/seed.ts`, `services/ap/mock/*`, `config/version.ts` e `frontend/index.html`.
- **Backend**: só o `SYSTEM_TITLE` em `src/version.py`.
- **Dependências**: nova dependência `lucide-vue-next` no frontend.
- **Documentação**: `docs/especificacao/` **não** será alterada nesta entrega, por decisão do usuário. Fica uma divergência registrada: `02-requisitos.md` e `04-modelo-dados.md` ainda pedem `recebido_por_nome` obrigatório.
- **Sem impacto** em API, banco ou auditoria (a mudança de situação continua auditada).
