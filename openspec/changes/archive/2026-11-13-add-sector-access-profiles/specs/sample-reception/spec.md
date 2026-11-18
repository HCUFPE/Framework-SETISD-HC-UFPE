# sample-reception Specification

## ADDED Requirements

### Requirement: Autorização das operações existentes da Recepção

Operações protegidas da Recepção SHALL exigir a permissão explícita correspondente no backend. A interface SHALL refletir as permissões efetivas, mas sua ocultação de ações SHALL NOT substituir a autorização da API. O catálogo poderá evoluir junto com cada módulo; uma matriz global completa SHALL NOT ser requisito para concluir esta mudança.

#### Scenario: Operação autorizada

- **WHEN** identidade autenticada possui a permissão explícita para uma operação existente
- **THEN** o backend executa a operação e usa a identidade autenticada como autora

#### Scenario: Operação não autorizada por chamada direta

- **WHEN** identidade autenticada sem a permissão correspondente chama diretamente a operação da Recepção
- **THEN** o backend responde 403 sem executar a mutação

#### Scenario: Operação fora do catálogo vigente

- **WHEN** um perfil tenta executar uma operação sem concessão explícita no catálogo
- **THEN** o backend nega a operação por padrão
- **AND** o catálogo pode ser ampliado junto com o módulo que implementar essa operação

### Requirement: Impressão física no navegador

A impressão de etiquetas e ficha SHALL ocorrer no navegador, sem endpoint, evento de histórico ou registro de auditoria. A permissão de consulta ao caso SHALL continuar protegendo o acesso aos dados exibidos para impressão.

#### Scenario: Impressão sem registro no backend

- **WHEN** o usuário imprime etiquetas ou ficha de um caso consultável
- **THEN** o navegador abre a impressão física
- **AND** nenhum evento de impressão é enviado ou persistido pelo backend

### Requirement: Vínculo manual IHQ como contingência

Quando o vínculo da solicitação IHQ não vier do AGHU, a Recepção SHALL poder associar manualmente o grupo IHQ a um caso principal elegível usando `recepcao:receber`. Quando o AGHU fornecer a associação, esse é o fluxo ideal.

#### Scenario: Vínculo ausente no AGHU

- **WHEN** o usuário recebe uma solicitação IHQ sem caso de origem associado
- **THEN** a interface permite buscar e selecionar um caso elegível e confirma o vínculo mediante permissão
