# Documento de Visão

## 1. Problema e Oportunidade

* **O Problema**:

O processo de marcação de exames de imagem no HC-UFPE exige que os funcionários, de maneira manual e despadronizada, validem as credenciais de cada pedido, agendem exames à medida que as solicitações chegam e comuniquem o resultado ao paciente para cada solicitação, tornando o fluxo complexo e ineficiente.

* **Impacto**:

Isso impacta tanto os profissionais responsáveis pela marcação quanto os pacientes, os quais precisam lidar com atrasos imprevisíveis e até podem voltar para o final da fila em casos de erro de preenchimento.

A relevância do problema vem do impacto na capacidade operacional do HC em não conseguir utilizar as vagas disponíveis da forma mais eficiente possível no momento atual, sem efetuar a priorização de pacientes com quadros mais severos.

* **Solução Proposta**:

Será desenvolvida uma plataforma web composta por duas interfaces principais: um novo formulário digital para coleta mais eficiente dos dados do paciente e uma interface de gestão para os funcionários hospitalares.

O sistema recebe os dados do paciente via formulário, os valida automaticamente consultando o sistema AGHU e aplica regras de negócio pré-definidas com a equipe de marcação para ordenar as solicitações de forma inteligente. O resultado é exibido em uma tela final em que o funcionário apenas confirma e agenda os exames na ordem sugerida pelo sistema, sem necessidade de intervenção manual no sequenciamento.

## 2. Partes Interessadas (Stakeholders)

* Pacientes
* Funcionários da Central de Marcação
* Gerentes da Central de Marcação

## 3. Escopo do Produto

* O projeto irá implementar apenas as seguintes funcionalidades:
    - Um formulário que recebe informações de pedidos de marcação;
    - Um sistema que valida e verifica em tempo real os pedidos enviados;
    - Um sistema que ordena os pedidos com base nas informações do paciente e da solicitação do(s) exame(s);
    - Uma interface para a visualização da fila de pedidos ordenados;
    - Uma interface para o gerenciamento da fila, do formulário e dos pedidos atribuídos a cada funcionário.

* O sistema não irá fazer a marcação no sistema do Hospital das Clínicas automaticamente.

* O sistema não se comprometerá com a marcação de exames que não são gerenciados pela Central de Marcação.

* O sistema não garante estabilidade caso a de fonte da verdade do Hospital das Clínicas, o AGHU, não esteja disponível.

## 4. Metas e Objetivos de Negócio

* Redução do tempo de resposta de marcação do paciente;
* Redução da taxa de reenvio dos pacientes;
* Redução de erros provenientes do tratamento manual de dados;
* Redução de tempo de marcação de um exame.