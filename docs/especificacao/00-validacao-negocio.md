# [NOME DO SISTEMA] — Documento de Validação e Especificação de Negócio

> **Padrão Oficial SETISD / HC-UFPE (HU Brasil) — Fase 0 (Alinhamento de Negócio)**  
> **Público-alvo:** Profissionais das áreas envolvidas e Equipe de TI.  
> **Objetivo:** Descrever o processo de trabalho em **linguagem pura de negócio** (sem jargões técnicos de programação ou banco de dados) para validação, alinhamento de expectativas e tomada de decisão antes de qualquer codificação.

---

## 1. Identificação do Projeto e Contexto Institucional

| Campo | Descrição |
| :--- | :--- |
| **Nome do Sistema** | [Sistema de Integração com o AGHU] |
| **Área Solicitante / Cliente** | [SERVIÇO DE ANATOMIA PATOLÓGICA-SAP da Unidade de Análises Clínicas e Anatomia Patológica] |
| **Instância Superior Competente** | [HC-UFPE]
| **Líder Técnico (SETISD)** | [Daniel Turmina] |
| **Objetivo Estratégico HU Brasil** | [Vincular o projeto aos objetivos do HU Brasil] |

---

## 2. O Problema que Queremos Resolver

> **Objetivo:** Dizer com clareza qual é o problema real de trabalho. Sem rodeios: o que hoje está quebrado, ineficiente ou gerando risco para o hospital?
Hoje o controle de exames do Serviço de Anatomia Patológica (SAP) depende de 3 controles paralelos que não se conversam: o sistema oficial (AGHU), uma planilha interna e o livro de registro manual.Essa separação gera quebra de fluxo constante. Quando um dado não é copiado de um local para o outro, o exame "some" do controle, perde-se a rastreabilidade de onde ele está e em que fase se encontra. Além disso, não existe obrigatoriedade de preenchimento. Como não há trava de validação, exames avançam de etapa mesmo com informações essenciais faltando, o que gera retrabalho e risco de liberação incompleta.
* **A Dor Central:**  
  [Resumo direto da dor em 1 ou 2 frases. A equipe acaba utilizando muito tempo controlando a planilha e o livro. A falta de rastreabilidade e de obrigatoriedade de preenchimento aumenta o risco de erro humano, perda de informação e atraso na entrega do laudo ao paciente.]

* **Por que isso não pode continuar (Impactos Reais):**
  - **Sobrecarga de Trabalho:** As chefias e equipes perdem horas redigitando dados e conferindo manualmente tarefas que poderiam ser automáticas.
  - **Falta de Visibilidade:** A gestão não sabe em tempo real quem já entregou, quem está com pendências e onde estão os gargalos.
  - **Risco Institucional e Legal:** Falta de histórico confiável para responder a auditorias, questionamentos de órgãos de controle ou conferências internas.

---
> 
## 3. Como o Processo Funciona Hoje (A Rotina Atual) - Baseado no fluxo realMeios Utilizados Hoje:
* **Meios Utilizados Hoje:** AGHU (sistema oficial), ficha de trabalho em papel, planilha eletrônica de controle interno, livro físico de protocolo, etiquetas de código de barras e cassetes.A Rotina Prática de Trabalho:1. FASE PRÉ-ANALÍTICA - Recepção, Triagem e Arquivamento;
**Objetivo:** Mapear a realidade crua de como as equipes se viram no dia a dia para realizar essa tarefa hoje - Tudo começa na recepção. A amostra chega do HU ou externa.
Se for interna, precisa conferir se a solicitação existe no AGHU. Se for externa, precisa cadastrar paciente no AGHU e criar a solicitação. Se qualquer dado ou amostra vier inconsistente, devolve para o setor de origem.
Se estiver OK, gera número de solicitação e código de barras, bipa etiqueta, imprime a ficha de trabalho e registra TUDO DE NOVO na planilha de controle interno para gerar o número interno.
Se for caso de congelamento, aciona equipe de plantão e registra no livro de protocolo. Ao final, amostra + ficha vão pra Macroscopia.Quebra aqui: O mesmo exame é digitado 3x: no AGHU, na planilha interna e no livro. O código de barras não carrega dados suficientes para um fluxo dinâmico, obrigando a reconsulta ao AGHU.2. FASE ANALÍTICA - Macroscopia / Congelamento
Chega amostra e ficha. Se for para congelamento, faz análise macroscópica preliminar, faz o congelamento e cortes e registra no AGHU.
Se não for congelamento, gera os cassetes, registra na planilha interna e registra a análise macroscópica no AGHU. Depois envia ficha + cassetes para o processamento técnico.Quebra aqui: Controle da planilha interna de novo. Sem ela, a equipe não sabe onde o exame está.3. FASE ANALÍTICA - Processamento Técnico
É o laboratório. Recebe do macro. Se for líquido, centrifuga, verifica se precisa de Cell Block, faz inclusão, corte, coloração, montagem e distribuição. Tudo manual.4. FASE ANALÍTICA - Microscopia
Chega material de 3 lugares diferentes: do processamento técnico, da recepção (revisão de lâmina) e do IHQ.
A checagem é feita com residentes e preceptoria. Se fechou diagnóstico, vai pro arquivo. Se não fechou, pede painel/ampliação de IHQ ou recorte/coleta especial e volta pra Macroscopia. É um ciclo.5. FASE PÓS-ANALÍTICA - Arquivo
Vem da microscopia. Faz o laudo no AGHU e gera o PDF. Se precisar de SISCAN, cadastra. Depois arquiva a ficha de trabalho física e finaliza.

## 4. O Que a Nova Solução Deve Entregar (Resultado Esperado)

> **Objetivo:** Definir com clareza o que a solução digital deve trazer para eliminar a dor do processo atual.
Definir com clareza o que a solução digital deve trazer para eliminar a dor do processo atual, respeitando a governança do AGHU.
* **A Proposta de Valor:** A Proposta de Valor:
Qualificar a camada que já existe. Hoje a ficha de trabalho já nasce com dados do AGHU, porém com informações faltantes e redundantes que obrigam a equipe a complementar à mão e a reconsultar o AGHU. A proposta é que a ficha passe a nascer completa e limpa, com todos os dados necessários já organizados, sem redundância. A planilha de controle interno, que hoje exige inserção manual, é substituída pelo sistema. O que antes era digitado linha a linha, passa a ser gerado automaticamente a partir da movimentação do exame. O esforço manual de inserção é reduzido ou eliminado.Ganhos Práticos Imediatos:Ficha de trabalho qualificada: Correção da coleta atual do AGHU. Fim de dados faltantes e fim de dados redundantes na ficha. A equipe para de completar ficha à mão.Fim da digitação na planilha: A planilha de controle interno deixa de ser um controle manual paralelo. Ela é substituída por um painel digital onde a inserção manual é eliminada. O sistema registra automaticamente a entrada, a fase atual e a saída.Redução drástica do trabalho manual: O ganho não é "tirar o papel", é tirar a redigitação. O que hoje é copiado do AGHU para a ficha e depois copiado da ficha para a planilha, passa a acontecer uma única vez e de forma automática.Conferência na origem: Antes de liberar a amostra para a macroscopia, o sistema valida se os dados vindos do AGHU estão completos. Se vier faltante, já alerta na recepção, não na microscopia.Rastreabilidade real: Mesmo mantendo o livro físico por exigência operacional, a gestão passa a saber em tempo real onde cada exame está, sem precisar abrir planilha ou folhear livro.
* **Ganhos Práticos Imediatos:**
Livro de registro embutido no sistema com assinatura eletrônica: O atual livro físico de protocolo deixa de ser um caderno à parte e passa a ser uma funcionalidade do sistema. Cada movimentação do exame já é o registro no livro, com assinatura eletrônica de quem recebeu, quem encaminhou e data/hora automática. Fim da redundância de assinar no sistema e assinar de novo no livro.Ficha de trabalho qualificada: Correção da coleta do AGHU. A ficha passa a nascer completa e sem dados redundantes, eliminando o preenchimento manual complementar.Fim da digitação manual na planilha: A planilha de controle interno é substituída pelo próprio Livro Eletrônico. O que hoje é digitado à mão passa a ser gerado automaticamente.Trava de obrigatoriedade na origem: O sistema só libera a impressão da ficha e a geração do cassete se os dados vindos do AGHU estiverem completos.Painel de rastreabilidade em tempo real: A gestão visualiza em tela onde cada exame está, com base no Livro Eletrônico, sem precisar folhear o livro físico.
---

## 5. Como Será o Trabalho no Novo Sistema (O Novo Fluxo)

Objetivo: Explicar em linguagem direta como o usuário vai interagir com o sistema, resolvendo a dor do processo manual de ponta a ponta.
1. Os dados já vêm prontos e qualificados do AGHU: Ao receber a amostra, o técnico não precisa mais redigitar ou complementar a ficha à mão. Ao bipar a requisição, a ficha de trabalho já nasce completa, sem dados faltantes ou redundantes, com todas as informações necessárias vindas do AGHU organizadas para a bancada.
2. Conferência rápida com travas contra erros: Na recepção, o sistema valida automaticamente se a solicitação no AGHU existe e está completa. Se houver inconsistência ou dado essencial faltando, avisa na hora, antes da amostra ir para a macroscopia. Fim do erro descoberto só na hora do laudo.
3. Tramitação com livro embutido e assinatura eletrônica: Concluída cada fase (recepção, macro, processamento, micro), o responsável encaminha o exame com um clique. Esse clique já é o registro no Livro de Protocolo Eletrônico, com assinatura eletrônica, data, hora e nome de quem fez. Não há mais necessidade de assinar no sistema e depois assinar no livro físico. O livro passa a ser o próprio sistema.
4. Informação pronta e rastreável: A chefia acompanha em tempo real em um painel onde cada amostra está, há quanto tempo está parada em cada fase e quem está com ela. A planilha de controle interno deixa de existir como digitação manual. O histórico completo do exame, com todas as movimentações, fica guardado e fácil de consultar para auditoria ou acreditação, sem precisar folhear livro ou abrir planilha.

---

## 6. Quem Participa do Processo (Atores: Como Faz Hoje vs. Como Fará no Sistema)

| Ator / Perfil no Hospital | O que faz HOJE (Rotina Manual) | O que passará a fazer no NOVO SISTEMA | O que NÃO poderá fazer |
| :--- | :--- | :--- | :--- |
|Recepção / Técnico Administrativo|Recebe a amostra, confere no AGHU, complementa a ficha de trabalho à mão com dados que faltaram, digita na planilha e registra no livro físico.Bipa a requisição. O sistema traz a ficha já qualificada do AGHU e gera automaticamente o registro no Livro Eletrônico|Confere e encaminha com um clique e assinatura eletrônica|Não poderá avançar amostras com dados obrigatórios do AGHU faltantes. O sistema trava|
|Médico Patologista|Macroscopia.Descreve a macro na ficha de papel e assina no livro a saída da peça,Registra a macro direto no sistema|Ao finalizar, o encaminhamento para o processamento já assina eletronicamente o Livro Eletrônico|Nada diferente do que já faz|
|Técnico de Histologia/Processamento| Recebe cassetes, anota em planilha paralela o que entrou e o que saiu para coloração.Bipa os cassetes na entrada e na saída de cada etapa (processamento, inclusão, microtomia, coloração)|O sistema atualiza automaticamente o painel e o Livro Eletrônico|
| **Área Gestora do Processo** *(Ex: Unidade de Pessoal, Farmácia Central, Regulação)* | Cobra prazos por telefone/e-mail, confere pilhas de papel ou junta dezenas de planilhas dispersas. | Habilita os períodos de trabalho, cadastra regras gerais, publica o resultado final e acompanha o painel geral de pendências em tempo real. | Não preenche dados rotineiros operacionais de setores individuais. | Não poderá visualizar ou editar exames de outros patologistas sem permissão.
| **Profissional do Setor / Executante** *(Quem realiza o atendimento ou rotina na ponta)* | Preenche formulário impresso ou Excel local, correndo risco de esquecer dados ou duplicar lançamentos. | Lança os dados direto no sistema com validações em tempo real e encaminha a sua parte para conferência da chefia. | Não visualiza nem altera dados de setores que não sejam de sua alçada. |
| **Chefia Imediata / Responsável pelo Setor** *(Ex: Chefia de Unidade ou Setor)* | Confere folhas rubricadas à mão na mesa física, assina no papel e leva as pastas fisicamente. | Visualiza em uma tela única o trabalho da sua equipe, faz ajustes rápidos e aprova eletronicamente com um clique. | Não pode enviar lotes parciais ou com pendências em aberto. |
| **Gestão / Coordenação Superior** *(Ex: Chefia de Divisão ou Gerência* | Não tem visão em tempo real das entregas; depende de relatórios manuais solicitados e demorados. | Acompanha indicadores gerais em tempo real (painel executivo com taxas de cumprimento de prazos e pendências). | Acesso estritamente para visualização gerencial (não edita registros operacionais). |
| **Público / Usuário do Serviço** *(Colaboradores do hospital, pacientes ou cidadãos)* | Precisa ligar, mandar e-mail ou ir presencialmente ao setor para obter uma informação ou comprovante. | Consulta com agilidade pelo portal, pesquisando por nome ou setor, com rapidez e transparência garantida. | Não tem acesso a dados restritos ou confidenciais. |.Não poderá pular fases. O sistema só permite avançar se a fase anterior foi registrada|
|Médico Patologista - Microscopia | Laudo | Faz o laudo em sistema à parte ou digita, depois precisa atualizar planilha e assinar livro|Registra o laudo no sistema, com assinatura eletrônica. O ato de laudar encerra automaticamente o fluxo no Livro Eletrônico e libera o resultado para consulta|Não poderá laudar sem que todo o rastro de processamento esteja registrado.|
|Chefia do SAP|Área Gestora|Cobra por telefone/WhatsApp onde está cada exame, junta planilhas e folheia livro para achar atrasos|Acompanha painel em tempo real de todas as amostras, gargalos por fase, tempo de permanência e pendências. Gera relatórios de produtividade e TAT com um clique|Não preenche dados operacionais de bancada. Acesso é gerencial e de auditoria.Gestão Superior / QualidadePede relatórios manuais que levam dias para ficarem prontos para acreditação.Consulta histórico inviolável e rastreável de qualquer exame a qualquer momento, com quem fez, quando fez e quanto tempo ficou em cada fase.Acesso apenas para visualização gerencial. Não edita registros operacionais.

---

## 7. Regras de Negócio Inegociáveis (RNs)

* **RN-01 (AGHU como fonte oficial e somente leitura):** O sistema NUNCA insere, altera ou exclui dados no AGHU. Atua exclusivamente como consumidor. Toda identificação do paciente, nº da requisição, solicitante e CID vem do AGHU via leitura. Qualquer inconsistência deve ser corrigida na origem (AGHU) e será re-refletida no SAP após nova coleta.
* **RN-02 (Qualificação da ficha e fim da redundância):** A ficha de trabalho deve nascer já qualificada. O sistema deve sanar a dor atual de dados faltantes e redundantes vindos do AGHU, organizando e completando a ficha com o que já existe no AGHU, sem exigir complementação manual à mão. É vedada a redigitação de dados que já existem no AGHU.
* **RN-03 (Livro de Protocolo Eletrônico embutido com assinatura eletrônica):** Fica instituído o Livro de Registro Eletrônico como funcionalidade nativa do sistema. Cada movimentação de fase (recepção, macroscopia, processamento, microscopia, laudo) gera automaticamente o registro no livro, com assinatura eletrônica institucional, data, hora e matrícula do responsável. Este registro substitui o livro físico como fonte oficial de rastreabilidade. O livro físico, se mantido, é apenas contingência e não fonte de controle.
* **RN-04 (Trava de obrigatoriedade e rastreabilidade de fases):** O sistema impede o avanço do exame para a fase seguinte se a fase anterior não foi registrada com assinatura eletrônica. Não é permitido pular etapas (ex: ir para microscopia sem registro de processamento). Amostras com dados obrigatórios do AGHU faltantes ficam travadas na recepção com alerta automático.
* **RN-05 (Imutabilidade e trilha de auditoria inviolável):** Uma vez registrada e assinada eletronicamente uma fase no Livro Eletrônico, o registro torna-se imutável. Qualquer correção posterior não apaga o histórico, gera nova versão com justificativa, mantendo quem fez, quando fez e o que alterou. Histórico preservado para acreditação e auditoria.
* **RN-06 (Autenticação institucional e vínculo de autoria):** Todo acesso para receber, processar, laudar ou gerenciar exige login com conta institucional do HC-UFPE. O sistema vincula automaticamente matrícula (SIAPE) à ação, sem coleta de CPF ou dados pessoais sensíveis desnecessários, em conformidade com a LGPD.
* **RN-07 (Eliminação da planilha paralela como fonte oficial):** A planilha de controle interno atual deixa de ser fonte oficial. O sistema passa a ser a única fonte de verdade para acompanhamento de status, TAT e pendências. É vedada a manutenção de controles paralelos manuais após a implantação.

---

## 8. Painel de Gestão e Indicadores Estratégicos (KPIs)

O sistema deve disponibilizar painel gerencial hierárquico (cada chefia enxerga o seu escopo) com os seguintes indicadores de negócio:
1. **Rastreabilidade e Status em Tempo Real (Fim da cobrança por telefone/WhatsApp)** Mapa visual de onde cada exame está agora (Recepção, Macro, Processamento, Microtomia, Coloração, Microscopia, Laudo).Tempo de permanência em cada fase, com alerta de cor para exames parados há mais tempo que o SLA definido.Quem é o responsável atual pelo exame (nome e matrícula), extraído da última assinatura eletrônica no Livro Eletrônico.
2. **TAT - Tempo de Atendimento Total e por Fase (Principal indicador de qualidade)** TAT Total: da recepção no SAP até a liberação do laudo.TAT por fase: tempo médio em macroscopia, processamento, microtomia, microscopia.TAT por prioridade, tipo de material e solicitante, permitindo identificar gargalos específicos.
3. **Mapa de Pendências e Atrasos Operacionais**  Listagem imediata de exames com prazo de laudo vencido ou próximo do vencimento.Listagem de exames travados na recepção por dados incompletos vindos do AGHU (RN-04).Listagem de exames aguardando complementação ou segunda opinião.
4. **Produtividade e Carga de Trabalho (Substitui a planilha de controle)** Volume de exames recebidos, processados e laudados por período, por técnico e por patologista.Quantidade de blocos/cassetes/lâminas produzidos por técnico. Distribuição da carga entre as bancadas.
5. **Qualidade e Não Conformidades** Taxa de não conformidade de identificação, material insuficiente, dados do AGHU incompletos.Taxa de refação de blocos/lâminas por fase.Histórico de correções no Livro Eletrônico (RN-05), com motivo e autor.Regra de visualização: Técnico enxerga apenas seus exames e sua bancada. Patologista enxerga seus exames. Chefia do SAP enxerga tudo do serviço. Gestão superior enxerga indicadores consolidados, sem acesso a edição operacional.
---


## 9. Matriz de Pontos de Decisão (Gabinete / Gestão do Negócio)

> *Itens que dependem de confirmação dos gestores do hospital antes da conclusão:*

| # | Ponto a Decidir | Impacto no Processo | Quem deve decidir? | Status / Definição |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Fim do livro físico e validade jurídica da assinatura eletrônica** | Define se haverá eliminação da redundância (assinar no sistema + assinar no livro impresso) ou se a dupla assinatura será mantida. Tem impacto direto na redução da carga operacional da bancada e no tempo de atendimento. | Chefia do SAP + Gestão de Qualidade / Acreditação + Diretoria (ou Jurídico/Compliance) | 🟡 **Em definição**<br>_Proposta técnica:_ Substituição integral. O Livro de Protocolo Eletrônico passa a ser a única fonte oficial de rastreabilidade. |
| **2** | **Amostra com dados incompletos vindos do AGHU** (Trava vs. Preenchimento manual) | Define a regra de negócio (RN-04). Travar 100% força a correção da causa raiz na origem (AGHU). Permitir preenchimento manual complementar cria risco de inconsistência de dados e mantém a falha estrutural da ficha incompleta. | Chefia do SAP + Equipe de Regulação / Gestão do AGHU | 🟡 **Em definição**<br>_Proposta técnica:_ Trava imediata na recepção com emissão de alerta automático para o setor solicitante no AGHU. |
| **3** | **Destino da planilha de controle paralelo pós-go-live** | Define a regra de negócio (RN-07). Manter a planilha em paralelo gera duplicidade de fonte da verdade, perpetua o retrabalho e desestimula o uso do novo sistema. | Chefia do SAP | 🟡 **Em definição**<br>_Proposta técnica:_ Descontinuação imediata da planilha a partir do *go-live*. O Painel do Sistema assume como única fonte de controle. |
| **4** | **SLA por fase / Tempo Máximo de Permanência** (Macro, Processamento, Microscopia, Laudo) | Parametriza os indicadores de desempenho (KPIs). Sem a definição dos tempos aceitáveis por fase, os alertas visuais de atraso (Turnaround Time - TAT) no painel não funcionarão. | Chefia do SAP + Corpo Clínico | 🟡 **Em definição**<br>_Proposta técnica:_ Estabelecer prazos operacionais padrão (ex.: Macro: Xh, Processamento: Yh, Laudo: Zh) diferenciando exames de rotina vs. urgências para acionamento de alertas visuais (amarelo/vermelho). |
| **5** | **Rito de retificação de registro assinado eletronicamente** | Define o fluxo formal para correções no Livro Eletrônico após a assinatura formal. Garante a auditabilidade (RN-05) e cumpre os requisitos de rastreabilidade para Acreditação. | Chefia do SAP + Gestão da Qualidade | 🟡 **Em definição**<br>_Proposta técnica:_ Modificação via emissão de nova versão/adendo, exigência de justificativa obrigatória registrada em sistema e manutenção do histórico original (pista de auditoria/log). |
---
# 📘 GUIA METODOLÓGICO: COMO ESTE DOCUMENTO SE INTERLIGA AOS DEMAIS ARQUIVOS DO PROJETO

> **Apresentação Executiva para a Chefia:**  
> Esta seção explica a lógica de engenharia e governança adotada pelo SETISD para conectar as necessidades de negócio da ponta à construção do software.

### A Linha do Tempo: A Separação entre "Fase de Negócio" e "Fase de Engenharia"

Em qualquer projeto de software hospitalar existem dois mundos que precisam se comunicar com perfeição:
1. **O Mundo do Negócio (Chefias, Áreas Solicitantes, Governança, Direção):** Não devem ser expostos a termos técnicos de TI (bancos de dados, endpoints, JSON, status HTTP, docker, etc.). Eles precisam discutir *processos, dores reais, prazos, responsabilidades e regras*.
2. **O Mundo da Engenharia (Desenvolvedores e Testes):** Precisam de tabelas relacionais, tipos de dados estritos, rotas de API seguras e casos de uso testáveis.

Este documento (`00-validacao-negocio.md`) funciona como a **Ponte Oficial** entre esses dois mundos:

```text
               ┌────────────────────────────────────────────────────────┐
               │         00-VALIDAÇÃO E FLUXO DE NEGÓCIO (ESTE ARQUIVO)  │
FASE 1         │   Linguagem humana, fluxos e regras reais de negócio.  │
(Negócio)      │   Validado e assinado pelas Chefias e Direção do HC.   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 ▼ (Uma vez aprovado, a TI desdobra tecnicamente)     ▼
               ┌────────────────────────────────────────────────────────┐
FASE 2         │            ARTEFATOS DE ESPECIFICAÇÃO TÉCNICA           │
(Engenharia)   │   01-visao.md  →  02-requisitos.md  →  03-casos-uso.md │
               │   04-modelo-dados.md  →  05-interfaces  →  SPEC.md     │
               └────────────────────────────────────────────────────────┘
```

---

### Como cada seção deste documento alimenta a documentação técnica:

| Seção deste Documento de Negócio | O que ela entrega para a documentação técnica? | Arquivo de Destino |
| :--- | :--- | :--- |
| **Seção 2 (O Problema que Queremos Resolver)** | Define a motivação institucional, os riscos do modelo atual e a justificativa do projeto. | [01-visao.md](01-visao.md) *(Problema e Escopo)* |
| **Seção 3 (Como o Processo Funciona Hoje)** | Serve de base para mapear os processos manuais que serão substituídos e os dados legados. | [01-visao.md](01-visao.md) *(Cenário Atual)* |
| **Seção 4 (O Que a Nova Solução Deve Entregar)** | Define os objetivos do produto e os ganhos práticos que orientam a entrega de valor. | [01-visao.md](01-visao.md) *(Visão de Futuro)* |
| **Seção 5 (Como Será o Trabalho no Novo Sistema)** | Detalha as etapas práticas do usuário na tela, que viram os fluxos e cenários de uso do sistema. | [02-requisitos.md](02-requisitos.md) e [03-casos-uso.md](03-casos-uso.md) *(Casos de Uso e Fluxos)* |
| **Seção 6 (Quem Participa do Processo)** | Define os perfis de acesso, permissões de cada papel e o modelo de autorização local. | [02-requisitos.md](02-requisitos.md) e [03-casos-uso.md](03-casos-uso.md) *(Atores e RBAC)* |
| **Seção 7 (Regras de Negócio Inegociáveis)** | É convertida diretamente em requisitos funcionais estritos e validações de backend. | [02-requisitos.md](02-requisitos.md) *(Requisitos Funcionais - RFs)* |
| **Seção 8 (Painel de Gestão e Indicadores)** | Dá origem às consultas analíticas de acompanhamento, relatórios e telas gerenciais. | [05-interfaces.md](05-interfaces.md) *(Protótipos e Dashboards)* |
| **Seção 9 (Matriz de Pontos de Decisão)** | Orienta os parâmetros de configuração e regras que alimentam as tarefas de implementação. | [SPEC.md](SPEC.md) *(Definições e Tarefas)* |

---

### A Regra de Ouro do Processo no SETISD:

1. **Início do Projeto (Fase de Negócio):** O profissional de TI preenche este documento junto com os responsáveis pela área de negócio em reuniões de alinhamento, validando o problema real, os fluxos práticos e as decisões pendentes.
2. **Desenvolvimento (Fase de Engenharia):** Com este documento aprovado pelas partes envolvidas, a equipe de desenvolvimento tem total clareza técnica para elaborar os artefatos de `01` a `06` e programar a solução com segurança e sem retrabalho.

**Resultado:** O cliente hospitalar participa ativamente sem ser sobrecarregado com termos técnicos, e a equipe de TI constrói exatamente o que o hospital precisa.
