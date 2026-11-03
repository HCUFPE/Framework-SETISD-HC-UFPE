# Especificação de Requisitos

## 1. Requisitos Funcionais (RF)
| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :---: |
| RF001 | Importação de dados | Importar dados de novos pacientes/solicitações de exame do AGHU diretamente para o sistema de AP. | Essencial |
| RF002 | Rastreabilidade de solicitações | Localizar e consultar solicitações de exames e acompanhar histórico. | Essencial |
| RF003 | Geração de ID interno | Atribuir um ID interno único a casos/amostras importadas do AGHU. | Essencial |
| RF004 | Consulta por ID | Consultar amostras por código de barras/qrcode. | Essencial |
| RF005 | Completude dos registros | Impedir conclusão de registro até que todos os campos sejam preenchidos, mantendo-os como rascunhos. | Essencial |
| RF006 | Recebimento de amostras | Permitir que o usuário confira os dados da solicitação e da amostra e confirme o seu recebimento no setor. | Essencial |
| RF007 | Registro de solicitações complementares | Registrar etapas complementares (IHQ, recoloração, relaminação) como eventos próprios na movimentação para medir retrabalho | Importante |
| RF008 | Impressão de etiqueta | Gerar e imprimir uma etiqueta de identificação da interna da amostra. | Essencial |
| RF009 | Gerência de permissões/visualização por perfil | Administrador atribui perfis de acordo com responsabilidades do usuário para garantir integridade de dados e simplicidade da interface | Importante |
| RF010 | Registro das etapas | Registrar o andamento da amostra nas diferentes etapas do diagnóstico. | Essencial |
| RF011 | Controle de urgências | Permitir identificar e filtrar solicitações de exame classificados como urgentes. | Essencial |
| RF012 | Rastreabilidade da amostra | Guardar informações sobre a data e responsável por cada etapa.| Essencial |
| RF013 | Painel gerencial de KPIs | Visualização de painel de KPIs sem dados identicáveis dos pacientes para perfil gerencial. | Desejável |
| RF014 | Máscaras de texto padrão | Oferecer máscaras de texto editáveis para macroscopia e microscopia | Importante |
| RF015 | Registro de conclusão do caso | Permitir realizar a conclusão do caso e armazenamento do laudo/responsável | Essencial |
| RF016 | Controle de exame externo | Registrar encaminhamentos de exames para o laboratório externo e acompanhar o andamento. | Essencial |
| RF017 | Visualização unificada de resultados | Administrador/residente tem acesso a tela com informações registradas para aprovação de maneira rápida e simples. | Importante |
| RF018 | Geração de ficha de trabalho | Gerar e imprimir uma ficha contendo os dados relativos ao caso para acompanhamento físico. | Desejável |
| RF019 | Registro de materiais produzidos | Registrar informações sobre recortes, cassetes, blocos e lâminas produzidos durante o processamento do caso. | Essencial |
| RF020 | Registro de não conformidades | Permitir registrar divergências de identificação, quantidade, integridade ou condições das amostras recebidas. | Essencial |
| RF021 | Controle de devolução e cancelamento | Registrar devoluções, cancelamentos e seus respectivos motivos, responsáveis e históricos. | Importante |
| RF022 | Alertas de estagnação | Destacar caso/emitir alertas quando um caso permanecer em uma etapa por mais tempo do que o esperado. | Desejável |
| RF023 | Controle de pendências | Identificar casos com etapas pendentes, indicando o que falta para permitir sua continuidade. | Essencial |
| RF024 | Painel de processos em andamentos | Gestão visualiza andamento de processos em tempo real em painel informando etapa atual, tempo desde o início do processamento, etc. | Importante |
| RF025 | Geração de documento de laudo para impressão | Após aprovação do residente, é gerado um arquivo formatado do laudo pronto para impressão. | Desejável |

### 📌 Legenda de Níveis de Prioridade:
- **Essencial (Alta):** Funcionalidade indispensável para o funcionamento básico da aplicação. Sem ela, o sistema não pode ir para produção (ex: autenticação, cadastros base).
- **Importante (Média):** Funcionalidade que agrega valor significativo ao negócio e melhora o fluxo de trabalho, mas cuja ausência temporária não impede a operação mínima (ex: relatórios, filtros avançados).
- **Desejável (Baixa):** Funcionalidade complementar, melhoria estética ou recurso secundário que pode ser implementado em sprints futuras (ex: temas visuais, atalhos de teclado).

## 2. Requisitos Não Funcionais (RNF)
| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF001 | Criptografia | Tokens JWT assinados com HS256 e Cookies HttpOnly para Refresh Tokens. |
| RNF002 | LGPD / Auditoria | Trilha de auditoria obrigatória (antes/depois) em tabela `audit_logs` para mutações. |
| RNF003 | Segurança HTTP | Middleware de Security Headers (anti-cache `no-store`, `X-Frame-Options: DENY`, anti-XSS). |
| RNF004 | Governança de segredos | Proibição de hardcode e validação de env vars na inicialização (`src/config.py`). |
| RNF005 | Governança híbrida | Definição de ponto único de controle no modelo Active Directory (AD) + RBAC. |
| RNF006 | Integridade de dados | Controle da manipulação de dados em acesso concorrente e estabelecimento de uma fonte de verdade. |
| RNF007 | Resiliência | Capacidade de operar ante eventual indisponibilidade do AGHU. |
| RNF008 | Usabilidade | Adequação ao fluxo de processos da unidade e à proficiência do usuários. |
| RNF009 | Desempenho | Consulta e cadastro em poucos segundos mesmo com uso simultâneo em todos os setores |
| RNF010 | Sincronização de dados | Atualização simultânea dos dados exibidos em acessos concomitantes distintos. |
| RNF011 | Manutenibilidade | Padronização, modularidade, documentação e testabilidade do código. |
| RNF012 | Compatibilidade e integração | Interoperabilidade com tecnologias e plataformas utilizadas pela unidade. |

## 3. Detalhamento SDD (CARE)
Para cada requisito, a implementação deve seguir o padrão:

# REQUISITOS FUNCIONAIS

### [CARE-RF001] Importação de dados
* **Context (Contexto)**: Existem novas solicitações de exame cadastradas no AGHU.
* **Action (Ação)**: O sistema consulta os dados disponíveis no AGHU e importa as informações necessárias para o sistema interno.
* **Result (Resultado)**: Os novos casos aparecem no sistema interno com os dados importados do AGHU associados corretamente à respectiva solicitação.
* **Evaluation (Avaliação)**: Verificar se os dados de um caso existente são importados automaticamente e corretamentamente para o sistema interno.

### [CARE-RF002] Rastreabilidade de casos
* **Context (Contexto)**: O técnico/médico está autenticado no sistema e existem solitações de exame cadastradas no sistema.
* **Action (Ação)**: O médico consulta um caso de anatomia patológica a partir do nome, status ou outro atributo e o sistema busca por um caso com atributo correspondente.
* **Result (Resultado)**: O sistema retorna as solicitações correspondentes ao que foi consultado e eles são exibidos na interface.
* **Evaluation (Avaliação)**: Verificar se a busca de uma solicitação acontece de maneira que as solicitações retornadas possuem atributos correspondentes aos atributos inseridos na busca.

### [CARE-RF003] Geração de ID
* **Context (Contexto)**: Existem solicitações de exames importadas do AGHU que precisam ser identificados de maneira única no sistema de Anatomia Patológica, independentemente dos identificadores utilizados no sistema de origem.
* **Action (Ação)**: O usuário importa um novo caso ou amostra do AGHU, e o sistema gera e associa automaticamente um identificador interno único ao registro importado.
* **Result (Resultado)**: O sistema armazena o identificador gerado e o associa ao respectivo caso ou amostra, permitindo sua identificação e rastreabilidade ao longo do fluxo de anatomia patológica.
* **Evaluation (Avaliação)**: Verificar se cada caso ou amostra importado recebe um identificador interno único, não duplicado entre os registros, persistente após consultas e atualizações e corretamente associado ao registro correspondente.

### [CARE-RF004] Consulta por ID
* **Context (Contexto)**: O usuário está autenticado e tem em mãos um material com etiqueta legível: a etiqueta do AGHU (antes do recebimento no setor) ou a etiqueta interna do Sistema AP (amostra, cassete/bloco ou lâmina).
* **Action (Ação)**: O usuário lê o código de barras/QR Code da etiqueta com o leitor (ou digita o código manualmente) e o sistema busca o registro correspondente.
* **Result (Resultado)**: O sistema abre o caso ao qual o código pertence, indicando qual item foi lido (amostra, cassete/bloco ou lâmina), a etapa atual e o histórico de movimentações.Se o código não existir, o sistema informa que nenhum registro foi encontrado.
* **Evaluation (Avaliação)**: Verificar se a leitura de cada tipo de etiqueta (AGHU, amostra, cassete/bloco, lâmina) abre exatamente o caso correspondente, se a digitação manual do código produz o mesmo resultado da leitura e se um código inexistente ou de outro caso não retorna dados indevidos.

### [CARE-RF005] Completude dos registros
* **Context (Contexto)**: O usuário está preenchendo o registro de uma etapa de um caso (recebimento, macroscopia, processamento, IHQ, microscopia, arquivamento etc.).
* **Action (Ação)**: O usuário tenta salvar o registro com campos obrigatórios em branco.
* **Result (Resultado)**: O sistema alerta o usuário sobre os campos obrigatórios em branco, com uma mensagem que lista os campos faltantes e com cada campo destacado na tela. O registro incompleto é salvo como rascunho, e o sistema impede que o processo continue: a conclusão da etapa fica bloqueada e o caso não avança para a etapa seguinte até que todos os campos obrigatórios estejam preenchidos. Um rascunho não conta como etapa concluída, e o alerta continua visível sempre que o registro for reaberto enquanto houver campos faltantes.
* **Evaluation (Avaliação)**: Verificar se, para cada tipo de exame e etapa, a tentativa de conclusão com qualquer campo obrigatório vazio exibe o alerta indicando todos os campos faltantes e é recusada, se o caso permanece na mesma etapa sem poder avançar enquanto houver pendências, se o rascunho é recuperado com os dados já preenchidos e se, com todos os campos preenchidos, o alerta desaparece e a etapa é concluída normalmente.

### [CARE-RF006] Recebimento de amostras
* **Context (Contexto)**: Uma amostra chega à recepção com a solicitação de exame já cadastrada no AGHU e a etiqueta do AGHU no recipiente. No caso de paciente externo, o cadastro do paciente e da solicitação no AGHU é feito antes, fora do Sistema AP. O Sistema AP apenas lê dados do AGHU e não grava nada nele.
* **Action (Ação)**: O profissional da recepção lê a etiqueta do AGHU no Sistema AP, confere os dados exibidos (paciente, prontuário, solicitação, exame, descrição do material e informações clínicas) com a amostra física e com a requisição e confirma a entrada no setor.
* **Result (Resultado)**: O sistema registra o recebimento com data/hora e responsável, gera o identificador interno e libera a impressão das etiquetas internas. Se a amostra não tiver etiqueta do AGHU ou se a conferência apontar divergência, o recebimento não é confirmado e segue para o registro de não conformidade e devolução. O registro do recebimento no AGHU continua sendo feito diretamente no AGHU, fora do Sistema AP.
* **Evaluation (Avaliação)**: Verificar se uma amostra com etiqueta do AGHU válida tem os dados da solicitação exibidos sem redigitação, se a confirmação registra data/hora, responsável e identificador interno, e se não é possível confirmar o recebimento de uma amostra sem solicitação correspondente no AGHU.

### [CARE-RF007] Registro de solicitações complementares
* **Context (Contexto)**: Durante a análise microscópica, o diagnóstico não foi fechado e o residente ou o patologista/preceptor precisa de uma etapa adicional: painel/ampliação de IHQ, recorte, nova coloração ou coloração especial, nova laminação, revisão da peça (retorno à macroscopia) ou material complementar.
* **Action (Ação)**: O médico registra a solicitação complementar no caso, informando o tipo, o detalhamento (ex.: anticorpos, coloração, blocos envolvidos) e a justificativa.
* **Result (Resultado)**: O sistema cria um evento próprio na movimentação do caso, vinculado à solicitação original, com solicitante, data/hora e setor de destino, e encaminha o caso de volta à etapa correspondente (processamento técnico, IHQ ou macroscopia). O registro da execução original não é sobrescrito. A conclusão do evento registra data/hora e responsável.
* **Evaluation (Avaliação)**: Verificar se cada solicitação complementar aparece como um evento distinto no histórico do caso, com tipo, solicitante, datas de abertura e conclusão e responsáveis, e se o painel de KPIs consegue contar esses eventos por tipo, setor e período para o indicador de taxa de retrabalho.

### [CARE-RF008] Impressão de etiqueta
* **Context (Contexto)**: O recebimento da amostra foi confirmado e o identificador interno foi gerado. Ao longo do processamento são produzidos derivados da amostra (cassetes/blocos e lâminas), e cada um também recebe identificação própria.
* **Action (Ação)**: O usuário solicita a impressão da etiqueta da amostra ou dos derivados registrados.
* **Result (Resultado)**: O sistema gera etiquetas com o número interno do item e um código de barras/QR Code que o identifica de forma única e o vincula ao caso.
* **Evaluation (Avaliação)**: Verificar se cada etiqueta impressa (amostra, cassete/bloco, lâmina) pode ser lida pelo leitor do setor e, na consulta por ID, abre o item e o caso corretos, e se dois itens distintos nunca recebem o mesmo código.

### [CARE-RF009] Gerência de permissões/visualização por perfil
* **Context (Contexto)**: Um usuário já cadastrado no Active Directory (AD) precisa acessar o sistema para executar as atividades do seu setor, e o Chefe de Unidade fez a solicitação formal de acesso.
* **Action (Ação)**: O administrador consulta o usuário no AD, cadastra-o no sistema e atribui, altera ou retira um ou mais perfis.
* **Result (Resultado)**: O usuário passa a ver e executar apenas as telas e ações permitidas aos seus perfis. Perfis gerenciais não veem dados que identifiquem pacientes. Toda atribuição, alteração ou retirada de perfil fica registrada na trilha de auditoria (categoria SEGURANCA), com autor, data/hora e estado anterior e novo.
* **Evaluation (Avaliação)**: Verificar se cada perfil acessa somente as funções previstas (inclusive por chamada direta à API, não só pela interface), se apenas o perfil administrador consegue gerenciar perfis, se a retirada de um perfil tem efeito no acesso seguinte do usuário e se cada mudança gera registro de auditoria.

### [CARE-RF010] Registro das etapas
* **Context (Contexto)**: Um caso recebido segue o fluxo próprio do seu tipo de exame, conforme o fluxograma TO-BE. Por exemplo: histopatológico (macroscopia → processamento técnico → microscopia → arquivo), citologia geral/líquidos (processamento técnico com centrifugação e, se houver, cell-block → microscopia), citopatológico, congelação (equipe de plantão), revisão de lâmina (direto à microscopia) e IHQ.
* **Action (Ação)**: Ao receber o material, cada setor lê o código da amostra (registrando o recebimento na etapa) e, ao final do trabalho, registra a conclusão da etapa com os dados que lhe cabem.
* **Result (Resultado)**: O sistema atualiza a etapa atual do caso e o encaminha para a etapa seguinte prevista para aquele tipo de exame. Cada setor só preenche os dados da sua própria etapa e não consegue registrar dados de outras etapas.
* **Evaluation (Avaliação)**: Verificar se, para cada tipo de exame, o caso percorre apenas as etapas previstas no fluxograma TO-BE, se a etapa atual exibida corresponde ao último registro e se o sistema recusa o registro de uma etapa fora de ordem ou por um setor diferente do responsável.

### [CARE-RF011] Controle de urgências
* **Context (Contexto)**: Uma amostra chega com pedido de prioridade e a recepção precisa sinalizá-la para os demais setores.
* **Action (Ação)**: O profissional da recepção marca o caso como urgente no recebimento. Nos demais setores, o usuário filtra as listas de trabalho para exibir os casos urgentes.
* **Result (Resultado)**: O caso urgente aparece destacado visualmente em todas as listas e telas em que é exibido, e o filtro retorna apenas os casos urgentes.
* **Evaluation (Avaliação)**: Verificar se a marcação feita na recepção aparece destacada em todos os setores pelos quais o caso passa, se o filtro de urgentes retorna todos e somente os casos marcados e se a marcação e eventuais alterações ficam no histórico do caso.

### [CARE-RF012] Rastreabilidade da amostra
* **Context (Contexto)**: Uma amostra ou um derivado (cassete/bloco, lâmina) passa por diferentes setores e responsáveis ao longo do fluxo, e o setor precisa saber onde ele está, por quais etapas passou e quem fez cada movimentação.
* **Action (Ação)**: Qualquer movimentação ou registro de etapa (recebimento, conclusão, solicitação complementar, devolução, arquivamento) é executado no sistema por um usuário autenticado.
* **Result (Resultado)**: O sistema grava automaticamente a data/hora, o usuário responsável (a partir da sessão, sem digitação) e o setor de cada movimentação, em um histórico que não pode ser alterado nem apagado. O histórico completo pode ser consultado a partir do caso ou de qualquer um dos seus itens.
* **Evaluation (Avaliação)**: Verificar se cada movimentação gera um registro com data/hora, usuário e setor corretos, se o responsável registrado é sempre o usuário autenticado e se nenhum perfil, inclusive administrador, consegue editar ou excluir registros do histórico.

### [CARE-RF013] Painel gerencial de KPIs
* **Context (Contexto)**: A chefia e a gestão precisam acompanhar o desempenho do setor sem consultar dados de pacientes.
* **Action (Ação)**: O usuário com perfil gerencial acessa o painel e filtra os indicadores por período, setor, etapa ou tipo de exame.
* **Result (Resultado)**: O sistema exibe, a partir dos registros de etapas, movimentações, solicitações complementares e não conformidades, os indicadores da seção 8 do documento de validação: taxa de retrabalho, tempo médio por etapa, taxa de laudos dentro do prazo, taxa de não conformidades, tempo médio até a liberação do laudo, taxa de amostras com não conformidades e taxa média de completude dos registros. Nenhum dado que identifique pacientes (nome, prontuário, nº de solicitação) é exibido ou exportado.
* **Evaluation (Avaliação)**: Verificar se os indicadores calculados conferem com uma contagem manual sobre uma massa de dados de teste conhecida e se o painel e suas exportações não contêm dados identificáveis de pacientes.

### [CARE-RF014] Máscaras de texto padrão
* **Context (Contexto)**: Na macroscopia, boa parte dos textos descritivos se repete para tipos comuns de material (ex.: BX GÁSTRICA, ÚTERO). As máscaras são cadastradas e mantidas pelo patologista/chefia e organizadas por tipo de material.
* **Action (Ação)**: O patologista/chefia cadastra, edita ou desativa máscaras por tipo de material. Na macroscopia de um caso, o responsável seleciona a máscara do tipo de material e ajusta o texto às características da peça.
* **Result (Resultado)**: O texto da máscara é carregado no registro da macroscopia do caso e pode ser editado livremente, sem alterar a máscara original. O texto final fica salvo no caso e pode ser copiado para o registro da macroscopia no AGHU, que continua sendo feito diretamente no AGHU. Alterações nas máscaras ficam registradas na trilha de auditoria (categoria CONFIGURACAO).
* **Evaluation (Avaliação)**: Verificar se apenas o perfil autorizado consegue criar ou alterar máscaras, se a edição do texto em um caso não modifica a máscara, se uma máscara alterada não modifica textos já salvos em casos anteriores e se as máscaras disponíveis são filtradas pelo tipo de material.

### [CARE-RF015] Registro de conclusão do caso
* **Context (Contexto)**: O residente registrou o parecer preliminar, o patologista/preceptor revisou e aprovou o laudo e o diagnóstico foi fechado.
* **Action (Ação)**: O patologista responsável registra a conclusão do caso no sistema com o texto do laudo/conclusão.
* **Result (Resultado)**: O sistema armazena o laudo, o patologista responsável, o residente envolvido e a data/hora da conclusão, muda o caso para concluído e o encaminha às etapas pós-analíticas (arquivamento e, quando aplicável, cadastro no Siscan). A liberação do laudo no AGHU continua sendo feita diretamente no AGHU.
* **Evaluation (Avaliação)**: Verificar se apenas o perfil de patologista consegue concluir um caso, se a conclusão exige a aprovação prévia do laudo pelo patologista/preceptor e o preenchimento dos campos obrigatórios, se responsável e data/hora ficam registrados e se o caso concluído não pode mais ser alterado.

### [CARE-RF016] Controle de IHQ externa
* **Context (Contexto)**: Foi solicitado painel/ampliação de IHQ para o caso e algum anticorpo necessário não está disponível internamente, então o material precisa ir para um laboratório externo.
* **Action (Ação)**: O usuário da IHQ registra o encaminhamento externo: laboratório de destino, data de envio, blocos/material enviados e anticorpos solicitados. Quando o resultado chega, registra o recebimento e anexa o PDF do resultado ao caso.
* **Result (Resultado)**: O caso passa a exibir a situação do encaminhamento externo (enviado, aguardando resultado, resultado recebido), com datas e responsáveis de cada movimentação, e o PDF fica disponível no caso para a análise microscópica. O anexo do resultado no AGHU continua sendo feito diretamente no AGHU.
* **Evaluation (Avaliação)**: Verificar se é possível listar todos os casos com IHQ externa pendente e há quanto tempo foram enviados, se o envio e o recebimento ficam registrados com data/hora e responsável e se o PDF anexado fica acessível no caso para os perfis autorizados.

### [CARE-RF017] Visualização unificada de resultados
* **Context (Contexto)**: O residente registrou o parecer preliminar do caso e o patologista/preceptor precisa revisá-lo e aprová-lo.
* **Action (Ação)**: O patologista/preceptor abre a tela de aprovação do caso, que reúne em um só lugar os dados da solicitação importados do AGHU, a macroscopia, os materiais produzidos, as solicitações complementares e seus resultados (inclusive IHQ interna e externa) e o parecer do residente. Em seguida, aprova o laudo ou o devolve ao residente com observações.
* **Result (Resultado)**: Na aprovação, o sistema registra o patologista que aprovou e a data/hora e libera o caso para conclusão.
* **Evaluation (Avaliação)**: Verificar se todas as informações do caso aparecem na tela sem necessidade de abrir outras telas ou o AGHU, se apenas o perfil de patologista/preceptor consegue aprovar e se aprovações e devoluções ficam registradas com autor e data/hora.

### [CARE-RF018] Geração de ficha de trabalho
* **Context (Contexto)**: O caso foi recebido no setor e o material físico circula entre os setores acompanhado de uma ficha impressa para acompanhamento.
* **Action (Ação)**: O usuário solicita a geração da ficha de trabalho do caso.
* **Result (Resultado)**: O sistema gera um documento pronto para impressão com os dados de identificação do caso (número interno com código de barras/QR Code, dados da solicitação e do material) e os espaços necessários ao acompanhamento físico.
* **Evaluation (Avaliação)**: Verificar se a ficha gerada contém os dados corretos do caso, se o código impresso na ficha abre o caso na consulta por ID e se a impressão funciona nas impressoras do setor.

### [CARE-RF019] Registro de materiais produzidos
* **Context (Contexto)**: Durante a macroscopia e o processamento técnico, a amostra dá origem a recortes, cassetes, blocos de parafina e lâminas e cada um precisa ser rastreado individualmente.
* **Action (Ação)**: O responsável pela macroscopia registra a clivagem (fragmentos e cassetes, sobra em fixador, coloração especial pedida). O técnico registra a rota de processamento (histotécnico ou manual), os blocos e as lâminas produzidos.
* **Result (Resultado)**: Cada cassete/bloco e cada lâmina passa a existir como um item próprio, com identificador e etiqueta, vinculado à amostra de origem (amostra → cassete/bloco → lâmina), com data/hora e responsável pela produção. Os materiais gerados por solicitações complementares ficam vinculados ao evento que os originou.
* **Evaluation (Avaliação)**: Verificar se cada item produzido recebe um identificador único vinculado à amostra correta, se a consulta a um caso mostra a árvore completa de materiais com as quantidades corretas e se a leitura do código de qualquer item leva ao caso de origem.

### [CARE-RF020] Registro de não conformidades
* **Context (Contexto)**: A amostra ou um de seus derivados apresenta divergência de identificação, quantidade, integridade ou condições (ou chega sem etiqueta do AGHU). O ideal é que a não conformidade seja identificada na conferência da recepção, mas ela também pode ser identificada nas etapas seguintes (macroscopia, processamento técnico, IHQ, microscopia etc.). Em qualquer etapa, a não conformidade leva à devolução do material à unidade de origem e à solicitação de uma nova amostra correta.
* **Action (Ação)**: O profissional do setor que identificou o problema registra a não conformidade: tipo da inconformidade (a partir de uma lista padronizada), detalhamento, solicitação AGHU, exame, origem, médico solicitante e especialidade.
* **Result (Resultado)**: O sistema grava a não conformidade com data/hora, o profissional que a registrou e o setor e a etapa em que foi identificada, interrompe o fluxo do caso e inicia a devolução com solicitação de nova amostra, vinculada à ocorrência.
* **Evaluation (Avaliação)**: Verificar se é possível registrar uma não conformidade a partir de qualquer etapa, se o registro exige o tipo e o detalhamento da inconformidade e grava automaticamente o setor e a etapa, se o caso com não conformidade não consegue mais avançar no fluxo e se as ocorrências são contabilizadas por tipo, setor e etapa nos indicadores de não conformidade.

### [CARE-RF021] Controle de devolução e cancelamento
* **Context (Contexto)**: A devolução é o retorno do material à unidade de origem, sempre decorrente de uma não conformidade, que pode ter sido identificada na recepção ou em uma etapa posterior. Ela vem acompanhada da solicitação de uma nova amostra correta. O cancelamento encerra um caso já aberto no setor e só pode ser feito por perfil de chefia/administrador.
* **Action (Ação)**: Na devolução, o profissional registra o motivo, quem devolveu, quem recebeu o material na unidade de origem e a solicitação de nova amostra. No cancelamento, a chefia/administrador informa obrigatoriamente o motivo.
* **Result (Resultado)**: O sistema registra a devolução ou o cancelamento com data/hora, responsáveis, motivo e, na devolução, o setor/etapa de onde o material saiu. Em seguida, muda o status do caso (devolvido ou cancelado) e o retira das listas de trabalho ativas. Nenhum registro é excluído fisicamente: o caso e todo o seu histórico, inclusive os materiais já produzidos, continuam disponíveis para consulta e auditoria.
* **Evaluation (Avaliação)**: Verificar se a devolução não pode ser registrada sem motivo e sem a não conformidade correspondente, se ela pode ser feita a partir de qualquer etapa em que a não conformidade foi identificada, se perfis sem permissão de chefia/administrador não conseguem cancelar casos, se casos devolvidos ou cancelados deixam de aparecer nas filas de trabalho e se o histórico anterior permanece íntegro e consultável.

## [CARE-RF022] Alertas de estagnação
* **Context (Contexto):** Os casos possuem data limite para fechar o diagnóstico. Algumas amostras podem estar estagnadas em etapas por mais tempo que o desejado.
* **Action (Ação):** O sistema informa há quanto tempo a amostra permanece na etapa, podendo emitir alerta caso passe do tempo padrão.
* **Result (Resultado):** O sistema calcula o tempo da amostra na etapa, destaca quando deveria estar se aproximando da finalização e emite alertas quando ultrapassa o tempo padrão.
* **Evaluation (Avaliação):** Verificar se o tempo contado no sistema condiz com a realidade, bem como analisar os tempos padrões das etapas.

## [CARE-RF023] Controle de pendências
* **Context (Contexto):** Todos os processos, para cada amostra, devem ser devidamente registrados.
* **Action (Ação):** O sistema indica/destaca os processos pendentes.
* **Result (Resultado):** O sistema calcula o tempo da amostra na etapa, destaca quando deveria estar se aproximando da finalização e emite alertas quando ultrapassa o tempo padrão.
* **Evaluation (Avaliação):** Verificar se as etapas possuem lacunas nos processos do sistema e indicar corretamente quais são.

## [CARE-RF024] Painel de processos em andamentos
* **Context (Contexto):** Durante o andamento do material, todas as etapas devem ser atualizadas em tempo real e visíveis para a gestão/equipe.
* **Action (Ação):** O sistema indica/destaca os processos pendentes.
* **Result (Resultado):** Interface dentro do sistema que sintetize o andamento das etapas.
* **Evaluation (Avaliação):** Verificar se os processos estão atualizados e condizentes com a realidade.

## [CARE-RF025] Geração de documento de laudo para impressão
* **Context (Contexto):** Após a amostra passar pelos procedimentos necessários, um documento constando o diagnóstico deve ser emitido e enviado para o AGHU.
* **Action (Ação):** O sistema gera um arquivo formatado pronto para a impressão.
* **Evaluation (Avaliação):** Verificar se o resultado do diagnóstico emitido confere ao que o médico patologista laudou.

# REQUISITOS NÃO FUNCIONAIS

## [CARE-RNF001] Criptografia
* **Context (Contexto):** O sistema armazena e processa informações sensíveis relacionadas aos pacientes e aos procedimentos de anatomia patológica. Portanto, é necessário proteger o acesso às informações e impedir que usuários não autorizados acessem os dados.
* **Action (Ação):** O sistema deverá utilizar tokens JWT assinados com HS256 para validar a autenticidade dos tokens de acesso e armazenar os tokens de renovação (Refresh Tokens) em cookies com a propriedade HttpOnly, reduzindo o risco de acesso a esses tokens por scripts executados no navegador.
* **Evaluation (Avaliação):** Verificar se requisições sem autenticação válida ou com tokens inválidos, adulterados ou expirados são rejeitadas. Confirmar também que os Refresh Tokens não podem ser acessados diretamente por JavaScript no navegador e que a renovação da autenticação funciona somente com tokens válidos.

## [CARE-RNF002] Registro de auditoria das alterações

* **Context (Contexto):** O sistema gerencia informações sensíveis de pacientes e registros de procedimentos de anatomia patológica. É necessário rastrear as operações realizadas para garantir a rastreabilidade das alterações e apoiar a investigação de acessos ou modificações indevidas.
* **Action (Ação):** O sistema deverá registrar em uma tabela de auditoria (audit_logs) as operações de alteração de dados, incluindo o usuário responsável, a data e hora, o tipo de operação e os valores anteriores e posteriores, quando aplicável.
* **Evaluation (Avaliação):** Verificar se as operações de alteração geram registros de auditoria completos e se é possível identificar quem realizou cada alteração, quando ocorreu e quais informações foram modificadas. Confirmar que usuários comuns não podem alterar ou excluir indevidamente os registros de auditoria.

## [CARE-RNF003] Proteção das respostas HTTP

* **Context (Contexto):** O sistema disponibiliza informações de pacientes e procedimentos por meio de requisições HTTP. É necessário reduzir os riscos de exposição indevida de dados, carregamento do sistema em páginas maliciosas e execução de scripts não autorizados.
* **Action (Ação):** O backend deverá configurar cabeçalhos HTTP de segurança, incluindo Cache-Control: no-store para respostas que contenham informações sensíveis, X-Frame-Options: DENY para impedir que a aplicação seja incorporada em frames de outros sites e uma política de segurança contra ataques de scripts (XSS).
* **Evaluation (Avaliação):** Inspecionar os cabeçalhos das respostas HTTP e verificar se as configurações esperadas estão presentes. Confirmar que páginas protegidas não podem ser incorporadas em frames externos e que as medidas adotadas reduzem os riscos de exposição e execução de scripts maliciosos.

## [CARE-RNF004] Gerenciamento seguro de credenciais e configurações

* **Context (Contexto):** O sistema utiliza credenciais, chaves secretas e configurações necessárias para acessar serviços e bancos de dados. A exposição dessas informações pode comprometer a segurança dos dados dos pacientes.
* **Action (Ação):** O sistema deverá armazenar informações sensíveis em variáveis de ambiente ou em mecanismos seguros de gerenciamento de segredos, proibindo a inclusão de credenciais diretamente no código-fonte. As variáveis necessárias deverão ser validadas durante a inicialização da aplicação.
* **Evaluation (Avaliação):** Verificar se o sistema funciona com as configurações fornecidas pelo ambiente, se a inicialização identifica variáveis obrigatórias ausentes ou inválidas e se nenhuma credencial sensível está exposta no código-fonte ou nos registros da aplicação.

## [CARE-RNF005] Controle centralizado de acesso

* **Context (Contexto):** Diferentes profissionais podem utilizar o sistema de anatomia patológica, mas nem todos devem ter acesso às mesmas informações e operações. É necessário centralizar as regras de acesso para evitar permissões inconsistentes entre os módulos.
* **Action (Ação):** O sistema deverá adotar um ponto central de controle de acesso, integrando o mecanismo de autenticação definido pela arquitetura ao modelo RBAC (Role-Based Access Control), no qual as permissões são atribuídas conforme os papéis dos usuários.
* **Evaluation (Avaliação):** Verificar se usuários com diferentes papéis possuem somente as permissões correspondentes às suas responsabilidades e se as regras de acesso são aplicadas de maneira consistente em todos os módulos e operações protegidas.

## [CARE-RNF006] Integridade e consistência dos dados
* **Context (Contexto):** A utilização simultânea do sistema por profissionais de diferentes setores pode ocasionar alterações concorrentes nos mesmos registros. É necessário evitar perda de atualizações, inconsistências e divergências nas informações sobre pacientes, amostras e exames.
* **Action (Ação):** O sistema deverá implementar mecanismos de controle de concorrência e integridade dos dados, utilizando o banco de dados como fonte oficial das informações e definindo regras para validar e tratar alterações simultâneas.
* **Evaluation (Avaliação):** Simular alterações simultâneas em um mesmo registro e verificar se os dados permanecem consistentes, se as regras de integridade são respeitadas e se conflitos são tratados sem perda silenciosa de informações.

## [CARE-RNF007] Continuidade operacional diante da indisponibilidade do AGHU

* **Context (Contexto):** O sistema precisa interoperar com o AGHU, mas esse sistema externo pode ficar temporariamente indisponível. Essa situação não deve comprometer desnecessariamente o registro das etapas internas da anatomia patológica.
* **Action (Ação):** O sistema deverá tratar falhas de comunicação com o AGHU de maneira controlada, permitindo a continuidade das operações internas que não dependam diretamente da integração e prevendo mecanismos seguros para reprocessar ou sincronizar operações pendentes após o restabelecimento da comunicação.
* **Evaluation (Avaliação):** Simular a indisponibilidade do AGHU e verificar se as operações internas independentes continuam funcionando, se as falhas são registradas e se as operações pendentes podem ser processadas posteriormente sem duplicação ou perda de dados.

## [CARE-RNF008] Adequação da interface ao fluxo de trabalho

* **Context (Contexto):** Atualmente, parte do acompanhamento das atividades de anatomia patológica é realizada por meio de planilhas Excel. A transição para um sistema próprio exige uma interface adequada às atividades dos profissionais, reduzindo dificuldades de utilização e erros de preenchimento.
* **Action (Ação):** A interface deverá apresentar informações de maneira clara e organizada, oferecer formulários compatíveis com as atividades da unidade e permitir a execução das tarefas rotineiras com facilidade, respeitando os diferentes perfis de usuários.
* **Evaluation (Avaliação):** Realizar testes de usabilidade com representantes dos perfis de usuários e verificar se conseguem executar tarefas típicas, como localizar uma amostra, atualizar uma etapa e consultar o andamento de um exame, com baixo índice de erros e sem dificuldades significativas.

## [CARE-RNF009] Desempenho das operações do sistema
* **Context (Contexto):** O sistema será utilizado por profissionais de diferentes setores, possivelmente de forma simultânea. Respostas lentas podem prejudicar o fluxo de trabalho e atrasar o registro e a consulta de informações.
* **Action (Ação):** O sistema deverá executar operações de consulta e cadastro em tempo adequado, mesmo sob uso simultâneo, adotando estratégias de otimização quando necessário.
* **Evaluation (Avaliação):** Realizar testes de desempenho com diferentes quantidades de usuários simultâneos, medindo o tempo de resposta das consultas e dos cadastros. Os limites aceitáveis de tempo e a quantidade esperada de usuários deverão ser definidos previamente com base nas necessidades da unidade.

## [CARE-RNF010] Sincronização das informações entre usuários

* **Context (Contexto):** Diferentes profissionais podem consultar ou modificar os mesmos registros simultaneamente. É necessário garantir que as informações exibidas na interface correspondam aos dados registrados no backend e que as atualizações relevantes sejam disponibilizadas aos demais usuários.
* **Action (Ação):** O sistema deverá sincronizar as informações entre frontend e backend e propagar as alterações confirmadas aos usuários envolvidos, utilizando um mecanismo de atualização adequado aos requisitos de comunicação da aplicação. Deverá também tratar conflitos decorrentes de edições simultâneas.
* **Evaluation (Avaliação):** Abrir o mesmo registro em diferentes sessões, realizar alterações e verificar se as atualizações confirmadas são refletidas nas demais sessões dentro do intervalo definido pelo projeto. Confirmar também que edições concorrentes não provocam perda silenciosa de dados.

## [CARE-RNF011] Manutenibilidade e organização do código

* **Context (Contexto):** O sistema poderá receber novas funcionalidades, correções e adaptações conforme as necessidades da unidade de anatomia patológica. Um código desorganizado ou sem documentação pode dificultar essas atividades e aumentar o risco de erros.
* **Action (Ação):** O projeto deverá seguir padrões de codificação, manter os componentes organizados em módulos com responsabilidades definidas, documentar aspectos relevantes da arquitetura e utilizar testes automatizados para verificar comportamentos importantes.
* **Evaluation (Avaliação):** Verificar a conformidade com os padrões definidos, a existência de documentação e testes relevantes e a possibilidade de modificar ou corrigir um módulo sem provocar falhas inesperadas em outros componentes.

## [CARE-RNF012] Interoperabilidade com sistemas externos

* **Context (Contexto):** O sistema de anatomia patológica precisa integrar-se ao AGHU e poderá precisar interagir com outras tecnologias e plataformas utilizadas pela unidade. A ausência de mecanismos padronizados de comunicação pode dificultar a troca de informações e gerar retrabalho.
* **Action (Ação):** O sistema deverá disponibilizar mecanismos de integração compatíveis com as interfaces, os formatos de dados e os protocolos suportados pelos sistemas externos envolvidos, respeitando os requisitos de segurança, autenticação e validação das informações trocadas.
* **Evaluation (Avaliação):** Realizar testes de integração para verificar se as informações são transmitidas, recebidas e interpretadas corretamente pelos sistemas envolvidos, preservando sua integridade e identificando adequadamente falhas de comunicação.
