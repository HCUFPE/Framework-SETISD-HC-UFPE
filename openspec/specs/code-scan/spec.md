# code-scan Specification

## Purpose

Oferece, no cabeçalho de qualquer tela autenticada, uma busca rápida de casos já cadastrados por número interno, prontuário ou nome do paciente, levando direto ao detalhe do caso sem precisar navegar pelos menus. Solicitações do AGHU ainda não recebidas são tratadas na Recepção de amostras.

## Requirements

### Requirement: Campo global de leitura
O cabeçalho SHALL exibir, para usuários autenticados, o campo de busca com o texto de apoio "Caso, solicitação AGHU, prontuário ou paciente (F2)" e ícone de busca, destinado à busca de casos já cadastrados. A tecla F2 SHALL colocar o foco nesse campo a partir de qualquer tela. A busca ignora espaços nas pontas, maiúsculas e minúsculas e acentos.

#### Scenario: Atalho F2
- **WHEN** o usuário pressiona F2 em qualquer tela autenticada
- **THEN** o campo global de busca recebe o foco

### Requirement: Resultados da busca global de casos
A partir de 2 caracteres, o campo SHALL listar abaixo dele os casos cujo número interno, código da solicitação AGHU (inclusive de IHQ vinculada), prontuário ou nome do paciente contenham o texto. A lista mostra até 8 casos, cada um com número interno, tipo de exame, paciente, prontuário, nº da solicitação AGHU e status. Quando houver mais, SHALL indicar quantos existem e pedir para refinar a busca.

#### Scenario: Busca por nome do paciente
- **WHEN** o usuário digita parte do nome de um paciente com dois casos cadastrados
- **THEN** a lista exibe os dois casos com número, tipo, paciente, prontuário, solicitação e status

#### Scenario: Busca pelo código da solicitação AGHU
- **WHEN** o usuário digita o código 7711390 de uma solicitação que gerou o caso HP-0010/26
- **THEN** a lista exibe o caso HP-0010/26

#### Scenario: Muitos resultados
- **WHEN** o texto corresponde a 12 casos
- **THEN** a lista exibe 8 casos e informa que há 12 resultados, pedindo para refinar a busca

### Requirement: Abertura de caso pela busca global
Escolher um caso na lista, por clique ou com as setas e o Enter, SHALL abrir o detalhe desse caso, limpar o campo e fechar a lista. Enter sem caso destacado SHALL abrir o caso quando o texto for exatamente o número interno de um caso, ou o código da solicitação AGHU de um único caso. Esc SHALL fechar a lista.

#### Scenario: Número interno completo
- **WHEN** o usuário digita o número interno exato de um caso e pressiona Enter
- **THEN** o detalhe desse caso é aberto

#### Scenario: Navegação por teclado
- **WHEN** o usuário desce com a seta até o segundo resultado e pressiona Enter
- **THEN** o detalhe do segundo caso da lista é aberto

### Requirement: Busca global sem resultado
Quando nenhum caso corresponder ao texto, a lista SHALL exibir "Nenhum caso encontrado para <texto>.", manter o texto no campo e não mudar de tela. Se o texto for o código de uma solicitação do AGHU com amostras aguardando recebimento, a lista SHALL oferecer o atalho para abrir a conferência dessa solicitação na recepção.

#### Scenario: Solicitação pendente digitada
- **WHEN** o usuário digita o número de uma solicitação do AGHU ainda não recebida
- **THEN** a lista informa que nenhum caso foi encontrado e oferece "A solicitação <nº> aguarda recebimento: abrir na recepção"

#### Scenario: Atalho para a recepção
- **WHEN** o usuário escolhe o atalho da solicitação pendente
- **THEN** a tela "Recepção de amostras" abre a conferência dessa solicitação
