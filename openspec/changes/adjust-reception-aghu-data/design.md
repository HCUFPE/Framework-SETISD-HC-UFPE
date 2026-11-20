## Context

Originalmente concebida apenas no frontend com serviços mock em memória (`services/ap/mock`, `mocks/ap/seed.ts`) e um modo híbrido (`VITE_AP_FONTE_SOLICITACOES=api`) lendo de `GET /api/solicitacoes`, a recepção passou a contar com persistência real no backend (`APP_DB` em SQLite com migrações Alembic) após a conciliação das branches. No contrato legado do CSV do AGHU, `GET /api/solicitacoes` devolve **uma linha por amostra** com id composto `<código>-<amostra>`, que antes era tratado como `SolicitacaoAghu` independente (resolvendo códigos puros com `MULTIPLAS_AMOSTRAS`).

Fatos do CSV que moldam a solução (ver `data/dicionario_dados.md`):
- dentro de uma solicitação, só variam `numero_amostra`, `descricao_material`, `cod_status_item`/`status_item_exame`, `sigla_exame`/`nome_exame` e `codigo_lab`;
- os dados do paciente, a origem, a unidade, a especialidade, a data e as informações clínicas são iguais em todas as linhas;
- 383 solicitações misturam siglas, e 316 misturam tipos de exame do SAP (CO+HP, HP+IHQ, CG+HP…);
- `data_solicitacao` não tem hora;
- `nome_paciente` vem anonimizado (iniciais) no CSV, mas no AGHU real é o nome completo.

## Goals / Non-Goals

**Goals:**
- Um modelo de "exame da solicitação" (unidade de recebimento) que represente fielmente as linhas do AGHU agrupadas.
- Catálogos do AGHU centralizados e usados por toda a interface, sem domínios paralelos.
- Formulário de não conformidade único, inline e reutilizável nos três pontos de registro.

**Non-Goals:**
- Leitura direta em tempo real do banco PostgreSQL de produção do AGHU (segue via CSV/seed no provedor local enquanto a integração direta não é habilitada).
- Filtrar a fila "Para receber" pelo status do AGHU (todos os itens do CSV seguem listados, como hoje).
- Atualizar `docs/especificacao/` (a divergência fica registrada na proposta).
- Normalizar grafias inconsistentes de unidades (`9º  SUL`, `7 º SUL`). Só se removem o U+200B e os espaços nas pontas.

## Decisions

### D1. `SolicitacaoAghu` passa a representar um exame da solicitação com suas amostras
A entidade vira o grupo `código da solicitação + sigla do exame`, com campos de nível de solicitação (paciente, origem, unidade, especialidade, data, informações clínicas) e `amostras: AmostraAghu[]` (`numeroAmostra`, `descricaoMaterial`, `codStatusItem`, `statusItemDescricao`). Os campos ficam assim:
- `id = "<código>:<SIGLA>"` é a chave de recebimento;
- `codigoSolicitacao` passa a ser **só o código do AGHU**, e `codigoSolicitacaoAghu` deixa de existir;
- `descricaoMaterial` e `statusAghuDescricao` saem do nível de cima, porque passam a ser por amostra.

O grupo é por **sigla**, não por tipo do SAP. "Múltiplos exames" no AGHU significa siglas diferentes. MBIOP e MPCIR na mesma solicitação são exames distintos no AGHU, embora ambos virem HP.

*Alternativa:* agrupar por tipo do SAP. Foi descartada porque juntaria exames que o AGHU trata como pedidos separados e esconderia a sigla na conferência.

### D2. O agrupamento é feito no frontend, e o backend limita por solicitação
`GET /api/solicitacoes` continua devolvendo uma linha por amostra, espelho da view do AGHU. O teste atual e o contrato não mudam. `solicitacaoApi.ts` agrupa as linhas por `codigoSolicitacao + siglaExame`. Para não cortar uma solicitação ao meio, o `limite` do backend passa a contar **solicitações distintas**, e não linhas. Essa é a única mudança de regra no backend, além de origem `CIRURGIA`.

*Alternativa:* um endpoint agrupado no backend. Fica para quando houver persistência real. Hoje ele duplicaria a lógica que o mock já precisa ter.

### D3. Catálogos do dicionário em `constants/ap.ts`
São escritos à mão a partir do dicionário, com um comentário que aponta para ele:
- `STATUS_ITEM_AGHU`: código → descrição e variante de badge. LI fica como success, CA como danger, AC/EC/PE como warning, e EX/AE/CO como info;
- `ORIGENS`: rótulos AGHU (`Ambulatório`, `Internação`, `Cirurgia`, `Paciente Externo`);
- `EXAMES_AGHU`: sigla → nome, tipo do SAP e código do laboratório;
- `UNIDADES_AGHU`: as 76 unidades, já limpas, que substituem `UNIDADES_ORIGEM`.

Um helper `limparTextoAghu()` remove o U+200B e os espaços nas pontas, e é aplicado na conversão do DTO. O tipo `OrigemAtendimento` troca `BLOCO_CIRURGICO` por `CIRURGIA`, e o mapa do backend acompanha.

### D4. Leitura e fila
`aghuService.lerSolicitacao(codigo)` passa a devolver:
- `PENDENTE` (um único exame pendente);
- `ESCOLHER_EXAME` (vários exames pendentes, com a lista);
- `RECEBIDA` (todos os exames já recebidos, com os casos ou IHQs);
- `DEVOLVIDA`;
- `NAO_ENCONTRADA`.

`MULTIPLAS_AMOSTRAS` deixa de existir. A leitura `<código>-<amostra>` resolve o exame que contém a amostra e então aplica as mesmas regras. A fila mostra um item por exame pendente. A espera vira dias inteiros (`diasDesde`) e `HORAS_ALERTA_PENDENTE` é trocada por `DIAS_ALERTA_PENDENTE = 1`. A escolha de exame aparece no passo 1 como cards no lugar da mensagem atual.

### D5. Conferência sem itens
`ItensConferencia` e `ITENS_CONFERENCIA` são removidos. `ConferenciaRecebimento` guarda `solicitacaoId`, `amostras: string[]` (números conferidos), o resultado, a observação, o usuário e a data e hora. As entradas `ConfirmarEntradaInput`/`VincularIhqInput` perdem `conferencia` e `quantidade`, e o serviço deriva a quantidade de `amostras.length`. A aba Recepção do detalhe passa a listar as amostras conferidas.

### D6. Amostras do caso a partir do AGHU
`confirmarEntrada` cria um `ItemMaterial` do tipo `AMOSTRA` por amostra do AGHU, com o novo campo `numeroAmostraAghu`, a descrição do material e o rótulo `Amostra <n>`. O código do item continua opaco e é o que vai no código de barras.

### D7. Não conformidade inline: `NaoConformidadeInline.vue`
O componente substitui `NaoConformidadeModal.vue`, que é removido. Ele recebe o `contexto` e usa vee-validate + zod:
- tipo é obrigatório;
- o texto é obrigatório só quando o tipo é `OUTROS`;
- observação é opcional;
- "Nova amostra?" é um radio Sim/Não obrigatório e começa sem valor;
- a unidade, escolhida em `UNIDADES_AGHU`, é exigida só no contexto `SEM_ETIQUETA`.

O componente emite `registrado` e `cancelar`. Quem o usa controla o `v-if`, e ele aparece logo abaixo do botão de origem, com foco no select ao abrir.

O catálogo `TipoNaoConformidadeCodigo` passa a ter 14 códigos, na ordem do formulário: `SEM_SOLICITACAO_OU_ETIQUETA`, `EXAME_NAO_CORRESPONDE_MATERIAL`, `FALTA_DESCRICAO_FRASCO`, `IDENTIFICACAO_ILEGIVEL`, `NUMERACAO_FRASCOS_DIVERGENTE`, `QUANTIDADE_FRASCOS_DIVERGENTE`, `LATERALIDADE_DIVERGENTE`, `FALTA_CARIMBO_ASSINATURA`, `ACONDICIONAMENTO_INADEQUADO`, `SOLICITACOES_DUPLICADAS`, `PECAS_NAO_DESCRITAS`, `SISCAN_INCORRETO`, `SEM_AGENDAMENTO_CMCE` e `OUTROS`. O catálogo também guarda a "solução" opcional, que só o tipo duplicadas tem.

`NaoConformidade` ganha `observacao?`. O campo `descricao` passa a guardar o texto de "Outros".

### D8. Devolução da solicitação inteira
No contexto `SOLICITACAO`, o mock marca como `DEVOLVIDA` todos os exames **pendentes** com o mesmo `codigoSolicitacao`, ligados a uma única não conformidade e a uma única devolução. Exames já recebidos não mudam.

### D9. Impressão com seleção
`PrintPreview` ganha, só para etiquetas e quando o caso tem 2 ou mais amostras, uma lista de checkboxes com número e descrição, todas marcadas por padrão, mais as ações "Todas" e "Nenhuma". Sem seleção, "Imprimir" fica desabilitado. A impressão e a reimpressão são locais no navegador, usando `window.print()`, sem chamada de API, histórico ou auditoria.

A etiqueta é reorganizada para caber o nome completo em 50 × 25 mm:
- linha 1: nº interno, "Am. <n>" e URG;
- código de barras com 5 mm;
- nome em negrito, até 2 linhas, com a fonte reduzida de 6,5 pt para 5,5 pt quando o nome passa de cerca de 40 caracteres;
- duas linhas compactas: Receb./Solic. e Pront./Exame.

O exame aparece pela sigla para economizar espaço.

### D10. Sugestão do caso de origem da IHQ
Quando outro exame da mesma solicitação já virou caso principal elegível, `PassoConferencia` pré-seleciona esse caso no campo de caso de origem, e o usuário pode trocá-lo.

### D11. Seed do mock
O seed é reescrito com valores apenas do dicionário e nomes completos fictícios. Ele cobre:
- um exame com 3 amostras;
- uma solicitação CONGE + APECR;
- uma solicitação APECR + IMUHI;
- um Paciente Externo sem prontuário nem especialidade;
- um CITO sem descrição;
- amostras com status diferentes no mesmo exame.

Casos e devoluções do seed migram para os novos códigos de NC e de origem.

### D12. Conferência e confirmação em um único passo
O formulário de entrada passa a ficar no painel "Conferência" (`PassoConferencia.vue`), e `PassoComplemento.vue` é removido. O tipo vem de `tipoExameSugerido` e é só exibido. Para IHQ, o painel mostra a busca do caso de origem, com a sugestão de D10. "Confirmar conferência" chama `confirmarEntrada`/`vincularIhq` e leva ao passo 2 ("Etiquetas e ficha"). O componente usa `:key` pelo id do exame, o que reinicia o formulário a cada leitura.

*Alternativa:* manter um passo só de revisão. Foi descartada porque não havia mais nada a decidir depois que o tipo e a quantidade passaram a vir do AGHU.

### D13. Opções de select estilizadas por CSS progressivo
O CSS usa `appearance: base-select` em `select.form-control` dentro de `@supports`, com `option:hover` e `option:focus-visible` no tom `paper-primary-soft`. Assim, todos os selects existentes ganham o destaque sem componente novo, e os navegadores sem suporte mantêm a lista nativa.

*Alternativa:* um componente de listbox próprio. Foi descartada por exigir reescrever todos os selects e a acessibilidade de teclado.

### D14. Conferência por solicitação, recebimento por tipo de exame (substitui D1, D4, D8 e D12)
O grupo passa a ser `código + tipo do SAP` (`id = "<código>:<TIPO>"`). Sigla e nome passam para cada amostra (`AmostraAghu.siglaExame/nomeExame`), e o grupo guarda as siglas distintas.

`lerSolicitacao` devolve `PENDENTE { codigoSolicitacao, exames }` com todos os grupos pendentes, e `ESCOLHER_EXAME` deixa de existir. O store guarda `exames` (os grupos em conferência) e `resultados[]`.

`confirmarConferencia` cria primeiro os casos principais (CO, HP, CG, CCV) e depois vincula as IHQs. Uma IHQ com "caso gerado nesta conferência" vai para o HP criado; se não houver HP, vai para o primeiro principal. Se uma entrada falhar depois de outras já confirmadas, a tela de resultado mostra as confirmadas e o erro aparece em toast.

Na não conformidade, o contexto vira `{ tipo: 'SOLICITACAO', solicitacaoIds }`, e só os grupos marcados são devolvidos (uma NC e uma devolução). A fila agrupa os grupos por solicitação no frontend, e o contador conta códigos distintos.

*Por que tipo e não sigla:* o setor emite um laudo por tipo de exame, então MBIOP + MPCIR na mesma solicitação formam um único caso HP.

### D15. `SelectBusca.vue` (substitui D13 nas telas de AP)
É um componente de combobox próprio: um botão com a aparência de `form-control` abre um popover com campo de busca e `listbox`. A busca ignora acentos e maiúsculas, e o componente funciona por teclado (setas, Enter, Esc, letra abre já filtrando) e fecha ao perder o foco.

Ele foi aplicado na não conformidade, na conferência, na Consulta de casos e em Devoluções. O CSS de D13 continua valendo para os `<select>` nativos que restam, nas telas do framework (Configurações, Exemplo, Novidades).

### D16. Urgência da solicitação, sem motivo
`urgente` é um só `ref` em `PassoConferencia`, copiado para o `ConfirmarEntradaInput` de cada tipo principal. Um `watch` sobre "há CO marcado" fixa Sim e libera a edição quando o CO é desmarcado. `motivoUrgencia` sai de `CasoAp`, de `ConfirmarEntradaInput`, da validação do mock, da ficha, do detalhe e do seed, junto com `MOTIVO_URGENCIA_CONGELACAO`. O evento "Marcado como URGENTE" passa a registrar "Urgência da solicitação AGHU.".

### D17. Modo `api` só com dados do CSV
`mocks/ap/db.ts` escolhe a carga inicial pela fonte. Em `mock`, carrega o seed. Em `api`, o banco começa vazio e `aplicarSolicitacoesExternas` preenche as solicitações. Quando a carga falha, `usarDadosDeDemonstracao()` troca o banco pelo seed, e uma carga bem-sucedida posterior volta a deixar só o CSV. O aviso de falha é exibido uma vez até a próxima carga bem-sucedida.

### D18. Não conformidade em modal
`NaoConformidadeInline.vue` vira `NaoConformidadeFormulario.vue`, só com o conteúdo do formulário, sem moldura nem botões. Ele expõe `salvando` e recebe `idFormulario`. `NaoConformidadeModal.vue` envolve o formulário no `Modal` do framework, com `close-on-backdrop=false`, título no cabeçalho e "Cancelar"/"Registrar devolução" no rodapé, ligados ao formulário pelo atributo `form`. O formulário é recriado a cada abertura (`v-if="show"`).

As regras obrigatórias (tipo e nova amostra) passam para o `superRefine`, para que todos os erros apareçam juntos.

O `SelectBusca` limita a altura da lista ao espaço visível do contêiner com rolagem (o corpo do modal) e abre para cima quando falta espaço embaixo.

## Risks / Trade-offs

- [Mudança grande de tipo em `SolicitacaoAghu` espalha erros de compilação] → fazer primeiro tipos e constantes e seguir o `vue-tsc` como lista de pendências.
- [Nome completo em 50 × 25 mm pode ficar ilegível em nomes muito longos] → reduzir a fonte em degraus e limitar a 2 linhas com quebra por palavra, sem reticências. Validar visualmente com um nome de 60 caracteres.
- [Amostra com status CANCELADO (CA) dentro de um exame pendente] → é exibida com o badge do status e entra no caso como as demais. Se o setor quiser excluí-la, isso vira um ajuste posterior.
- [O limite por solicitações distintas muda quantas linhas a API devolve] → o máximo continua 1000 solicitações. A rota já filtra por período.
- [A confirmação de vários tipos não é atômica no mock (as chamadas são sequenciais)] → quando há falha parcial, a tela mostra o que foi criado e avisa o erro. O backend real deve fazer isso em uma transação.
- [`appearance: base-select` só funciona no Chrome/Edge 135+] → nos outros navegadores fica a lista nativa (sem hover colorido), sem perda de função.
- [A divergência com `docs/especificacao/` (catálogo de NC e origem)] → fica registrada na proposta, e a atualização dos docs vem num change próprio.

## Migration Plan

A persistência local no backend (`APP_DB`) é versionada via migrações do Alembic (`alembic/versions/`), executadas automaticamente na inicialização (`alembic upgrade head`). As mudanças de contrato da recepção e das solicitações estão cobertas por `tests/test_solicitacoes.py` e `tests/test_reception_api.py`. Para reverter, basta reverter a branch e aplicar downgrade das revisões do Alembic se necessário.
