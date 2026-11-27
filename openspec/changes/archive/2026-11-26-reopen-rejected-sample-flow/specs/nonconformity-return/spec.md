# Spec Delta

## MODIFIED Requirements

### Requirement: Atualização da situação da devolução
O usuário SHALL poder alterar a situação de uma devolução pela ação "Alterar situação", que abre um modal com a identificação da devolução e somente o campo de situação. Salvar sem mudar a situação não SHALL registrar alteração. Cada alteração registra auditoria com os valores anterior e novo, o usuário e a data e hora. Quando a situação passa a "Nova amostra recebida" ou "Encerrada", a não conformidade vinculada passa a "Resolvida". A transição para "Nova amostra recebida" SHALL reabrir atomicamente os grupos rejeitados na recepção ou o caso devolvido, conforme o vínculo da devolução, respeitando estados terminais e mantendo o histórico anterior.

#### Scenario: Nova amostra recebida
- **WHEN** o usuário abre "Alterar situação", escolhe "Nova amostra recebida" no lugar de "Aguardando nova amostra" e salva
- **THEN** o modal fecha, a nova situação aparece no selo da linha, o sistema confirma a atualização e a auditoria registra os valores anterior e novo

#### Scenario: Cancelar a alteração
- **WHEN** o usuário abre "Alterar situação", muda a opção e fecha o modal sem salvar
- **THEN** a situação da devolução permanece a anterior

#### Scenario: Reabrir grupos rejeitados na recepção
- **WHEN** uma devolução sem caso passa para "Nova amostra recebida" e os grupos vinculados ainda estão devolvidos por essa ocorrência
- **THEN** esses grupos voltam a "Aguardando recebimento", deixam de apontar para a devolução e retornam à fila pendente na mesma transação

#### Scenario: Reabrir caso devolvido
- **WHEN** uma devolução vinculada a caso passa para "Nova amostra recebida" e o caso está "Devolvido"
- **THEN** o caso retorna ao estado ativo anterior registrado na ocorrência, ou "Recebido" para ocorrência legada sem esse dado, e o histórico recebe "FLUXO_REABERTO"

#### Scenario: Bloquear estados terminais
- **WHEN** a devolução está "Encerrada", algum grupo vinculado está "Cancelada" ou "Recebida", ou o caso não está "Devolvido"
- **THEN** a operação responde HTTP 409 sem alterar parcialmente devolução, grupos, caso ou auditoria

#### Scenario: Impedir regressão após avanço
- **WHEN** a devolução já está "Nova amostra recebida" e um grupo vinculado foi recebido ou cancelado depois disso
- **THEN** a tentativa de retornar a devolução para "Aguardando nova amostra" responde HTTP 409 e mantém os estados atuais
