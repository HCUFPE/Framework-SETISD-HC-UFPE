# case-search Specification

## Purpose

Permite localizar qualquer caso de anatomia patológica, inclusive os devolvidos, cancelados e arquivados, a partir de busca e filtros, e abrir o seu detalhe.

## Requirements

### Requirement: Busca textual de casos
A tela "Consulta de casos" SHALL filtrar os casos enquanto o usuário digita, comparando o texto, sem diferenciar maiúsculas de minúsculas e por trecho, com número interno, nº da solicitação AGHU, prontuário e nome do paciente.

#### Scenario: Busca por prontuário
- **WHEN** o usuário digita parte de um prontuário existente
- **THEN** a tabela exibe apenas os casos desse prontuário

### Requirement: Filtros de casos
A tela SHALL oferecer:
- filtro por status, com os 13 status do caso;
- filtro por tipo de exame (HP, CG, CCV e CO);
- filtro por período de entrada (qualquer data, últimos 7, 30 ou 90 dias);
- a opção "Somente urgentes".

Os filtros SHALL ser combinados entre si e com a busca.

#### Scenario: Filtros combinados
- **WHEN** o usuário escolhe o tipo HP e ativa "Somente urgentes"
- **THEN** apenas os casos HP urgentes são exibidos

### Requirement: Etiquetas de filtros ativos
Cada filtro ativo, incluindo a busca, SHALL aparecer como uma etiqueta removível, junto com a ação "Limpar filtros". Qualquer mudança de filtro SHALL voltar a tabela à primeira página.

#### Scenario: Remover filtro
- **WHEN** o usuário remove a etiqueta "Status: Recebido"
- **THEN** o filtro de status volta a "Todos" e a tabela é atualizada

### Requirement: Tabela de casos
A tabela SHALL exibir:
- número interno, com o selo URGENTE quando aplicável;
- tipo;
- paciente com prontuário;
- nº AGHU;
- material;
- status, com selo de cor por categoria;
- data e hora de entrada.

A tabela é paginada em 10 casos por página, com os urgentes primeiro e, dentro de cada grupo, a entrada mais recente primeiro. As linhas dos casos urgentes são destacadas.

#### Scenario: Ordenação
- **WHEN** existem casos urgentes e não urgentes no resultado
- **THEN** os urgentes aparecem antes, com destaque na linha

#### Scenario: Paginação
- **WHEN** o resultado tem 23 casos
- **THEN** a primeira página exibe 10 casos e o rodapé indica "Exibindo 1–10 de 23"

### Requirement: Abertura do caso
Clicar em uma linha, ou pressionar Enter com a linha em foco, SHALL abrir o detalhe do caso correspondente.

#### Scenario: Clique na linha
- **WHEN** o usuário clica na linha do caso CG-0004/26
- **THEN** o detalhe de CG-0004/26 é exibido

### Requirement: Resultado vazio
Quando nenhum caso atender à busca e aos filtros, a tela SHALL exibir "Nenhum caso encontrado. Revise a busca ou limpe os filtros."

#### Scenario: Busca sem resultado
- **WHEN** o usuário busca um texto que não corresponde a nenhum caso
- **THEN** a mensagem de vazio é exibida no lugar das linhas

### Requirement: Sem exportação de dados
A consulta não SHALL oferecer exportação nem download da lista de casos.

#### Scenario: Ações da tela
- **WHEN** o usuário visualiza a tela "Consulta de casos"
- **THEN** não existe ação de exportar, baixar ou gerar arquivo da lista
