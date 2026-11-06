## MODIFIED Requirements

### Requirement: Campo global de leitura
O cabeçalho SHALL exibir, para usuários autenticados, o campo de busca com o texto de apoio "Buscar por nº do caso, prontuário ou paciente (F2)" e ícone de busca, destinado exclusivamente à busca de casos já cadastrados. A tecla F2 SHALL colocar o foco nesse campo a partir de qualquer tela. A busca ignora espaços nas pontas, maiúsculas e minúsculas e acentos.

#### Scenario: Atalho F2
- **WHEN** o usuário pressiona F2 em qualquer tela autenticada
- **THEN** o campo global de busca recebe o foco

## ADDED Requirements

### Requirement: Resultados da busca global de casos
A partir de 2 caracteres, o campo SHALL listar abaixo dele os casos cujo número interno, prontuário ou nome do paciente contenham o texto. A lista mostra até 8 casos, cada um com número interno, tipo de exame, paciente, prontuário e status. Quando houver mais, SHALL indicar quantos existem e pedir para refinar a busca.

#### Scenario: Busca por nome do paciente
- **WHEN** o usuário digita parte do nome de um paciente com dois casos cadastrados
- **THEN** a lista exibe os dois casos com número, tipo, paciente, prontuário e status

#### Scenario: Muitos resultados
- **WHEN** o texto corresponde a 12 casos
- **THEN** a lista exibe 8 casos e informa que há 12 resultados, pedindo para refinar a busca

### Requirement: Abertura de caso pela busca global
Escolher um caso na lista, por clique ou com as setas e o Enter, SHALL abrir o detalhe desse caso, limpar o campo e fechar a lista. Enter sem caso destacado SHALL abrir o caso quando o texto for exatamente o número interno de um caso. Esc SHALL fechar a lista.

#### Scenario: Número interno completo
- **WHEN** o usuário digita o número interno exato de um caso e pressiona Enter
- **THEN** o detalhe desse caso é aberto

#### Scenario: Navegação por teclado
- **WHEN** o usuário desce com a seta até o segundo resultado e pressiona Enter
- **THEN** o detalhe do segundo caso da lista é aberto

### Requirement: Busca global sem resultado
Quando nenhum caso corresponder ao texto, a lista SHALL exibir "Nenhum caso encontrado para <texto>.", manter o texto no campo e não mudar de tela. A busca não SHALL considerar solicitações do AGHU que ainda não viraram caso.

#### Scenario: Solicitação pendente digitada
- **WHEN** o usuário digita o número de uma solicitação do AGHU ainda não recebida
- **THEN** a lista informa que nenhum caso foi encontrado e a tela atual é mantida

## REMOVED Requirements

### Requirement: Leitura de solicitação AGHU pendente
**Reason**: O campo do topo passa a buscar exclusivamente casos cadastrados. Abrir solicitações pendentes cabe à tela de Recepção de amostras.
**Migration**: Use o campo de leitura do passo 1 da Recepção de amostras ou "Iniciar recebimento" na fila de pendentes.

### Requirement: Leitura de caso, item ou IHQ
**Reason**: O campo do topo deixa de interpretar códigos de amostra, IHQ ou nº AGHU. A busca é por número interno, prontuário ou nome do paciente.
**Migration**: Busque pelo número interno do caso (que aparece na etiqueta) e use a aba Materiais ou IHQ do detalhe.

### Requirement: Código não encontrado
**Reason**: Substituído por "Busca global sem resultado", com a mensagem própria da busca de casos.
**Migration**: Nenhuma ação necessária.

### Requirement: Solicitação devolvida
**Reason**: Solicitações devolvidas não são casos cadastrados e saem do escopo da busca do topo.
**Migration**: Consulte a tela "Rejeições e devoluções" ou leia o número no passo 1 da Recepção de amostras, que continua informando a devolução.
