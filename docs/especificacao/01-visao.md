# Documento de Visão

## 1. Problema e Oportunidade

- **O Problema**: O recebimento e controle de marcação de exames ambulatoriais ocorre hoje por meio de Google Forms, planilhas manuais no Google Drive e comunicação informal via WhatsApp, sem integração de leitura com o sistema hospitalar (AGHU). Isso gera grande volume de dados incorretos, pedidos duplicados e obriga a equipe a triar e priorizar manualmente toda a fila.
- **Impacto**: A equipe da Central de Marcação sofre sobrecarga operacional pesquisando solicitações inválidas no AGHU e mantendo controles visuais manuais ("pintar linhas de verde"). Além disso, há subotimização da fila, risco de falha humana na aplicação de prioridades clínicas complexas, dificuldade para aproveitar vagas urgentes de última hora (por falta de filtro rápido de localidade) e ausência de alertas automatizados para conflitos entre exames, preparos e datas de retorno.
- **Solução Proposta**: Uma **aplicação web estritamente interna** (sistema satélite) para a Central de Marcação do HC-UFPE, construída sobre o `Framework-SETISD-HC-UFPE`. O sistema consulta as solicitações oficiais diretamente na base somente-leitura do AGHU, aplica um motor de priorização clínica **configurável**, fornece filtros operacionais (incluindo município/região para urgências), alerta sobre incompatibilidades/janelas de retorno e centraliza o controle de status e indicadores em banco local auditável.

## 2. Partes Interessadas (Stakeholders)

- **Usuários Finais**: Equipe da Central de Marcação de Exames (operadores que gerenciam a fila, aplicam filtros/alertas, efetivam o agendamento no AGHU e registram o status interno de atendimento/contato).
- **Patrocinadores**: Gestão Médica, Coordenação da Central de Marcação, Superintendência do HC-UFPE e Setor de TI e Saúde Digital (SETISD).
- **Beneficiários Indiretos (Pacientes)**: Cidadãos atendidos no HC-UFPE que se beneficiam de uma fila mais justa, ágil e com menos erros/remarcações — **sem acesso direto a este sistema** (a interação com pacientes será provida por aplicativo próprio em contratação pela sede da EBSERH).

## 3. Escopo do Produto

- **Funcionalidades principais**:
  - Importação/leitura da planilha do Google Forms (sem alterar o arquivo original) e **cruzamento/higienização automática** com a base somente-leitura do AGHU (PostgreSQL em produção / CSV espelho em desenvolvimento), identificando pacientes por **prontuário** e **número da solicitação**, detectando erros de exame, duplicidades e exames já realizados.
  - Painel interno da fila de marcação com **priorização clínica automática, determinística e configurável** (Oncologia → Transplante → Nefrologia/Hemodiálise → Vulneráveis → Rotina, considerando afinidade com a clínica solicitante e data de retorno).
  - **Filtros operacionais** por exame, unidade executora, especialidade, status e **município/região** (para aproveitamento de vagas de última hora, sem alterar a prioridade clínica).
  - **Cadastro editável de regras de exames e prioridades**: pesos de prioridade, matriz de incompatibilidades (preparo e mesmo dia), antecedência mínima, orientações de preparo e janelas vinculadas à data de retorno (ex: espirometria até 10 dias antes; INR até 72h).
  - **Monitoramento de confirmação em 24 horas** (antes da marcação oficial no AGHU, conforme alinhamento de 06/11) e controle de status do fluxo interno (`Na Fila`, `Aguardando Confirmação 24h`, `Confirmado / Agendado no AGHU`, `Sem Resposta / Cancelado`) com **trilha de auditoria imutável (`audit_logs`)**.
  - Painel gerencial (Dashboard) com indicadores operacionais (KPIs).
- **Limites do projeto (Fora de Escopo)**:
  - **Sem escrita no AGHU:** O sistema **não** grava, altera ou agenda exames diretamente no banco do AGHU, nem altera o ticket impresso emitido pelo sistema legado. A efetivação final permanece manual no AGHU.
  - **Sem portal para o paciente e sem disparo automático de WhatsApp/SMS:** O Google Forms oficial continua sendo a porta de entrada dos pacientes; o sistema é estritamente interno (AD/LDAP + RBAC).
  - **Exclusões operacionais alinhadas em 06/11:** Atendimentos presenciais diretos na Central, fluxos de remarcação/faltas, exceções de códigos de solicitação em lote no AGHU e gestão da fila estadual do SUS (CMCE).

## 4. Metas e Objetivos de Negócio

- **Redução de Retrabalho e Erros Operacionais**: Eliminar a conferência manual de planilhas soltas, bloqueando/sinalizando solicitações duplicadas e utilizando diretamente os dados oficiais do AGHU.
- **Equidade e Transparência na Priorização**: Garantir que critérios clínicos prioritários sejam aplicados de forma consistente e auditável, com flexibilidade para a gestão atualizar pesos e regras de preparo/retorno sem depender de alterações em código.
- **Otimização de Vagas e Redução do Tempo de Espera**: Agilizar o preenchimento de vagas ociosas e desistências de última hora por meio do filtro geográfico operacional e dos alertas de conflito/preparo.
- **Rastreabilidade e Gestão Orientada por Dados**: Substituir o controle informal em planilhas por histórico auditável e indicadores gerenciais (tempo de espera, ocupação, absenteísmo, remarcações e TFD).
