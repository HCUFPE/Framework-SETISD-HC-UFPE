# Sistema de Agendamento de Exames (SAE-HC) — Documento de Validação e Especificação de Negócio

> **Padrão Oficial SETISD / HC-UFPE (HU Brasil) — Fase 0 (Alinhamento de Negócio)**  
> **Público-alvo:** Profissionais das áreas envolvidas e Equipe de TI.  
> **Objetivo:** Descrever o processo de trabalho em **linguagem pura de negócio** (sem jargões técnicos de programação ou banco de dados) para validação, alinhamento de expectativas e tomada de decisão antes de qualquer codificação.

---

## 1. Identificação do Projeto e Contexto Institucional

| Campo | Descrição |
| :--- | :--- |
| **Nome do Sistema** | Sistema de Agendamento de Exames |
| **Área Solicitante / Cliente** | Central de Marcação de Exames |
| **Instância Superior Competente** | SETISD |
| **Líder Técnico (SETISD)** | Tiago Ferrão |
| **Objetivo Estratégico HU Brasil** | Garantir eficiência, rastreabilidade e padronização do processo de agendamento de exames no HC-UFPE |

---

## 2. O Problema que Queremos Resolver

> **Objetivo:** Dizer com clareza qual é o problema real de trabalho. Sem rodeios: o que hoje está quebrado, ineficiente ou gerando risco para o hospital?

* **A Dor Central:**  
  O processo de agendamento de exames não garante a prioridade de atendimento dos pacientes e as informações coletadas dos pacientes possuem erros demasiados.

* **Por que isso não pode continuar (Impactos Reais):**
  - **Sobrecarga de Trabalho:** As chefias e equipes perdem horas redigitando dados e conferindo manualmente tarefas que poderiam ser automáticas.
  - **Falta de Visibilidade:** A gestão não sabe em tempo real quem já entregou, quem está com pendências e onde estão os gargalos.
  - **Risco Institucional e Legal:** Falta de histórico confiável para responder a auditorias, questionamentos de órgãos de controle ou conferências internas.

---

## 3. Como o Processo Funciona Hoje (A Rotina Atual)

> **Objetivo:** Mapear a realidade crua de como as equipes se viram no dia a dia para realizar essa tarefa hoje.

* **Meios Utilizados Hoje:**
  Recebimento das solicitações de marcação de exame: Forms da Microsoft
  Armazenamento das solicitações de marcação de exame: Planilha Excel
  Marcação definitiva dos Exames: Sistema AGHUX
  Comunicação da equipe: Whatsapp

* **A Rotina Prática de Trabalho:**
  Lançamento do formulário para marcação de exames -> Exportação das respostas para planilha do Excel -> 
  Seleção dos pacientes manualmente para marcação -> Verificação dos dados preenchidos pelo paciente com os dados do AGHU -> 
  Contato com paciente para verificar disponibilidade -> Marcação do exame no sistema AGHU.

---

## 4. O Que a Nova Solução Deve Entregar (Resultado Esperado)

> **Objetivo:** Definir com clareza o que a solução digital deve trazer para eliminar a dor do processo atual.

* **A Proposta de Valor:** Integrar o processo de validação dos dados preenchidos automaticamente e priorizar os pacientes seguindo critérios predefinidos, facilitando a inclusão no backbone.
* **Ganhos Práticos Imediatos:**
  - Alerta automático de erros ou inconsistências no lançamento do formulário.
  - Assinatura eletrônica segura com registro de quem fez, quando aprovou e o que alterou.
  - Painel de controle em tempo real para a gestão acompanhar entregas e pendências.
  - Histórico guardado, inviolável e fácil de consultar a qualquer momento.
  - Redução no tempo necessário para validar os dados antes do lançamento.

---

## 5. Como Será o Trabalho no Novo Sistema (O Novo Fluxo)

> **Objetivo:** Explicar em linguagem direta como o usuário vai interagir com o sistema, resolvendo a dor do processo manual de ponta a ponta.

1. **Recebimento e Validação Automática da Solicitação**:
O paciente ou solicitante preenche um formulário externo ao sistema. O sistema recebe os dados preenchidos, processa as informações e realiza a checagem, gerando alertas e sinalizando onde estão os erros, divergências ou campos incorretos para a equipe responsável. Havendo inconsistência, a solicitação fica como **Pendente de correção**; sem inconsistência, segue como **Solicitação recebida**.
2. **Ordenação Automática da Fila por Prioridade**:
A solicitação é inserida em uma fila centralizada e classificada automaticamente com base nos critérios de prioridade predefinidos pelo hospital (como urgência clínica ou idade), garantindo que os casos mais graves fiquem no topo do atendimento. A fila mostra, por padrão, `#`, `Prioridade`, `Paciente / Prontuário`, `Unidade solicitante`, `Exame(s)`, `Status` e `Tempo na fila`; a equipe pode mostrar ou ocultar colunas e filtrar por unidade solicitante.
3. **Validação dos Dados Cadastrados pelo Operador**:
O profissional da Central de Marcação acessa a fila já priorizada. Ao abrir uma solicitação, vê **somente os dados que já estão cadastrados no AGHUX** — nome, prontuário, telefone, cidade/UF, unidade/solicitante e exames. Não há mais uma tela de conferência campo a campo: divergências apontadas aparecem em uma seção separada, apenas enquanto estiverem pendentes. O operador corrige/justifica, valida e registra sua assinatura eletrônica.
4. **Contato com o Paciente**:
Com os dados validados, a solicitação passa a **Aguardando contato**. O operador registra o retorno: com aceite, passa a **Aguardando confirmação**; com recusa ou sem resposta, passa a **Aguardando reagendamento**. O registro evita contatos duplicados.
5. **Efetuar Marcação e Confirmação da Proposta**:
O botão **Efetuar marcação** leva ao calendário com a solicitação e a busca já preenchidas. O exame específico da solicitação controla quais horários podem ser oferecidos; o operador pode escolher diretamente uma vaga ou gerar a simulação dos próximos 30 dias. A simulação cria propostas que reservam a vaga, mas só viram agendamento ativo quando o operador confirma em um clique. Se o paciente não confirmar, a proposta é cancelada com justificativa e a solicitação volta para **Aguardando reagendamento**. A confirmação efetiva no AGHUX segue como etapa futura; nesta versão a reserva e a confirmação são operacionais e ficam apenas na agenda local do SAE-HC. Os estados da solicitação são: **Solicitação recebida**, **Pendente de correção**, **Aguardando contato**, **Aguardando confirmação**, **Aguardando reagendamento**, **Agendado** e **Cancelado**.
5.1. **Remarcação e Distância**:
Quando o paciente pede outro horário, a chefia ou o operador consulta o histórico de agendamentos daquele paciente no calendário, escolhe uma nova vaga e informa o motivo. A vaga anterior volta a ficar disponível imediatamente. Se o endereço tiver sido informado no formulário, o sistema calcula a distância até o hospital e a usa apenas como desempate entre horários equivalentes — nunca para superar um caso clinicamente mais prioritário.
6. **Acompanhamento e Gestão em Tempo Real**:
A gestão acessa um painel de controle central para acompanhar os indicadores operacionais em tempo real: volume de solicitações pendentes, tempo médio de validação, exames agendados e gargalos da fila, dispensando o tempo gasto na consolidação de relatórios e conferências manuais.

---

## 6. Quem Participa do Processo (Atores: Como Faz Hoje vs. Como Fará no Sistema)

| Ator / Perfil no Hospital | O que faz HOJE (Rotina Manual) | O que passará a fazer no NOVO SISTEMA | O que NÃO poderá fazer |
| --- | --- | --- | --- |
| **Área Gestora do Processo** *(Central de Marcação)* | Exporta dados do Microsoft Forms para planilhas Excel, tenta organizar prioridades manualmente e cobra pendências da equipe por WhatsApp. | Cadastra e atualiza as regras de priorização da fila, monitora o fluxo global e gerencia exceções do processo em tempo real. | Não poderá alterar a ordem da fila sem justificativa formal nem realizar agendamentos fora do fluxo auditável. |
| **Profissional do Setor / Executante** *(Operador da Central de Marcação)* | Seleciona pacientes manualmente na planilha Excel, compara dados com o AGHUX campo a campo, contata paciente por WhatsApp e agenda no AGHUX. | Trabalha na fila priorizada, analisa os alertas de erro gerados pós-envio e divergências com o AGHUX, corrige/valida os dados com assinatura eletrônica e confirma a marcação. | Não poderá alterar manualmente a prioridade dos pacientes, ignorar os alertas de inconsistência ou editar dados sem registro de sua assinatura eletrônica. |
| **Chefia Imediata / Responsável pelo Setor** *(Chefia da Central de Marcação)* | Revisa planilhas dispersas, trata erros e divergências reportados informalmente e tenta gerenciar a distribuição do trabalho sem visão do processo em tempo real. | Acompanha a produtividade da equipe e o andamento da fila em tela única, gerencia tratativas de cadastros divergentes e aprova solicitações excepcionais. | Não poderá aprovar agendamentos que permaneçam com erros ou pendências cadastrais em aberto. |
| **Gestão / Coordenação Superior** *(Gerência de Atenção à Saúde / Superintendência)* | Depende de relatórios demorados consolidados manualmente em planilhas para acompanhar gargalos, volume de exames e tempo de espera. | Acompanha o painel executivo em tempo real com indicadores de volume, taxa de erro pós-envio, tempo médio de validação e gargalos operacionais. | Acesso estritamente para visualização gerencial e acompanhamento estratégico (não realiza edições ou agendamentos operacionais). |
| **Público / Usuário do Serviço** *(Pacientes / Solicitantes do Exame)* | Preenche o Microsoft Forms, aguarda contato passivamente e precisa ligar ou ir ao hospital para obter informações. | Preenche o formulário externo, é notificado pelo meio de contato registrado em caso de inconsistência nos dados e é contatado pelo operador para confirmar data e horário do exame. | Não terá acesso ao sistema, a informações de terceiros nem a opções de alteração na fila de prioridade. |

---

## 7. Regras de Negócio Inegociáveis (RNs)

* **RN-01 (Identificação Única do Paciente):** Cada solicitação é vinculada ao paciente pelo CNS ou CPF, validado após o recebimento dos dados. Os dados do paciente são usados apenas para o agendamento e nunca são exibidos a terceiros.
* **RN-02 (Priorização Automática e Equitativa):** Toda solicitação entra em uma fila única e é classificada automaticamente pelos critérios de prioridade definidos pelo hospital. Nenhum operador pode alterar a prioridade manualmente.
* **RN-03 (Alteração de Fila Somente com Justificativa):** A ordem da fila só pode ser modificada pela Área Gestora, com justificativa formal registrada. Agendamentos fora do fluxo auditável são proibidos.
* **RN-04 (Validação Obrigatória contra o AGHUX):** Antes de qualquer agendamento, os dados informados são comparados com o cadastro do AGHUX. A tela do paciente mostra apenas os dados já cadastrados; o operador não pode ignorar divergências pendentes: cada uma deve ser corrigida ou justificada.
* **RN-05 (Prevenção de Duplicidade e Choques):** O sistema bloqueia solicitações duplicadas do mesmo paciente para o mesmo exame e impede dois agendamentos conflitantes no mesmo horário para o mesmo paciente.
* **RN-06 (Autenticação Institucional e Assinatura Eletrônica):** O acesso interno exige login institucional com a conta de rede do hospital. Toda ação (correção, validação, agendamento) é vinculada à assinatura eletrônica do operador, com data e hora.
* **RN-07 (Marcação antes da Confirmação do Paciente):** Para garantir a vaga, a solicitação recebida é marcada na agenda local antes do contato com o paciente, sem exigir aceite prévio; a solicitação passa a **Aguardando contato**. Se o paciente não confirmar em 24 horas, o agendamento é cancelado e a vaga é liberada (**Não confirmado**). Os demais caminhos de agendamento (solicitações já contatadas, em confirmação ou em reagendamento) continuam exigindo aceite registrado. O retorno do contato (aceite, recusa ou sem resposta) é registrado no sistema para evitar contatos duplicados; a confirmação efetiva no AGHUX permanece como etapa futura e não é prometida por esta versão.
* **RN-08 (Preservação e Imutabilidade do Histórico):** Nenhum registro é apagado ou sobrescrito. Todo o histórico (quem solicitou, validou, alterou e agendou, e quando) forma uma trilha auditável inviolável.
* **RN-09 (Ocupação Real de Vagas):** Nenhum horário é oferecido acima da capacidade cadastrada pela Área Gestora. Agendamentos ativos e propostas pendentes de confirmação ocupam vaga e bloqueiam choque do mesmo paciente, inclusive quando pertencem a outros pacientes.
* **RN-10 (Privacidade do Endereço):** O endereço informado no formulário é usado somente para calcular a distância até o hospital. Não pode aparecer em telas de terceiros, relatórios, histórico de auditoria ou logs; se o cálculo falhar, o sistema informa que a distância está indisponível em vez de estimar um valor.

---

## 8. Painel de Gestão e Indicadores Estratégicos (KPIs)

O sistema deve disponibilizar painel gerencial em tempo real, com os seguintes indicadores de negócio:
1. **Volume de Solicitações Pendentes:** Quantidade de solicitações aguardando validação, contato ou agendamento, separadas por tipo de exame e faixa de prioridade.
2. **Tempo Médio de Validação:** Tempo entre o envio do formulário pelo paciente e a conclusão da validação pelo operador.
3. **Exames Agendados:** Quantidade de exames efetivamente marcados no período, com o tempo total entre solicitação e agendamento.
4. **Gargalos da Fila:** Identificação das etapas e dos tipos de exame onde as solicitações ficam paradas por mais tempo.
5. **Taxa de Erro Pós-Envio:** Percentual de formulários com inconsistências ou divergências em relação ao AGHUX, para orientar melhorias no preenchimento.

---

## 9. Matriz de Pontos de Decisão (Gabinete / Gestão do Negócio)

> *Itens que dependem de confirmação dos gestores do hospital antes da conclusão:*

| # | Ponto a Decidir | Impacto no Processo | Quem deve decidir? | Status / Definição |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Critérios de Priorização:** Quais critérios (urgência clínica, idade, tempo de espera, outros) e qual o peso de cada um? | Define a ordem automática da fila e a equidade no atendimento. | Gestão da Área / Direção Clínica | 🟡 Em definição |
| **2** | **Política de Preenchimento de Vagas:** Como as vagas disponíveis serão distribuídas entre as solicitações da fila? | Evita vagas ociosas e garante que os casos prioritários sejam atendidos primeiro. | Gestão da Área | 🟢 **Definido (v0.5.0):** a Área Gestora e a Chefia da Central cadastram/ajustam vagas por unidade/exame/data/horário; a sugestão e a simulação respeitam a capacidade, incluindo as reservas geradas na própria execução, ordenando por prioridade, compatibilidade, tempo de espera e distância como desempate. O exame da solicitação é filtro duro e as propostas da simulação exigem confirmação do operador. |
| **3** | **Prazo Máximo de Validação:** Qual o tempo-limite para o operador validar uma solicitação? | Define os alertas de atraso e a meta do indicador de tempo médio de validação. | Gestão Central / Chefias | 🟡 Em definição |
| **4** | **Regra de Contato com o Paciente:** Qual o canal oficial, quantas tentativas e qual o prazo de resposta antes de devolver a solicitação à fila? | Evita contatos duplicados e vagas bloqueadas por pacientes sem retorno. | Gestão da Área | 🟡 Em definição |
| **5** | **Alteração Excepcional de Prioridade:** Quais situações permitem à Área Gestora mudar a ordem da fila e qual a justificativa mínima? | Mantém a equidade sem impedir o tratamento de exceções reais. | Gestão Central | 🟡 Em definição |
| **6** | **Cancelamento e Reagendamento:** Qual o rito formal para desmarcar ou remarcar um exame já efetivado? | Define o registro no histórico e o retorno da vaga à fila. | Gestão Central | 🟢 **Definido (v0.4.0):** toda remarcação ou cancelamento exige justificativa, devolve a vaga anterior na mesma operação e registra quem fez, quando e o motivo; o histórico de todos os agendamentos do paciente fica consultável no calendário. Proposta cancelada ou não confirmada retorna para **Aguardando reagendamento**. |
| **7** | **Distância até o hospital:** Como obter a distância a partir do endereço informado no formulário? | Permite encaixes mais próximos do paciente sem usar dados sensíveis em telas ou relatórios. | Gestão da Área / TI | 🟢 **Definido (v0.3.0):** geocoding com OpenStreetMap (Nominatim) e rota com OSRM, sem chave paga, com cache e timeout; falha no cálculo é sinalizada como indisponível, nunca estimada. |
| **8** | **Ferramenta de calendário:** qual visualização usar para vagas e remarcação? | Define a usabilidade da Central de Marcação e o custo de manutenção do frontend. | Gestão da Área / TI | 🟢 **Definido (v0.4.0):** FullCalendar Vue 3 nas visões mês e semana, com cores por ocupação; arrastar um agendamento abre confirmação com justificativa antes de salvar. O clique no dia abre os horários, sem listar solicitações antes da busca. |
| **9** | **Exibição da fila e da tela do paciente:** quais informações a equipe de marcação vê primeiro? | Reduz digitação e evita que a equipe trabalhe com dados inventados ou divergências já tratadas. | Central de Marcação / Gestão da Área | 🟢 **Definido (v0.5.0):** colunas padrão e menu para mostrar/ocultar colunas, filtro por unidade solicitante; a tela do paciente mostra apenas dados do AGHUX e a seção de divergências aparece somente com pendências. As propostas da simulação também são exibidas como fila ordenada, com prioridade, tempo na fila e horário proposto. |
| **10** | **Quem ajusta a disponibilidade dos exames:** a Chefia da Central pode alterar vagas sem depender da Área Gestora/TI? | Agiliza a rotina diária sem enfraquecer a trilha de auditoria nem o RBAC. | Gestão Central / TI | 🟢 **Definido (v0.7.0):** `CHEFIA` cria, edita e remove vagas (por soft delete, quando vazias) e copia configurações de uma semana para outra no backend e na tela; cada alteração gera auditoria `CONFIGURACAO`. `COORDENACAO` continua somente leitura. |
| **11** | **Momento da marcação:** a vaga é marcada antes do contato com o paciente ou só depois do aceite? | Define a ordem do fluxo e o que acontece com a vaga quando o paciente não confirma. | Gestão da Área | 🟢 **Definido:** confirmado com o HC que a marcação é feita antes da confirmação do paciente, para garantir a vaga, e desfeita se ele não confirmar (RN-07). |

---
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
