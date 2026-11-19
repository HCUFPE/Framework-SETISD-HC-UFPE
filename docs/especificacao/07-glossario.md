# Glossário e Referências

## 1. Termos Técnicos
* **HIS**: Hospital Information System.
* **TISS**: Troca de Informação de Saúde Suplementar.
* **AGHU**: Aplicação de Gestão para Hospitais Univesitários
* **AD**: Active Directory

## 2. Termos da Anatomia Patológica
* **Bancada**: área de trabalho por tipo de exame. A Anatomia Patológica tem 5: HP, CO, IHQ, CG e CCV.
* **HP**: exame histopatológico, feito em fragmentos ou peças de tecido.
* **CO**: congelação, exame intraoperatório de resposta rápida ao Bloco Cirúrgico.
* **IHQ**: imuno-histoquímica, exame com anticorpos feito a partir de um bloco. O nº interno usa o prefixo `IH`.
* **CG**: citologia geral, feita em líquidos ou lâminas.
* **CCV**: citologia cérvico-vaginal.
* **Solicitação**: pedido de exame criado no AGHU, identificado por `codigo_solicitacao` (6 ou 7 dígitos).
* **Número da amostra (`numero_amostra`)**: número de cada amostra dentro da solicitação no AGHU. Pode ter lacunas.
* **Laboratório (`codigo_lab`)**: código do AGHU que define a bancada: 207 = HP, 203 = CG, 139 = CCV, 205 = CO, 209 = IHQ.
* **Sigla do exame (`sigla_exame`)**: identifica o exame no AGHU (ex.: APECR, CCVM, CONGE, IMUHI). Só o descreve; não define a bancada.
* **Status do item**: situação do item no AGHU: A COLETAR (AC), EM COLETA (EC), COLETADO (CO), AREA EXECUTORA (AE), PENDENTE (PE), EXECUTANDO (EX), LIBERADO (LI) e CANCELADO (CA).
* **Especialidade**: clínica responsável pelo pedido. Corresponde à coluna "clínica" da planilha.
* **Unidade**: andar ou ambulatório de origem do pedido.
* **Paciente Externo**: origem no AGHU. Sempre vem sem especialidade e pode vir sem prontuário.
* **Referência ao HP**: indicação do HP de origem em uma IHQ, no formato `HP-AAAA/N` (ex.: `HP-2025/24`).
* **CMCE**: sistema de agendamento da SES-PE. O nº da solicitação no CMCE não vem do AGHU.
* **SISCAN**: sistema de informação do câncer, do Ministério da Saúde.
* **Nº interno**: identificador do exame na Anatomia Patológica, formado por sigla + sequencial (ex.: `HP 4757`). A sequência é independente por tipo e reinicia a cada ano.
* **Não conformidade**: problema encontrado na conferência (ex.: amostra sem etiqueta do AGHU) que faz o material ser devolvido ao setor de origem, sem gerar nº interno.
* **Macroscopia**: etapa de avaliação a olho nu da peça, com sua descrição e a seleção dos fragmentos a processar.
* **Cassete**: pequeno recipiente identificado que guarda os fragmentos de tecido durante o processamento.
* **Cell-block**: bloco feito a partir do sedimento de uma amostra líquida, processado como um bloco de tecido.

## 3. Referências
* Normas da ANS, CFM e manuais internos.
