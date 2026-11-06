# Proposal

## Why

A recepção do Serviço de Anatomia Patológica hoje recebe e confere as amostras no AGHU e copia os dados à mão para planilhas, livro de protocolo e fichas em papel (`docs/especificacao/00-validacao-negocio.md`, seção 3). Este é o primeiro fluxo do sistema a ser construído: recepção de amostras, consulta de casos e rejeições e devoluções. Ele é entregue só no frontend, com dados mockados, para validar a interação com os usuários antes da integração com o backend e o AGHU.

## What Changes

- **Navegação:**
  - O menu lateral passa a ter duas seções. "Recepção" reúne Início, Recepção de amostras, Consulta de casos, Rejeições e devoluções e Configurações. "Temporário" reúne Componentes, Novidades dos Componentes e Exemplo.
  - O cabeçalho ganha um campo global de leitura de código, acessível pela tecla F2.
- **Recepção de amostras (`/recepcao`)** em 4 passos:
  1. ler a etiqueta do AGHU;
  2. conferir a amostra (conferência registrada);
  3. completar e confirmar a entrada;
  4. ver o resultado.

  Na confirmação, o sistema gera o número interno por tipo e ano para os casos principais HP, CG, CCV e CO. A IHQ é sempre vinculada a um caso já existente e nunca vira um caso próprio.
- **Não conformidade e devolução:**
  - registro em 2 passos, a partir da recepção (com ou sem etiqueta do AGHU) e do detalhe do caso;
  - toda não conformidade gera devolução (RF020/RF021).
- **Consulta de casos (`/casos`):** busca, filtros, etiquetas de filtro, tabela paginada com os urgentes destacados e acesso ao detalhe. Sem exportação de dados.
- **Detalhe do caso (`/casos/:numero`):**
  - cabeçalho, indicador das etapas do fluxo e faixa de bloqueio;
  - abas de resumo, solicitação AGHU, recepção, macroscopia, processamento, IHQ, microscopia, laudo, arquivo, materiais, não conformidades e histórico. As abas das etapas posteriores à recepção mostram dados mockados, só para leitura;
  - ações: registrar não conformidade, imprimir e cancelar o caso (motivo obrigatório).
- **Rejeições e devoluções (`/rejeicoes-devolucoes`):** lista que distingue a rejeição na recepção (sem caso aberto) da devolução de caso, com filtros e acompanhamento da situação da devolução.
- **Impressão:**
  - etiqueta do frasco (50×25 mm) com o código de barras do número interno;
  - ficha de trabalho (A4) com os dados de identificação, solicitação, origem, solicitante e material organizados em blocos, mais o quadro de acompanhamento físico por setor.
- **Dados mockados:** uma camada de serviços tipada, substituível pela API futuramente. Nomes, prontuários, números do AGHU, médicos e funcionários são todos fictícios e criados para este change.

## Capabilities

### New Capabilities
- `app-navigation`: organização do menu lateral em seções e acesso às telas do fluxo de recepção.
- `sample-reception`: leitura da solicitação do AGHU, conferência, complementação e confirmação da entrada da amostra, incluindo o vínculo da IHQ a um caso existente.
- `nonconformity-return`: registro de não conformidade com devolução e acompanhamento das rejeições e devoluções.
- `case-search`: consulta e filtragem dos casos de anatomia patológica.
- `case-detail`: visualização consolidada do caso, com histórico, materiais, não conformidades e cancelamento.
- `sample-labels`: impressão da etiqueta do frasco e da ficha de trabalho do caso.
- `code-scan`: leitura ou digitação de código em qualquer tela, levando à recepção ou ao caso correspondente.

### Modified Capabilities
<!-- Nenhuma: ui-component-library e ui-interaction-feedback são usadas sem mudança de requisito. -->

## Impact

- **Frontend:**
  - novas views em `frontend/src/views/`;
  - tipos de domínio, serviços mockados e stores Pinia novos;
  - rotas novas em `frontend/src/router/index.ts`;
  - menu e cabeçalho em `frontend/src/layouts/DefaultLayout.vue`;
  - estilos de impressão em `frontend/src/index.css`.
- **Componentes:** reaproveita `Button`, `Card`, `DataTable`, `Modal`, `Badge`, `Stepper`, `Tabs`, `Alert` e `FilterChips`, sem alterar o comportamento especificado deles.
- **Dependências:** nenhuma nova. O código de barras é gerado em SVG pelo próprio projeto.
- **Backend, AGHU e banco:** sem impacto. Toda a persistência é simulada em memória.
- **Fora do escopo:**
  - perfis e RBAC (o usuário `admin` atua como recepcionista);
  - telas de outros setores, solicitação complementar e indicadores;
  - exportação de dados, escrita no AGHU e acionamento real da equipe de plantão.
