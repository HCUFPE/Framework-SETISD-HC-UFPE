## Why

O CSV extraído do AGHU (`data/privado/solicitacoes.csv`), descrito em `data/dicionario_dados.md`, mostra como os dados chegam de fato. Uma solicitação pode ter várias amostras, cada uma com número e descrição de material próprios. Também pode misturar exames diferentes: Congelação + peça cirúrgica, ou HP + IHQ (cerca de 1,5% das solicitações). Status, origem, exames e unidades vêm de domínios fechados. A recepção atual trata cada amostra como uma solicitação separada e usa domínios próprios que não batem com o AGHU, como origem "Bloco cirúrgico", status "Recebido"/"Solicitado" no mock e um catálogo de não conformidades diferente do formulário em papel do setor. Ela também pede dados que o AGHU não fornece (sexo, médico solicitante) e torna a conferência mais lenta com checkboxes e um modal de dois passos.

## What Changes

- **Dicionário do AGHU como fonte de verdade:** tipos, formatos e opções dos dados do AGHU seguem `data/dicionario_dados.md`. São eles: status do item (8 códigos: LI, AC, EX, AE, CA, CO, EC, PE), origem (Ambulatório, Internação, Cirurgia, Paciente Externo), exames (12 siglas), unidades (76), datas `dd/mm/aaaa` e prontuário e especialidade vazios para Paciente Externo. Todo campo de status ou com opções predefinidas passa a usar esses domínios.
- **BREAKING:** o código de origem `BLOCO_CIRURGICO` passa a `CIRURGIA`. Os rótulos de origem passam a ser os textos do AGHU.
- **BREAKING:** a unidade de recebimento passa a ser o **exame da solicitação** (código da solicitação + sigla do exame), com todas as amostras desse exame. Uma solicitação com vários exames tem um recebimento por exame. Os exames podem ser recebidos em momentos diferentes (recebimento parcial), e a solicitação fica pendente enquanto restar algum exame não recebido nem devolvido.
- A fila "Para receber" mostra um item por exame pendente, com a quantidade de amostras. A leitura do código da solicitação abre o exame pendente. Se houver mais de um, o usuário escolhe qual receber. A leitura de `código-amostra` abre o exame dessa amostra.
- O passo "Conferir" lista cada amostra do exame separadamente: número, descrição do material e status no AGHU.
- **BREAKING:** os quatro checkboxes de conferência são removidos. Os botões "Confirmar conferência" e "Registrar não conformidade" sobem para o lugar deles.
- **BREAKING:** a quantidade de peças/frascos deixa de ser digitada no passo "Completar e confirmar". O caso recebe uma amostra por amostra do AGHU, com o número e a descrição dela.
- **BREAKING:** o modal de não conformidade é removido nos três pontos de registro (sem etiqueta, conferência e detalhe do caso). O botão abre, logo abaixo, um formulário com:
  - um select com as 14 opções do formulário em papel do setor;
  - um campo de texto obrigatório quando a opção for "Outros";
  - "Observação" opcional;
  - "Nova amostra solicitada?" obrigatório, sem valor padrão;
  - a unidade de origem, apenas sem etiqueta, escolhida entre as unidades do AGHU.
  A não conformidade na conferência devolve todas as amostras ainda pendentes da solicitação.
- As etiquetas e a ficha de trabalho mostram o **nome completo** do paciente. A etiqueta passa a mostrar o número da amostra, e a ficha lista todas as amostras com as descrições delas.
- A impressão de etiquetas de um caso com mais de uma amostra permite imprimir todas ou só as amostras escolhidas pelo usuário. Isso vale na tela de resultado e no detalhe do caso.
- Sexo e médico solicitante deixam de ser exibidos, porque não existem no AGHU. A data da solicitação passa a ser exibida só como data. A espera na fila passa a ser medida em dias, e o atraso passa a valer a partir de 1 dia, porque o AGHU não fornece a hora.

### Ajustes de revisão (2026-11-17)

- **BREAKING:** o passo "Completar e confirmar" é removido e a recepção passa a ter 3 passos ("Ler etiqueta AGHU", "Conferir", "Etiquetas e ficha"). O tipo de exame vem do AGHU, sem edição. Urgente?, procedimento e observações vão para o painel de Conferência, e "Confirmar conferência" passa a confirmar a entrada.
- As amostras na conferência passam a ser exibidas em uma tabela (Amostra, Descrição do material, Status no AGHU), com a sigla do exame no título. Pelo CSV, o exame é por amostra, mas a conferência já agrupa as amostras pelo exame. Por isso, repeti-lo em cada linha seria redundante.
- O título da fila vira o selo "<N> amostra(s) para receber", e o selo de pendentes sai.
- As opções de não conformidade ficam sem ponto final, e a "Observação" deixa de ser redimensionável.
- A seleção de etiquetas perde o botão "Nenhuma".
- Com o menu lateral recolhido, um clique em qualquer parte dele o expande.
- Os campos de seleção ganham cursor de mão e destaque de cor nas opções ao passar o mouse, nos navegadores com select personalizável.

### Ajustes de revisão 2 (2026-11-17)

- **BREAKING:** a conferência passa a ser feita **por solicitação** do AGHU. As amostras pendentes ficam agrupadas por **tipo de exame do SAP** (HP, CG, CCV, CO, IHQ), não mais por sigla. Cada tipo é recebido, devolvido e cancelado como uma unidade, e gera um caso (e um laudo). Tipos diferentes podem ser recebidos em momentos diferentes: o usuário marca quais recebe agora.
- A tabela de amostras ganha a coluna "Exame" (tipo, sigla e nome por amostra). Uma confirmação pode gerar vários casos, e a IHQ pode ser vinculada ao caso principal criado na mesma conferência.
- A fila mostra um item por solicitação, com o título "<N> solicitações para receber". O contador do menu também passa a contar solicitações.
- A não conformidade na conferência permite escolher quais tipos de exame devolver.
- A busca do topo aceita o código da solicitação AGHU e oferece um atalho para a recepção quando a solicitação ainda está pendente.
- Os selects das telas de AP passam a ter busca por digitação (`SelectBusca`).
- A "Observação" da não conformidade passa a ter 3 linhas.
- O menu "Rejeições e devoluções" vira "Devoluções", e o menu lateral fica um pouco mais estreito.

### Ajustes de revisão 3 (2026-11-17)

- **BREAKING:** a urgência passa a ser da solicitação: há um único "Urgente?" na conferência, aplicado a todos os casos gerados, e ele fica travado em Sim quando há Congelação marcada. O campo e o dado "motivo da urgência" deixam de existir (formulário, caso, ficha e detalhe).

### Ajustes de revisão 4 (2026-11-17)

- O registro de não conformidade volta a ser um modal ("Não conformidade e devolução") nos três pontos, com os campos e o layout atuais (contexto no topo e ações no rodapé). O formulário passa a mostrar todos os erros de validação de uma vez.
- A fila "Para receber" passa a ser paginada (10 por página).

## Capabilities

### New Capabilities
- `aghu-data-dictionary`: domínios, formatos e regras de qualidade dos dados vindos do AGHU (status do item, origem, exames, unidades, datas, campos vazios) e a obrigação de usar esses domínios em todo campo de status ou de opções predefinidas.

### Modified Capabilities
- `sample-reception`: unidade de recebimento por exame da solicitação, recebimento parcial, fila e leitura agrupadas, amostras separadas na conferência, conferência sem checkboxes, fim da quantidade digitada, dados exibidos conforme o dicionário.
- `nonconformity-return`: registro inline no lugar do modal, novo catálogo de 14 tipos, "Outros" com texto, observação opcional, nova amostra sem padrão, unidade de origem do AGHU e devolução de todas as amostras pendentes da solicitação.
- `sample-labels`: nome completo na etiqueta e na ficha, número da amostra na etiqueta, lista de amostras na ficha e seleção de etiquetas a imprimir.
- `case-detail`: impressão de etiquetas com seleção das amostras e registro de não conformidade inline no detalhe.
- `app-navigation`: o menu lateral recolhido expande com um clique em qualquer parte dele.
- `ui-interaction-feedback`: campos de seleção com busca por digitação, cursor de mão e destaque de hover nas opções.
- `code-scan`: a busca do topo aceita o código da solicitação AGHU e tem atalho para solicitações pendentes.

## Impact

- **Frontend:**
  - `types/ap.ts` (solicitação com amostras e exames, novos códigos de NC, origem, status AGHU) e `constants/ap.ts` (catálogos do dicionário).
  - `stores/recepcao.ts` e os passos em `components/ap/recepcao/`.
  - `DadosSolicitacao.vue`, `EtiquetaFrasco.vue`, `FichaTrabalho.vue` e `PrintPreview.vue`.
  - Remoção de `NaoConformidadeModal.vue`, substituído por um componente inline.
  - `views/ap/DetalheCaso.vue` e `RejeicoesDevolucoes.vue` (filtro pelo novo catálogo).
  - Serviços mock e seed (`mocks/ap/seed.ts`), além de `services/ap/http/solicitacaoApi.ts` (agrupamento das linhas do AGHU).
- **Backend:** `src/controllers/solicitacao_controller.py` (origem `CIRURGIA`, código de status exposto) e `tests/test_solicitacoes.py`.
- **Dados:** o seed do mock passa a usar só valores existentes no dicionário. O formato de `GET /api/solicitacoes` (uma linha por amostra) continua o mesmo.
- **Documentação:** `docs/especificacao/` cita o antigo catálogo de NC e a origem "bloco cirúrgico". Essa divergência fica registrada e não é corrigida neste change.
