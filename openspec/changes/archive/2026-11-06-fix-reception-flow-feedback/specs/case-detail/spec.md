## MODIFIED Requirements

### Requirement: Indicador do fluxo do caso
O detalhe SHALL exibir as etapas do fluxo do tipo do caso, marcando as concluídas, a atual e as futuras. O indicador SHALL caber na largura disponível, quebrando as etapas em linhas quando necessário, e não SHALL exibir barra de rolagem.

#### Scenario: Caso CG em processamento
- **WHEN** o usuário abre um caso CG com status "Em processamento técnico"
- **THEN** Recepção aparece como concluída, Processamento técnico como atual e as demais como futuras

#### Scenario: Caso interrompido
- **WHEN** o caso está devolvido ou cancelado
- **THEN** o indicador mostra a etapa em que o caso parou, marcada como interrompida

#### Scenario: Tela estreita
- **WHEN** o usuário abre o detalhe de um caso em uma janela estreita
- **THEN** as etapas do fluxo quebram em mais de uma linha e nenhuma barra de rolagem aparece no indicador

### Requirement: Ações do caso ativo
Para casos ativos, o detalhe SHALL oferecer, nesta ordem, "Não conformidade", "Cancelar caso" e "Imprimir" (etiquetas das amostras ou ficha de trabalho). Para casos bloqueados, SHALL oferecer apenas "Imprimir". As ações SHALL ficar na mesma linha do número interno e dos selos, alinhadas à direita, e quebrar para a linha seguinte só quando não houver espaço.

#### Scenario: Imprimir a partir do detalhe
- **WHEN** o usuário escolhe "Imprimir" e depois "Ficha de trabalho"
- **THEN** a pré-visualização da ficha de trabalho do caso é aberta

#### Scenario: Posição das ações
- **WHEN** o usuário abre um caso ativo em tela larga
- **THEN** "Não conformidade", "Cancelar caso" e "Imprimir" aparecem nessa ordem, na linha do número interno e dos selos
