
Sistema de acompanhamento de exames da Anatomia Patológica do HC-UFPE. Ele lê dados do AGHU mas não grava nele, e substitui a planilha do Teams, o livro de protocolo e as pranchetas. Usa a etiquetadora e o leitor de código de barras do setor.

## 1. Requisitos Funcionais (RF)

| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :---: |
| RF001 | Autenticação | Login via LDAP/AD do hospital. | Essencial |
| RF002 | Perfis de acesso | Perfis por função (recepção, macroscopista, técnico, residente, patologista, citotécnico). Cada perfil vê as filas e ações do seu setor. | Essencial |
| RF003 | Recebimento de amostra | Ao bipar ou digitar o código da etiqueta, mostrar numa só tela o paciente e cada amostra com sua descrição, permitindo receber só os itens das 5 bancadas (HP, CO, IHQ, CG, CCV). | Essencial |
| RF004 | Conferência da amostra | Checklist obrigatório por amostra: sigla × conteúdo do frasco, descrição × frasco e nº de recipientes. | Essencial |
| RF005 | Não conformidade e devolução | Registrar a não conformidade com motivo padronizado e a devolução ao setor de origem. | Essencial |
| RF006 | Número interno | Gerar o nº interno no formato sigla do tipo (HP, CG, CCV, CO, IH) + sequencial curto, reiniciado a cada ano, para ser escrito no cassete e usado na ordem do arquivo. | Essencial |
| RF007 | Dados complementares | Registrar urgência, clínica responsável, classificação de faturamento (geral, mama, colo) e nº de peças. | Essencial |
| RF008 | Etiquetas internas | Imprimir na etiquetadora etiquetas com nº interno, paciente e código de barras para frascos e lâminas. | Importante |
| RF009 | Ficha de trabalho | Imprimir a ficha de trabalho com nº interno e descrição de cada amostra quando o material chegar sem ficha. | Importante |
| RF010 | Exame externo | Registrar a pré-entrada do externo, gerar a ficha estruturada para o cadastro pela Regulação e vincular a solicitação quando ela for criada. | Essencial |
| RF011 | Etapa inicial do externo | Indicar a etapa inicial do externo e marcar as etapas já realizadas fora. | Importante |
| RF012 | Gravação assistida no AGHU | Gerar pendências com o conteúdo pronto para copiar no AGHU (recebimento, laudos, pedido de IHQ, PDF externo), sempre com o nº interno incluído no texto, com baixa quando a gravação for confirmada. | Essencial |
| RF013 | Encaminhamento entre setores | Registrar o envio e o recebimento entre setores com data, hora e usuário, substituindo o livro de protocolo. | Essencial |
| RF014 | Filas de trabalho | Fila de cada setor com urgências no topo e, entre elas, ordem de chegada, substituindo as pranchetas. | Essencial |
| RF015 | Fluxo de congelação | Registrar a escala de plantão de congelação e alertar o residente escalado (ou permitir escolher o responsável na hora); registrar laudo CO, resposta ao Bloco Cirúrgico e novas margens; vincular a solicitação HP, que entra no Processamento após o Corte. | Essencial |
| RF016 | Registro da macroscopia | Registrar cassetes (letras e nº de fragmentos), tipo de processamento (histotécnico ou manual), coloração especial e sobra com local de guarda. | Essencial |
| RF017 | Modelos de macroscopia | Modelos de texto por tipo de material, com campos para medidas, peso e características, que geram a descrição macroscópica. | Importante |
| RF018 | Registro do processamento | Registrar as etapas do histo (histotécnico ou manual, inclusão, corte, coloração, montagem) e do cito (centrifugação, cell-block, coloração, montagem), com data e técnico. | Essencial |
| RF019 | Distribuição de lâminas | Registrar as lâminas geradas e distribuí-las ao residente, ao patologista ou ao citotécnico (CCV). | Essencial |
| RF020 | Microscopia e laudo | Acompanhar pré-laudo, discussão e aprovação; registrar amostra insuficiente ou laudo provisório; encerrar o exame quando o laudo for liberado. | Essencial |
| RF021 | Solicitação de complementos | Pedir revisão de peça (só HP), recorte, coloração especial ou envio à rede externa, com tipo, data e solicitante, deixando o exame como "aguardando complemento". | Essencial |
| RF022 | Exame de IHQ vinculado | Criar o IHQ sempre vinculado a um HP ou cito, com nº IH e anticorpos; novas rodadas mantêm o mesmo nº IH. | Essencial |
| RF023 | Retorno por erro | Devolver o exame da Macroscopia ou da Microscopia à Recepção com motivo; após a correção, ele volta à etapa que o devolveu, sem reiniciar o fluxo. | Essencial |
| RF024 | Consulta de status | Buscar exame por nº interno, solicitação, nome ou prontuário, vendo etapa atual, datas e responsáveis. | Essencial |
| RF025 | Painel de urgências | Lista das urgências ainda não liberadas, visível para todos os setores. | Importante |
| RF026 | Localização do material | Registrar onde estão lâminas, blocos, fichas e sobras (arquivo de aço, pastas, armário). | Importante |
| RF027 | Indicadores e prazos | Tempo por etapa, laudos no prazo e alertas para exames perto dos limites (20 dias internos, 60 dias do Ministério da Saúde). | Desejável |
| RF028 | Responsável e edição concorrente | Ao abrir um exame para registrar uma etapa, o profissional passa a ser o responsável por ela. Quem abrir o mesmo exame vê o aviso "em edição por [nome] desde [hora]" e fica só com leitura até a edição ser concluída, cancelada ou transferida. | Importante |

### 📌 Legenda de Níveis de Prioridade:
- **Essencial (Alta):** Funcionalidade indispensável para o funcionamento básico da aplicação. Sem ela, o sistema não pode ir para produção (ex: autenticação, cadastros base).
- **Importante (Média):** Funcionalidade que agrega valor significativo ao negócio e melhora o fluxo de trabalho, mas cuja ausência temporária não impede a operação mínima (ex: relatórios, filtros avançados).
- **Desejável (Baixa):** Funcionalidade complementar, melhoria estética ou recurso secundário que pode ser implementado em sprints futuras (ex: temas visuais, atalhos de teclado).

## 2. Requisitos Não Funcionais (RNF)

| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF001 | Restrição de ambiente | O sistema funciona sem nenhuma alteração no AGHU, pois mudanças nele só podem ser solicitadas à sede da EBSERH em Brasília [56:49]. |
| RNF002 | Interoperabilidade | Reconhece o código da etiqueta AGHU no formato atual, incluindo o sufixo de cada amostra (001, 002, 003) [69:04, 72:31]. |
| RNF003 | Interoperabilidade | Usa os mesmos nomes de status do AGHU (ex.: "liberado", "a coletar"), sem criar uma nomenclatura paralela [66:54]. |
| RNF004 | Implantação | Roda na infraestrutura do próprio HC, como o sistema de leitos de UTI hoje em uso oficial [59:32]. |
| RNF005 | Segurança | Dados de pacientes acessíveis apenas a usuários do hospital com perfil autorizado, por se tratar de dados de saúde. |
| RNF006 | Rastreabilidade física | O mesmo identificador legível aparece em todos os materiais do exame: frasco, cassete, bloco, lâmina e ficha [34:48]. |
| RNF007 | Responsabilização | Toda etapa registrada exibe o nome de quem a executou, para saber a quem procurar em caso de problema [21:08]. |
| RNF008 | Usabilidade | A interface usa as siglas e os termos do setor (HP, CG, CCV, CO, IH, bancada, macro) [22:16]. |
| RNF009 | Usabilidade | Telas simples para usuários com pouca afinidade com sistemas, com campos obrigatórios em vez de opcionais [89:55]. |
| RNF010 | Usabilidade | Exames urgentes têm destaque visual em todas as telas em que aparecem [47:26]. |
| RNF011 | Coexistência | O sistema funciona em conjunto com a ficha física, que continua acompanhando o material [55:13]. |
| RNF012 | Extensibilidade | Novos anticorpos, colorações e tipos de material podem ser incluídos sem alterar o código (hoje são cerca de 100 anticorpos) [111:22]. |
| RNF013 | Confiabilidade | Nenhum registro é perdido ou fica incompleto se a conexão cair no meio de uma operação. |

## 3. Detalhamento SDD (CARE)
Para cada requisito, a implementação deve seguir o padrão:

### [CARE-RF001] Autenticação
* **Context (Contexto)**: LDAP/AD do hospital acessível com credencial de serviço.
* **Action (Ação)**: Criar middleware de autenticação que valide usuário e senha no AD.
* **Result (Resultado)**: JWT gerado em caso de sucesso; código 401 em falha.
* **Evaluation (Avaliação)**: Testes de login válido, senha inválida e AD indisponível.

### [CARE-RF002] Perfis de acesso
* **Context (Contexto)**: RF001 implementado; perfis cadastrados.
* **Action (Ação)**: Associar perfis aos usuários e restringir telas e ações.
* **Result (Resultado)**: Ação fora do perfil retorna 403.
* **Evaluation (Avaliação)**: Cada perfil acessa as rotas permitidas e é barrado nas demais.

### [CARE-RF003] Recebimento de amostra
* **Context (Contexto)**: Dados da solicitação disponíveis pela leitura do AGHU (RNF001).
* **Action (Ação)**: Criar a tela de recebimento com a lista de amostras e suas descrições.
* **Result (Resultado)**: Exame criado com as amostras recebidas, data, hora e usuário.
* **Evaluation (Avaliação)**: Uma solicitação com itens HP e sorologia mostra só os HP; recebendo 2 de 3 amostras, o exame fica com 2.

### [CARE-RF004] Conferência da amostra
* **Context (Contexto)**: Tela de recebimento disponível.
* **Action (Ação)**: Incluir o checklist obrigatório por amostra.
* **Result (Resultado)**: O recebimento só é concluído com o checklist completo.
* **Evaluation (Avaliação)**: Recebimento bloqueado com item pendente e liberado com checklist completo.

### [CARE-RF005] Não conformidade e devolução
* **Context (Contexto)**: Motivos cadastrados (etiqueta ausente, sigla incompatível, descrição divergente, nº de recipientes diferente, peça ausente).
* **Action (Ação)**: Registrar a não conformidade com motivo e observação.
* **Result (Resultado)**: Exame marcado como devolvido, sem consumir nº interno.
* **Evaluation (Avaliação)**: Após uma devolução, o status, o motivo e a sequência de números ficam corretos.

### [CARE-RF006] Número interno
* **Context (Contexto)**: Tabela de sequências por tipo e ano criada.
* **Action (Ação)**: Gerar o próximo número na conclusão do recebimento, dentro de uma transação.
* **Result (Resultado)**: Número no formato sigla + sequencial (ex.: HP 4757).
* **Evaluation (Avaliação)**: 50 recebimentos simultâneos sem números repetidos; teste da virada de ano.

### [CARE-RF007] Dados complementares
* **Context (Contexto)**: Exame recebido.
* **Action (Ação)**: Incluir os campos de urgência, clínica, faturamento e nº de peças.
* **Result (Resultado)**: Dados usados nas filas e na consulta; CO já entra como urgente.
* **Evaluation (Avaliação)**: Um exame CO é criado urgente; edições ficam registradas.

### [CARE-RF008] Etiquetas internas
* **Context (Contexto)**: Layout de etiqueta validado com a equipe.
* **Action (Ação)**: Gerar e enviar a etiqueta para a etiquetadora.
* **Result (Resultado)**: Etiqueta impressa com código legível pelo leitor do setor.
* **Evaluation (Avaliação)**: A etiqueta impressa, quando lida, abre o exame correto.

### [CARE-RF009] Ficha de trabalho
* **Context (Contexto)**: Modelo de ficha validado com a equipe.
* **Action (Ação)**: Gerar a ficha em PDF para impressão.
* **Result (Resultado)**: Ficha com nº interno, paciente e descrição de cada amostra.
* **Evaluation (Avaliação)**: A ficha de um exame com várias amostras confere com os dados recebidos.

### [CARE-RF010] Exame externo
* **Context (Contexto)**: Guia de encaminhamento e requisição em mãos.
* **Action (Ação)**: Registrar a pré-entrada, gerar a ficha para a Regulação e procurar a nova solicitação.
* **Result (Resultado)**: Pré-entrada vinculada à solicitação e liberada para recebimento.
* **Evaluation (Avaliação)**: Vínculo correto com a solicitação do paciente da pré-entrada.

### [CARE-RF011] Etapa inicial do externo
* **Context (Contexto)**: RF010 implementado.
* **Action (Ação)**: Permitir escolher a etapa inicial e marcar as etapas feitas fora.
* **Result (Resultado)**: Exame entra direto na fila da etapa escolhida.
* **Evaluation (Avaliação)**: Um externo com blocos e lâminas vai direto para a Microscopia.

### [CARE-RF012] Gravação assistida no AGHU
* **Context (Contexto)**: Pontos de gravação no AGHU mapeados.
* **Action (Ação)**: Criar pendências com o conteúdo pronto para copiar, incluindo o nº interno do exame.
* **Result (Resultado)**: Pendência fechada quando o dado aparece no AGHU; laudo no AGHU ligado ao nº interno do arquivo.
* **Evaluation (Avaliação)**: Com os dados de antes e de depois da gravação, a pendência passa de aberta para concluída; todo texto gerado contém o nº interno.

### [CARE-RF013] Encaminhamento entre setores
* **Context (Contexto)**: Exame com nº interno.
* **Action (Ação)**: Criar as ações "Encaminhar" e "Receber" (pelo leitor ou pelo nº digitado).
* **Result (Resultado)**: Passagem registrada dos dois lados.
* **Evaluation (Avaliação)**: O histórico aparece correto na consulta (RF024).

### [CARE-RF014] Filas de trabalho
* **Context (Contexto)**: Exames com etapa atual e urgência.
* **Action (Ação)**: Criar a fila por setor.
* **Result (Resultado)**: Ordenação por urgência e depois por chegada.
* **Evaluation (Avaliação)**: Ordem correta com exames urgentes e comuns de datas diferentes.

### [CARE-RF015] Fluxo de congelação
* **Context (Contexto)**: Exame CO recebido; escala de plantão cadastrada.
* **Action (Ação)**: Notificar o residente escalado (ou o escolhido na hora), registrar o ciclo e criar o vínculo com o HP.
* **Result (Resultado)**: HP vinculado aparece no Processamento após o Corte.
* **Evaluation (Avaliação)**: O alerta chega ao residente escalado do dia; ciclo completo com uma nova margem e entrada do HP na etapa correta.

### [CARE-RF016] Registro da macroscopia
* **Context (Contexto)**: Exame HP na Macroscopia.
* **Action (Ação)**: Criar o formulário de cassetes, processamento, coloração e sobra.
* **Result (Resultado)**: Lista de cassetes disponível para o Processamento.
* **Evaluation (Avaliação)**: Exame com cassetes A a J e sobra registrada.

### [CARE-RF017] Modelos de macroscopia
* **Context (Contexto)**: Modelos levantados com os macroscopistas.
* **Action (Ação)**: Permitir escolher o modelo e preencher os campos variáveis.
* **Result (Resultado)**: Texto gerado e enviado para a pendência do AGHU (RF012).
* **Evaluation (Avaliação)**: O texto de 3 modelos confere com os exemplos atuais da equipe.

### [CARE-RF018] Registro do processamento
* **Context (Contexto)**: Cassetes registrados ou exame cito recebido.
* **Action (Ação)**: Registrar cada etapa com data e técnico, inclusive pedidos de recorte e coloração especial.
* **Result (Resultado)**: Histórico de etapas completo.
* **Evaluation (Avaliação)**: Caminhos histotécnico, manual, cito sem fragmento e cito com cell-block.

### [CARE-RF019] Distribuição de lâminas
* **Context (Contexto)**: Processamento concluído.
* **Action (Ação)**: Registrar o nº de lâminas e o responsável pela leitura.
* **Result (Resultado)**: Exame na fila do responsável.
* **Evaluation (Avaliação)**: O CCV vai para o citotécnico e o HP para o residente.

### [CARE-RF020] Microscopia e laudo
* **Context (Contexto)**: Lâminas distribuídas.
* **Action (Ação)**: Registrar os estados da análise e o desfecho.
* **Result (Resultado)**: Exame encerrado com data de liberação e patologista responsável.
* **Evaluation (Avaliação)**: Quando o laudo aparece liberado no AGHU, o exame passa a encerrado.

### [CARE-RF021] Solicitação de complementos
* **Context (Contexto)**: Diagnóstico não fechado.
* **Action (Ação)**: Criar o pedido de complemento por tipo.
* **Result (Resultado)**: Pedido na fila do setor de destino; exame aguardando complemento.
* **Evaluation (Avaliação)**: O cito não oferece revisão de peça; cada tipo cai na fila certa.

### [CARE-RF022] Exame de IHQ vinculado
* **Context (Contexto)**: Pedido de IHQ feito na Microscopia.
* **Action (Ação)**: Gerar o nº IH vinculado ao exame de origem e registrar os anticorpos.
* **Result (Resultado)**: IHQ ligado ao HP ou cito, sem laudo próprio.
* **Evaluation (Avaliação)**: Duas rodadas de anticorpos mantêm o mesmo nº IH.

### [CARE-RF023] Retorno por erro
* **Context (Contexto)**: Exame na Macroscopia ou na Microscopia.
* **Action (Ação)**: Criar a ação "devolver à Recepção" guardando a etapa de origem.
* **Result (Resultado)**: Após a correção, o exame volta à etapa que o devolveu.
* **Evaluation (Avaliação)**: Uma devolução pela Microscopia volta à Microscopia, com o histórico preservado.

### [CARE-RF024] Consulta de status
* **Context (Contexto)**: Exames com histórico de etapas.
* **Action (Ação)**: Criar a busca pelos quatro identificadores.
* **Result (Resultado)**: Etapa atual, datas e responsáveis do exame.
* **Evaluation (Avaliação)**: As quatro formas de busca retornam o mesmo exame.

### [CARE-RF025] Painel de urgências
* **Context (Contexto)**: Exames marcados como urgentes.
* **Action (Ação)**: Criar o painel com etapa atual e tempo decorrido.
* **Result (Resultado)**: Visível para todos os perfis.
* **Evaluation (Avaliação)**: Urgências liberadas saem do painel.

### [CARE-RF026] Localização do material
* **Context (Contexto)**: Exame encerrado.
* **Action (Ação)**: Registrar o local de cada material.
* **Result (Resultado)**: A busca pelo nº interno mostra onde está cada material.
* **Evaluation (Avaliação)**: Um exame arquivado retorna os locais de lâminas, blocos e ficha.

### [CARE-RF027] Indicadores e prazos
* **Context (Contexto)**: Datas das etapas registradas.
* **Action (Ação)**: Calcular os tempos por etapa e sinalizar exames perto dos limites.
* **Result (Resultado)**: Relatório por período e destaque nas filas.
* **Evaluation (Avaliação)**: Indicadores conferidos contra dados de teste calculados à mão.

### [CARE-RF028] Responsável e edição concorrente
* **Context (Contexto)**: Usuários autenticados (RF001) e exames com etapas registráveis.
* **Action (Ação)**: Ao iniciar uma edição, reservar a etapa para o usuário; mostrar aos demais quem está editando e desde quando; liberar a reserva ao salvar, cancelar, expirar o tempo configurado ou transferir a responsabilidade.
* **Result (Resultado)**: Só uma pessoa edita a etapa por vez; os demais veem o responsável e acessam em modo leitura.
* **Evaluation (Avaliação)**: Com dois usuários abrindo o mesmo exame, o segundo vê o aviso com o nome do primeiro e não consegue salvar; após o primeiro salvar, o segundo consegue editar.

## 4. Pendências a validar com a equipe
- Quem abre a solicitação do externo no AGHU: a Regulação ou a Anatomia Patológica? (RF010)
- Há leitor de código de barras fora da recepção? (RF013)
- O pré-laudo do residente fica no sistema ou continua no AGHU? (RF020)
