# Portal de Agendamento e Triagem de Exames — Documento de Validação e Especificação de Negócio

> **Padrão Oficial SETISD / HC-UFPE (HU Brasil) — Fase 0 (Alinhamento de Negócio)**  
> **Público-alvo:** Profissionais das áreas envolvidas e Equipe de TI.  
> **Objetivo:** Descrever o processo de trabalho em **linguagem pura de negócio** (sem jargões técnicos de programação ou banco de dados) para validação, alinhamento de expectativas e tomada de decisão antes de qualquer codificação.

---

## 1. Identificação do Projeto e Contexto Institucional

| Campo                              | Descrição                                                                                                                                                                                  |
| :--------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nome do Sistema**                | Sistema Interno de Gestão de Fila e Triagem de Exames (Portal Interno HC-UFPE)                                                                                                             |
| **Área Solicitante / Cliente**     | Central de Marcação de Exames / HC-UFPE                                                                                                                                                    |
| **Instância Superior Competente**  | Superintendência do HC-UFPE / SETISD                                                                                                                                                       |
| **Líder Técnico (SETISD)**         | Tiago Ferrão                                                                                                                                                                               |
| **Objetivo Estratégico HU Brasil** | Modernizar o fluxo de atendimento ao paciente, mitigando filas, otimizando o preenchimento de vagas ociosas e garantindo a rastreabilidade e priorização clínica no agendamento de exames. |

---

## 2. O Problema que Queremos Resolver

> **Objetivo:** Dizer com clareza qual é o problema real de trabalho. Sem rodeios: o que hoje está quebrado, ineficiente ou gerando risco para o hospital?

- **A Dor Central:**  
  O recebimento de pedidos de exames ocorre via Google Forms sem validação prévia, gerando um volume massivo de dados incorretos que a equipe precisa triar visualmente em planilhas, resultando em lentidão, filas subotimizadas e dependência da memória humana para priorização clínica e logística.

- **Por que isso não pode continuar (Impactos Reais):**
  - **Sobrecarga de Trabalho:** A equipe perde horas tentando localizar solicitações no AGHU porque os pacientes frequentemente digitam informações erradas no formulário (como o número de celular no lugar do número do exame).
  - **Falta de Visibilidade e Subotimização:** A gestão não consegue cruzar dados rapidamente. Vagas urgentes (ex: desistências para o dia seguinte) acabam sendo perdidas ou alocadas para pacientes que moram muito longe (ex: no município de Pesqueira) e não têm tempo hábil de deslocamento.
  - **Risco de Falha Humana na Prioridade:** Regras clínicas complexas (como a prioridade máxima para pacientes da Nefrologia em hemodiálise) dependem inteiramente da atenção e do conhecimento prévio do atendente ao olhar a planilha.

---

## 3. Como o Processo Funciona Hoje (A Rotina Atual)

> **Objetivo:** Mapear a realidade crua de como as equipes se viram no dia a dia para realizar essa tarefa hoje.

- **Meios Utilizados Hoje:**  
  Google Forms (para os pacientes enviarem pedidos), Planilhas do Google Drive (para controle da fila) e o sistema legado AGHU (para a efetivação final do agendamento).

- **A Rotina Prática de Trabalho:**
  1. **Início:** O paciente sai da consulta com o ticket de solicitação impresso pelo AGHU e acessa um link do Google Forms para pedir a marcação.
  2. **Preenchimento:** O paciente digita seus dados e o "número da solicitação",sujeito a errar, e anexa uma foto do pedido.
  3. **Conferência (O Gargalo):** A equipe da Central de Marcação abre a planilha gerada pelo Forms, copia o número digitado pelo paciente e cola na tela de agendamento do AGHU. Muitas vezes, o sistema retorna "Solicitação não encontrada".
  4. **Entrega e Arquivo:** Quando a solicitação está correta e a vaga é encontrada, a atendente agenda no AGHU, volta para a planilha do Drive e altera a cor da linha correspondente para "verde" (indicando que foi resolvido). Não há histórico automatizado ou rastreabilidade de fila.

---

## 4. O Que a Nova Solução Deve Entregar (Resultado Esperado)

> **Objetivo:** Definir com clareza o que a solução digital deve trazer para eliminar a dor do processo atual.

- **A Proposta de Valor:** Substituir as planilhas manuais e controles paralelos por uma **aplicação web estritamente interna** da Central de Marcação que lê diretamente as solicitações registradas no AGHU, apresentando para a equipe uma fila de espera limpa, validada e organizada automaticamente por prioridade clínica configurável, com filtros operacionais e alertas de conflito.
- **Ganhos Práticos Imediatos:**
  - Eliminação da dependência de planilhas coloridas ("pintar linha de verde") e redução do retrabalho com números de solicitação inválidos ou duplicados.
  - Organização automática da fila baseada em regras clínicas **configuráveis/editáveis** pela gestão (clínica solicitante, grupo prioritário, data de retorno).
  - Filtro rápido por município/região para aproveitamento ágil de vagas urgentes de última hora (amanhã ou depois de amanhã), sem penalizar a prioridade clínica de pacientes do interior.
  - Alertas automáticos para exames incompatíveis (preparo ou mesmo dia), janelas de retorno e duplicidades.
  - Painel de status operacional (Aguardando, Agendado no AGHU, Contatado/Confirmado, Sem Contato — 24h, Cancelado/Remarcação) com histórico auditável.

---

## 5. Como Será o Trabalho no Novo Sistema (O Novo Fluxo)

> **Objetivo:** Explicar em linguagem direta como o usuário vai interagir com o sistema, resolvendo a dor do processo manual de ponta a ponta.

- **1. Importação da Planilha do Forms + Higienização contra o AGHU (uso interno):** O paciente continua enviando seu pedido pelo Google Forms oficial (por restrição de segurança de exposição externa da rede hospitalar). A equipe importa/lê essa planilha no nosso sistema interno (sem alterar ou desconfigurar o arquivo original), que cruza automaticamente cada pedido com a base oficial de leitura do AGHU — validando o número da solicitação (com busca ativa por prontuário quando houver erro), checando se o exame escolhido no Forms corresponde ao pedido médico real e identificando duplicidades ou exames já realizados.
- **2. Priorização Automática e Configurável:** A fila higienizada já aparece ranqueada segundo pesos e critérios clínicos editáveis no próprio sistema — priorizando Oncologia, Transplante, Nefrologia/Hemodiálise e grupos vulneráveis (gestantes, crianças/Pediatria e idosos) frente à rotina ambulatorial, considerando a afinidade entre a clínica solicitante e o exame e a data de retorno.
- **3. Filtro Inteligente para Vagas de Última Hora:** Quando abre uma vaga urgente para o dia seguinte ou daqui a dois dias, a equipe aciona o **filtro de município/região** (Capital, Região Metropolitana ou Interior) para encontrar rapidamente pacientes com tempo hábil de chegada, mantendo intacta a ordem de prioridade clínica para vagas regulares.
- **4. Alertas de Conflito, Preparo e Data de Retorno:** O sistema alerta automaticamente sobre exames incompatíveis (ex: colonoscopia × sangue; ressonância × oftalmologia), prazos de preparo/antecedência mínima e janelas vinculadas à data de retorno (ex: espirometria até 10 dias antes; INR até 72h).
- **5. Confirmação em 24h ANTES da Marcação no AGHU (Fluxo Ideal Validado em 06/11):** A equipe entra em contato com o paciente via WhatsApp e registra o início do prazo de **24 horas** no sistema. Se o paciente confirmar disponibilidade, a equipe efetiva a marcação oficial no **AGHU**, envia as orientações de preparo e marca como `Confirmado / Agendado no AGHU`. Caso não responda em 24h, a vaga é liberada para o próximo da fila com rastreabilidade completa.

---

## 6. Quem Participa do Processo (Atores: Como Faz Hoje vs. Como Fará no Sistema)

| Ator / Perfil no Hospital                                     | O que faz HOJE (Rotina Manual)                                                                                                  | O que passará a fazer no NOVO SISTEMA                                                                                                           | O que NÃO poderá fazer                                                                                                            |
| :------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| **Central de Marcação** _(Ex: Maíra, Tatyanne/Tati, Larissa)_ | Alterna entre planilhas, WhatsApp e AGHU. Copia números, testa um por um, aplica prioridades de memória e pinta linhas de verde. | Acessa painel interno único com a fila validada do AGHU, priorizada e filtrável (inclusive por município em urgências). Registra status/contato. | Não agenda diretamente no AGHU por dentro do sistema satélite (limitação institucional da sede em Brasília) e não altera o ticket. |
| **Gestão / Coordenação Superior**                             | Não tem visão consolidada de gargalos, tamanho real da fila, tempo de espera, faltas ou remarcações.                            | Acompanha painel de indicadores (KPIs) e configura/edita pesos de prioridade e regras de preparo/incompatibilidade dos exames.                  | Não altera registros sem trilha de auditoria nem exclui dados fisicamente.                                                        |
| **Paciente / Usuário** _(Fora do sistema)_                    | Preenche Google Forms manualmente, gerando erros de digitação e solicitações duplicadas.                                        | **Não acessa este sistema diretamente.** A interação com o paciente será atendida por aplicativo específico em contratação pela sede da EBSERH.  | Não possui login nem acesso direto ao sistema interno da Central.                                                                 |

---

## 7. Regras de Negócio Inegociáveis (RNs)

- **RN-01 (Cruzamento `Forms × AGHU` e Identificação por Prontuário/Solicitação):** O sistema lê a planilha originada pelo Google Forms (sem editá-la) e cruza cada entrada com a base somente-leitura do AGHU utilizando **número da solicitação** e **prontuário** (sem exigir CPF obrigatório; prevendo busca ativa por prontuário em caso de erro de digitação). Sinaliza automaticamente solicitações inexistentes, divergência entre o exame escolhido no Forms e o pedido médico no AGHU, duplicidades (inclusive de múltiplos médicos) e exames já realizados.
- **RN-02 (Soberania do AGHU e Integridade do Ticket):** Como a política da sede (EBSERH/Brasília) bloqueia qualquer escrita externa no AGHU, a efetivação final do agendamento continua sendo feita pela equipe na tela do AGHU, e o ticket impresso não pode ser modificado. O sistema atua como aplicação satélite interna de apoio e gestão.
- **RN-03 (Fila de Prioridade Clínica Dinâmica e Configurável):** A ordenação da fila não é apenas cronológica (ordem de chegada). O sistema aplica uma hierarquia clínica **configurável e editável pela gestão** (sem alterar código), partindo da ordem preliminar: **Oncologia → Transplante → Nefrologia/Hemodiálise → Vulneráveis (gestantes, crianças/Pediatria, idosos) → rotina ambulatorial**, considerando a afinidade entre a clínica solicitante e o exame e a data de retorno.
- **RN-04 (Filtro Geográfico Operacional para Urgências — Não Prioridade):** O município/endereço do paciente **não** altera sua prioridade clínica. Ele funciona como um **filtro operacional** acionado pela equipe quando surgem vagas de última hora (amanhã ou depois de amanhã), evitando desperdício de vagas e respeitando a logística do TFD.
- **RN-05 (Alertas Configuráveis de Conflito, Preparo e Janela de Retorno):** O sistema deve manter um cadastro editável por exame para alertar sobre combinações inviáveis (mesmo dia ou interferência de preparo, como colonoscopia × exame de sangue e ressonância × oftalmologia), antecedência mínima de preparo, particularidades clínicas (ex: diabéticos nos primeiros horários para exames em jejum) e janelas vinculadas ao retorno (ex: espirometria até 10 dias antes; INR até 72h).
- **RN-06 (Confirmação em 24h Antes da Marcação e Escopo Interno):** Conforme alinhamento de 06/11, o fluxo ideal monitora o prazo de **24 horas para confirmação da disponibilidade do paciente antes de efetivar a marcação no AGHU** (liberando a vaga em caso de ausência de resposta). O sistema não substitui o Google Forms, não possui portal externo nem envia WhatsApp/SMS automaticamente. **Fora de escopo (alinhado em 06/11):** atendimentos presenciais diretos na Central, fluxos de remarcação/faltas e exceções de códigos de solicitação em lote no AGHU.

---

## 8. Painel de Gestão e Indicadores Estratégicos (KPIs)

O sistema deve disponibilizar um painel gerencial em tempo real com os seguintes indicadores de negócio:

1. **Tempo Médio de Espera e de Resposta:** Acompanhamento da fila por tipo de exame e especialidade (solicitação → confirmação → realização).
2. **Ocupação de Vagas e Aproveitamento TFD:** Relação entre exames realizados e vagas ofertadas, incluindo visibilidade do uso das vagas de Tratamento Fora de Domicílio (TFD).
3. **Absenteísmo e Remarcações por Indisponibilidade:** Percentual de faltas/cancelamentos tardios e volume de remarcações geradas por manutenção de equipamentos ou ausência de profissionais.
4. **Qualidade e Duplicidade de Solicitações:** Controle de solicitações redundantes, inconsistentes ou canceladas por ausência de contato em 24h.

---

## 9. Matriz de Pontos de Decisão (Gabinete / Gestão do Negócio)

> _Registro consolidado das decisões fechadas em reunião com SETISD/Central e pendências remanescentes:_

|   #   | Ponto a Decidir                                                                                                                                                     | Decisão / Encaminhamento                                                                                                                                                                                           | Responsável                          | Status / Definição           |
| :---: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------- | :--------------------------- |
| **1** | **Pesos de Prioridade Clínica:** Ordem oficial e pesos numéricos da fila.                                                                                           | **Configurável no sistema** (exigência do Tiago Ferrão). Adotada a hierarquia preliminar validada com Tatyanne/Maíra (**Oncologia → Transplante → Nefrologia/Hemodiálise → Vulneráveis → Rotina**) como padrão inicial editável. | Gestão Médica / Central / SETISD     | 🟢 Definido (Editável)       |
| **2** | **Raio de Deslocamento:** Critério geográfico para vagas urgentes ("amanhã cedo").                                                                                  | **Filtro operacional, não trava rígida nem prioridade** (esclarecimento de Tatyanne). A equipe filtrará por município/região (Capital, RMR, Interior) em vagas de última hora, respeitando a rotina do TFD.        | Central de Marcação (Tatyanne)       | 🟢 Definido                  |
| **3** | **Integração de Notificações (WhatsApp/SMS) e Portal do Paciente:** Disparo automático ou interação direta com o paciente.                                          | **Fora de escopo** (decisão do Tiago Ferrão). O sistema é **estritamente interno**; a interação com o paciente será feita por aplicativo em contratação pela sede. Haverá apenas registro interno de status de contato (24h). | TI (SETISD — Tiago Ferrão)           | 🟢 Definido (Fora de escopo) |
| **4** | **Tabela Inicial de Regras por Exame:** Pares incompatíveis, intervalos de preparo, janelas de retorno (além de espirometria 10d e INR 72h) e regra de mamografia (+40 anos). | Aguardando disponibilização da lista inicial pela Central (Tati/Camila/Tiago no Drive) para popular os cadastros configuráveis do sistema.                                                                        | Central de Marcação / Processos      | 🟡 Em definição              |
| **5** | **Identificação de Hemodiálise no AGHU e Controle de Grades Internas:** Flag de hemodiálise no SQL do Drive e escopo de cadastro interno de grades/vagas/remarcação. | Validar no CSV/SQL oficial do Drive se já existe distinção entre Hemodiálise e Nefrologia ambulatorial (ou se será marcação manual no sistema satélite) e confirmar se o sistema controlará grades/vagas locais.  | SETISD (Tiago) / Central (Maíra)     | 🟡 Em definição              |

---

---

# 📘 GUIA METODOLÓGICO: COMO ESTE DOCUMENTO SE INTERLIGA AOS DEMAIS ARQUIVOS DO PROJETO

> **Apresentação Executiva para a Chefia:**  
> Esta seção explica a lógica de engenharia e governança adotada pelo SETISD para conectar as necessidades de negócio da ponta à construção do software.

### A Linha do Tempo: A Separação entre "Fase de Negócio" e "Fase de Engenharia"

Em qualquer projeto de software hospitalar existem dois mundos que precisam se comunicar com perfeição:

1. **O Mundo do Negócio (Chefias, Áreas Solicitantes, Governança, Direção):** Não devem ser expostos a termos técnicos de TI (bancos de dados, endpoints, JSON, status HTTP, docker, etc.). Eles precisam discutir _processos, dores reais, prazos, responsabilidades e regras_.
2. **O Mundo da Engenharia (Desenvolvedores e Testes):** Precisam de tabelas relacionais, tipos de dados estritos, rotas de API seguras e casos de uso testáveis.

Este documento (`00-validacao-negocio.md`) funciona como a **Ponte Oficial** entre esses dois mundos:

```text
               ┌────────────────────────────────────────────────────────┐
               │         00-VALIDAÇÃO E FLUXO DE NEGÓCIO (ESTE ARQUIVO) │
FASE 1         │   Linguagem humana, fluxos e regras reais de negócio.  │
(Negócio)      │   Validado e assinado pelas Chefias e Direção do HC.   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 ▼ (Uma vez aprovado, a TI desdobra tecnicamente)    ▼
               ┌────────────────────────────────────────────────────────┐
FASE 2         │            ARTEFATOS DE ESPECIFICAÇÃO TÉCNICA          │
(Engenharia)   │   01-visao.md  →  02-requisitos.md  →  03-casos-uso.md │
               │   04-modelo-dados.md  →  05-interfaces  →  SPEC.md     │
               └────────────────────────────────────────────────────────┘
```
