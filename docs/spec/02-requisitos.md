# Especificação de Requisitos

## Requisitos Funcionais (RF)

### 1. FORMULÁRIO
| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| RF101 | Feedback imediato | Usuário recebe feedback sobre envio do formulário na mesma sessão. | Essencial |
| RF102 | Validação ao enviar | Informações validadas assim que são enviadas. | Essencial |
| RF103 | Checagem disponibilidade | Sistema verifica individualmente disponibilidade de cada exame por solicitação. | Essencial |
| RF104 | Resultado por exame | Deixar claro quais exames puderam ser marcados e quais não (relatório por solicitação). | Essencial |
| RF105 | Resposta a erros | Resposta imediata em casos de formulários preenchidos incorretamente. | Essencial |
| RF106 | Definição de vagas | Define automaticamente a quantidade de entradas por exame com base nas vagas disponíveis. | Alta |
| RF107 | Fechamento automático | Impede novas entradas se não há vagas disponíveis para o(s) exame(s) solicitado(s). | Alta |
 
### 2. ÁREA DO FUNCIONÁRIO
| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| RF201 | Visualizar fila | Mostrar fila ordenada de cartões com informações das solicitações. | Essencial |
| RF202 | Cards resumo | Visualizar informações resumidas das solicitações através de cards. | Essencial |
| RF203 | Filtrar solicitações | O funcionário deve conseguir filtrar solicitações. | Alta |
| RF204 | Área individual | O funcionário deve possuir uma área individual no sistema. | Alta |
| RF205 | Assumir solicitação | O funcionário deve conseguir assumir uma solicitação da fila geral. | Alta |
| RF206 | Devolver solicitação | O funcionário deve conseguir devolver uma solicitação para a fila geral. | Alta |
| RF207 | Alterar status | Alterar o status de uma solicitação. | Alta |
| RF208 | Pesquisar solicitações | Pesquisar por nome do paciente, prontuário ou tipo de exame. | Média |
| RF209 | Notificações automáticas | Receber notificação para verificar a resposta do paciente após 24 horas. | Média |

### 3. ÁREA DO ADMINISTRADOR
| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| RF301 | Métricas operacionais | Visualizar métricas operacionais da fila (marcações por funcionário, total marcado, tempo de espera por paciente). | Essencial |
| RF302 | Visualizar marcações | Visualizar exames a serem marcados e o funcionário responsável. | Alta |
| RF303 | Liberar solicitações | Permitir que o administrador libere solicitações que ficaram bloqueadas (assumidas por um funcionário por tempo excessivo) | Alta |
| RF304 | Reatribuir solicitações | Reatribuir solicitações entre funcionários. | Alta |
| RF305 | Configurar filtros rápidos | Definir quais filtros rápidos serão exibidos na fila principal. | Média |
| RF306 | Filtrar marcações | Filtrar exames marcados por critérios (data, funcionário, tipo). | Média |
| RF307 | Solicitações paradas | Visualizar solicitações paradas por muito tempo. | Média |

## Requisitos Não Funcionais (RNF)

### 1. FORMULÁRIO
| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF101 | Acessibilidade | Elementos visuais preferíveis; fácil compreensão; etapas separadas para reduzir carga cognitiva. |
| RNF102 | Design responsivo | Priorizar visão em telefones/telas pequenas; layout adaptativo. |
| RNF103 | Simplicidade | Minimizar número de campos; auto-preenchimento assistido onde aplicável. |

### 2. ÁREA DO FUNCIONÁRIO
| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF201 | Consistência | Todo funcionário deve ver a mesma fila em tempo real. |
| RNF202 | Confiabilidade | Evitar que dois funcionários assumam/editem simultaneamente a mesma solicitação. |
| RNF203 | Usabilidade | Baixo esforço cognitivo; principais ações em poucos cliques; leitura rápida via cores/tags. |

### 3. ÁREA DO ADMINISTRADOR
| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF301 | Usabilidade | Baixo esforço cognitivo; principais ações em poucos cliques; leitura rápida via cores/tags. |
