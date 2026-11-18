## 1. Backend: origem e limite por solicitação

- [x] 1.1 Em `src/controllers/solicitacao_controller.py`, mapear "Cirurgia" → `CIRURGIA`, aplicar `limite` a solicitações distintas (todas as amostras de cada solicitação incluídas) e limpar U+200B/espaços nas pontas de `unidade`. Atualizar a descrição do `limite` em `src/routers/solicitacao.py`. Verificar com testes novos em `tests/test_solicitacoes.py` (origem CIRURGIA, solicitação não cortada pelo limite, unidade limpa) passando em `uv run pytest tests/test_solicitacoes.py`.

## 2. Tipos e catálogos do dicionário

- [x] 2.1 Em `frontend/src/types/ap.ts`:
  - criar `AmostraAghu`;
  - remodelar `SolicitacaoAghu` como exame da solicitação (`id`, `codigoSolicitacao` só do AGHU, `amostras`), sem `descricaoMaterial`/`statusAghuDescricao` no topo, sem `sexo`/`nomeSolicitante` e sem `codigoSolicitacaoAghu`/`numeroAmostra`;
  - trocar `BLOCO_CIRURGICO` por `CIRURGIA` e definir os 14 códigos de NC;
  - remover `ItensConferencia`, ajustar `ConferenciaRecebimento`, as entradas de confirmação (sem `conferencia`/`quantidade`), `ContextoNaoConformidade` e `RegistrarNaoConformidadeInput` (`observacao`, `descricao` para "Outros");
  - incluir `numeroAmostraAghu` em `ItemMaterial` e `observacao` em `NaoConformidade`;
  - trocar `MULTIPLAS_AMOSTRAS` por `ESCOLHER_EXAME` em `LeituraSolicitacao`, e fazer `RECEBIDA` listar os casos.
  
  Verificar que o arquivo compila isoladamente. Os erros nos usos são resolvidos nos grupos seguintes.
- [x] 2.2 Em `frontend/src/constants/ap.ts`:
  - criar `STATUS_ITEM_AGHU` (8 códigos, com rótulo e variante), `EXAMES_AGHU` (12 siglas → nome, tipo, código do laboratório) e `UNIDADES_AGHU` (76 unidades limpas, substituindo `UNIDADES_ORIGEM`);
  - mudar `ORIGENS` para os rótulos do AGHU;
  - substituir `TIPOS_NAO_CONFORMIDADE` pelo catálogo de 14 itens, na ordem do formulário, com a solução de "solicitações duplicadas";
  - trocar `HORAS_ALERTA_PENDENTE` por `DIAS_ALERTA_PENDENTE = 1`;
  - remover `ITENS_CONFERENCIA` e `RESULTADOS`, se não forem mais usados;
  - criar o helper `rotuloStatusItemAghu()` com o fallback "status não catalogado".
  
  Verificar conferindo cada lista contra `data/dicionario_dados.md`.
- [x] 2.3 Em `frontend/src/helpers/`, adicionar `limparTextoAghu()` e `diasDesde()` e o rótulo de espera ("hoje", "há 1 dia", "há N dias"). Verificar os casos de borda (meia-noite, data futura) com chamadas de exemplo no console do dev server.

## 3. Serviços, agrupamento e seed

- [x] 3.1 Em `services/ap/http/solicitacaoApi.ts`, agrupar as linhas do DTO por `codigoSolicitacao + siglaExame` em `SolicitacaoAghu` com `amostras` ordenadas, aplicando `limparTextoAghu` e mantendo datas só com dia. Verificar com `VITE_AP_FONTE_SOLICITACOES=api`: uma solicitação com 3 amostras do CSV aparece como um único item da fila com "3 amostras".
- [x] 3.2 Reescrever `mocks/ap/seed.ts` só com valores do dicionário e nomes completos fictícios. Cobrir:
  - um exame com 3 amostras;
  - CONGE + APECR na mesma solicitação;
  - APECR + IMUHI na mesma solicitação;
  - um Paciente Externo sem prontuário nem especialidade;
  - um CITO sem descrição;
  - status diferentes no mesmo exame.
  
  Migrar casos e devoluções do seed para os novos códigos. Verificar com `npx vue-tsc --noEmit` sem erros no seed e conferindo na tela que nenhum valor foge do dicionário.
- [x] 3.3 Ajustar `aghuServiceMock`:
  - `listarPendentes`/`contarPendentes` passam a contar por exame;
  - `lerSolicitacao` resolve código puro e `código-amostra`, com os resultados `PENDENTE`, `ESCOLHER_EXAME`, `RECEBIDA` (com casos), `DEVOLVIDA` e `NAO_ENCONTRADA`.
  
  Verificar pelo `window.apMock` no console: lendo o código da solicitação CONGE+APECR, o resultado é `ESCOLHER_EXAME` com 2 exames.
- [x] 3.4 Ajustar `casoServiceMock`:
  - `confirmarEntrada`/`vincularIhq` sem itens de conferência;
  - quantidade derivada das amostras;
  - uma `AMOSTRA` por amostra do AGHU (`numeroAmostraAghu`, descrição, rótulo `Amostra <n>`);
  - conferência registrada com as amostras;
  - apenas o exame marcado como recebido;
  - impressão e reimpressão locais com `window.print()`, sem endpoint, histórico ou auditoria.
  
  Verificar que, recebendo o CONGE da solicitação mista, o APECR continua pendente.
- [x] 3.5 Em `naoConformidadeServiceMock.registrar`, gravar `observacao` e o texto de "Outros". No contexto `SOLICITACAO`, devolver todos os exames pendentes do mesmo código, com uma NC e uma devolução, sem afetar exames já recebidos. Verificar os dois cenários do spec "Devolução de todas as amostras pendentes" na tela.

## 4. Passos da recepção

- [x] 4.1 Em `stores/recepcao.ts`, remover a conferência por itens e `conferenciaCompleta`. Tratar `ESCOLHER_EXAME` (lista de exames para escolha) e `RECEBIDA` com vários casos. Fazer `confirmarConferencia` avançar direto. Verificar que `npx vue-tsc --noEmit` não aponta erros no store.
- [x] 4.2 Em `PassoLeitura.vue`:
  - fila por exame, com "N amostras", data só com dia, espera em dias e destaque a partir de 1 dia;
  - cards de escolha de exame quando a leitura retornar `ESCOLHER_EXAME`;
  - mensagem de "já recebida" com links para cada caso;
  - `NaoConformidadeInline` abaixo do botão de material sem etiqueta.
  
  Verificar os cenários de fila e leitura do spec `sample-reception` na tela.
- [x] 4.3 Em `DadosSolicitacao.vue`, remover sexo e médico solicitante e exibir nome completo, data só com dia, exame com sigla e a lista de amostras separadas (número, descrição ou "Não informado", badge do status AGHU), com o total. Verificar no passo "Conferir" e na aba Solicitação AGHU do detalhe.
- [x] 4.4 Em `PassoConferencia.vue`, remover os checkboxes e o alerta de conferência incompleta, colocar "Confirmar conferência" e "Registrar não conformidade" no topo do painel e renderizar `NaoConformidadeInline` logo abaixo deste último. Verificar que confirmar avança direto e que a NC abre inline sem modal.
- [x] 4.5 Em `PassoConferencia.vue`, exibir a quantidade de amostras somente leitura e pré-selecionar o caso de origem da IHQ quando outro exame da mesma solicitação já virou caso elegível. Verificar o cenário "Sugestão do caso da mesma solicitação" e a confirmação com Ctrl+Enter.
- [x] 4.6 Em `PassoResultado.vue`, exibir o aviso de outros exames pendentes da mesma solicitação. Verificar recebendo o CONGE da solicitação mista.

## 5. Não conformidade inline

- [x] 5.1 Criar `components/ap/NaoConformidadeInline.vue` (vee-validate + zod):
  - select com os 14 tipos;
  - texto obrigatório só para "Outros" e observação opcional;
  - "Nova amostra solicitada?" obrigatório, sem valor inicial;
  - unidade de `UNIDADES_AGHU` só para `SEM_ETIQUETA`, com o tipo pré-selecionado nesse contexto;
  - solução exibida para "solicitações duplicadas";
  - ações "Registrar devolução" e "Cancelar", com foco no select ao abrir.
  
  Verificar os cenários de validação do spec `nonconformity-return`.
- [x] 5.2 Remover `NaoConformidadeModal.vue` e o uso dele em `RecepcaoAmostras.vue` e `DetalheCaso.vue`. No detalhe, abrir o formulário inline abaixo da linha de ações e esconder após registrar. Verificar com `grep -r NaoConformidadeModal frontend/src` vazio e com o registro funcionando nos três pontos.
- [x] 5.3 Em `RejeicoesDevolucoes.vue` e na aba Não conformidades do detalhe, exibir o tipo do novo catálogo, "Outros: <texto>" e a observação. O filtro de tipo deve listar os 14 tipos na ordem do formulário. Verificar os cenários "Tipo Outros" e "Filtro por tipo".

## 6. Etiquetas, ficha e impressão

- [x] 6.1 Reorganizar `EtiquetaFrasco.vue` conforme o design D9: nº interno, "Am. <n>", URG, código de barras, nome completo em até 2 linhas com redução de fonte, e as linhas Receb./Solic. e Pront./Exame (sigla). Verificar na pré-visualização com um nome de 60 caracteres: nome inteiro, sem reticências, dentro de 50 × 25 mm.
- [x] 6.2 Em `FichaTrabalho.vue`, colocar o nome completo no bloco Paciente e origem, tirar o médico solicitante do bloco Solicitante, exibir o exame com sigla e listar as amostras (número e descrição) no bloco Material. Verificar a ficha de um caso com 3 amostras.
- [x] 6.3 Em `PrintPreview.vue`, criar a seleção de amostras para etiquetas quando houver 2 ou mais amostras (todas marcadas, "Todas", "Nenhuma", "Imprimir" desabilitado sem seleção) e pré-visualizar só as marcadas. Imprimir localmente pelo navegador, sem chamada de API, histórico ou auditoria. Verificar os cenários do spec `sample-labels` na tela de resultado e no detalhe do caso.
- [x] 6.4 Na aba Recepção de `DetalheCaso.vue`, trocar a lista de itens de conferência pelas amostras conferidas. Verificar o cenário "Conferência na aba Recepção".

## 7. Verificação integrada

- [x] 7.1 Rodar `npx vue-tsc --noEmit` (em `frontend/`) sem erros e `uv run pytest` com todos os testes passando.
- [x] 7.2 Rodar `python audit_framework.py .` e confirmar 100% de conformidade.
- [x] 7.3 Percorrer o fluxo completo no navegador (modo mock e modo api):
  - receber o CONGE e depois o APECR de uma solicitação mista;
  - receber um exame com 3 amostras e imprimir só a etiqueta da amostra 2;
  - registrar NC "Outros" na conferência e conferir em "Rejeições e devoluções";
  - registrar NC sem etiqueta com uma unidade do AGHU;
  - registrar NC no detalhe de um caso.

## 8. Ajustes de revisão

- [x] 8.1 Remover o passo "Completar e confirmar". Levar Urgente?, procedimento, observações e caso de origem da IHQ para o painel de `PassoConferencia.vue`, com o tipo vindo do AGHU sem edição. Fazer "Confirmar conferência" confirmar a entrada e reduzir o stepper a 3 passos. Verificado no navegador com HP de 3 amostras (resumo de erros e confirmação), CO (urgência travada) e IHQ (sugestão do caso de origem).
- [x] 8.2 Mostrar as amostras em tabela (Amostra, Descrição do material, Status no AGHU), com a sigla do exame no título. Verificado na conferência do exame MBIOP.
- [x] 8.3 Trocar o título da fila pelo selo "<N> amostra(s) para receber" e remover o selo de pendentes. Verificado: "13 amostras para receber".
- [x] 8.4 Tirar o ponto final das opções de não conformidade, deixar a "Observação" sem redimensionamento e remover "Nenhuma" da seleção de etiquetas. Verificado: 0 de 14 opções com ponto final, `resize: none` e nenhum botão "Nenhuma".
- [x] 8.5 Expandir o menu lateral recolhido com um clique em qualquer parte dele. Verificado: a largura passa de 80 px para 256 px.
- [x] 8.6 Adicionar cursor de mão e hover nas opções de select (`index.css`). Verificado no Chromium: cursor `pointer` e fundo `rgb(230, 238, 238)` ao passar o mouse.
- [x] 8.7 Rodar `npx vue-tsc --noEmit`, `uv run pytest` e `python audit_framework.py .`.

## 9. Ajustes de revisão 2

- [x] 9.1 Reagrupar por solicitação + tipo de exame (tipos, helpers, agrupamento da API, seed com HP + IHQ na mesma solicitação). Ler por solicitação, contar pendentes por solicitação e devolver só os tipos escolhidos. Verificado no navegador: a solicitação 7712340 aparece como um item com CO e HP.
- [x] 9.2 Conferência por solicitação: tabela com a coluna Exame, um bloco por tipo com "receber agora", IHQ ligada ao caso da própria conferência e resultado com vários registros. Verificado: HP-0012/26 + IH-0004/26 vinculada a ele, e CO recebido com HP devolvido em separado.
- [x] 9.3 Fila e menu por solicitação ("9 solicitações para receber", contador 9). Verificado.
- [x] 9.4 Busca do topo pelo código da solicitação AGHU, com atalho para solicitação pendente. Verificado com 7711390 (caso) e 7712301 (abre a conferência).
- [x] 9.5 Criar `SelectBusca.vue` e aplicá-lo na não conformidade, na conferência, na Consulta de casos e em Devoluções. Verificado: "agulha" filtra 2 procedimentos, e "outros" filtra o tipo em Devoluções.
- [x] 9.6 "Observação" com 3 linhas, menu "Devoluções" e menu lateral com 224 px. Verificado.
- [x] 9.7 Rodar `npx vue-tsc --noEmit`, `npx vite build`, `uv run pytest` e `python audit_framework.py .`.

## 10. Urgência por solicitação

- [x] 10.1 Trocar o "Urgente?" por tipo por um único da solicitação, travado em Sim quando há CO marcado e escondido quando só há IHQ. Verificado: CO+HP gera CO e HP urgentes, desmarcar CO libera o campo e só IHQ não mostra o campo.
- [x] 10.2 Remover o motivo da urgência (formulário, modelo, mock, ficha, detalhe, seed e constante). Verificado com `grep motivoUrgencia` vazio e `vue-tsc`/`vite build` sem erros.

## 11. Integração com o CSV

- [x] 11.1 No modo `api`, começar com o banco do mock vazio: só as solicitações do CSV, e os casos, devoluções e NCs criados na sessão (sem o seed). Se o backend falhar, usar o seed como demonstração. Separar `fonteSolicitacoes` em `services/ap/http/fonte.ts` para evitar ciclo de imports. Verificado: Consulta e Devoluções começam vazias, a fila tem 200 solicitações do CSV e o primeiro caso é HP-0001/26.
- [x] 11.2 Mostrar só um aviso "Exibindo dados de demonstração" quando o backend falha, mesmo com cargas simultâneas (login + F5). Verificado: 1 aviso após o login e 1 após o F5.
- [x] 11.3 Paginar a fila "Para receber" (10 por página, no padrão da tabela da Consulta). Verificado com 200 solicitações do CSV: 20 páginas, botões desabilitados nas pontas e recebimento a partir da última página.

## 12. Não conformidade em modal

- [x] 12.1 Voltar o registro de não conformidade para um modal com o layout atual (`NaoConformidadeModal` + `NaoConformidadeFormulario`) nos três pontos. Verificado: abre, Cancelar e Esc fecham sem registrar, o formulário reabre vazio e o registro fecha o modal (conferência volta ao passo 1, detalhe fica Devolvido).
- [x] 12.2 Mostrar todos os erros de validação de uma vez. Verificado no registro sem etiqueta: unidade e nova amostra indicadas juntas.
- [x] 12.3 Fazer a lista do `SelectBusca` caber no espaço visível dentro de modais. Verificado: a lista de unidades fica inteira acima do rodapé do modal.

## Workflow follow-up

- Não commitar sem pedido explícito do usuário. Ao concluir, avisar que as mudanças estão prontas para commit na branch `feat/ajustes-recepcao-aghu`.
- Arquivar o change (`/opsx:archive`) após a revisão do usuário.
- Avaliar um change próprio para alinhar `docs/especificacao/` ao novo catálogo de NC e à origem "Cirurgia".
