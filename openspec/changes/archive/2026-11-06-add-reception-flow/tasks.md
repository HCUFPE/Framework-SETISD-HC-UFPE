# Tasks

## 1. Domínio, dados mockados e serviços

- [x] 1.1 Criar `frontend/src/types/ap.ts` com os tipos de domínio e as uniões de códigos da especificação (status do caso, tipo de exame, etapa, resultado da conferência, tipo e status de não conformidade, situação da devolução, situação da IHQ); verificar com `npx vue-tsc --noEmit`
- [x] 1.2 Criar `frontend/src/constants/ap.ts` com o fluxo de etapas por tipo (HP, CG, CCV, CO), os rótulos e as variantes de badge dos 13 status, o catálogo de tipos de não conformidade, os procedimentos, as unidades de origem e os prazos por etapa; verificar com `vue-tsc` e conferir os códigos com `04-modelo-dados.md`
- [x] 1.3 Criar `frontend/src/mocks/ap/seed.ts` e `db.ts` com a carga fictícia descrita no design (6 solicitações pendentes, casos nos 13 status, registros das etapas posteriores, árvores de materiais, 2 rejeições e 1 devolução de caso); verificar com `grep` que nenhum nome ou número do protótipo nem de `data/pacientes.csv` aparece na carga
- [x] 1.4 Criar as interfaces `AghuService`, `CasoService` e `NaoConformidadeService`, a classe `ServiceError` e as implementações mock, com latência simulada e as regras do design (numeração por tipo e ano e IH, elegibilidade da IHQ, efeitos da não conformidade, situação ⇒ resolvida, histórico e auditoria em cada mutação, `resolverCodigo`); verificar com `vue-tsc` e chamando cada método no console do navegador em modo dev
- [x] 1.5 Criar as stores Pinia `recepcao`, `casos` e `devolucoes`, consumindo apenas os serviços; verificar com `vue-tsc`

## 2. Navegação e leitura de código

- [x] 2.1 Adicionar as rotas `/recepcao`, `/casos`, `/casos/:numero(.*)` e `/rejeicoes-devolucoes` com `requiresAuth` e `meta.menu`; verificar que acessar `/recepcao` sem login leva ao login e que `/casos/HP-0003/26` resolve a rota do detalhe
- [x] 2.2 Reorganizar o menu do `DefaultLayout.vue` nas seções "Recepção" e "Temporário", com o contador de pendentes e o item ativo por `meta.menu`, e mantendo o recolhimento e o rodapé de versão; verificar pelos cenários da spec `app-navigation` e com `python audit_framework.py .` em 100%
- [x] 2.3 Criar `CodeScanField.vue` no cabeçalho, com o atalho F2 e a navegação conforme `resolverCodigo` (solicitação pendente, devolvida, caso, item, IHQ e não encontrado); verificar cada cenário da spec `code-scan` com códigos da carga inicial

## 3. Impressão

- [x] 3.1 Criar `helpers/barcode.ts` (Code 128-B com dígito verificador) e `Barcode.vue` (SVG); verificar lendo o código de um número interno exibido na tela com um leitor ou aplicativo de celular
- [x] 3.2 Criar `PrintPreview.vue`, `EtiquetaFrasco.vue` (50×25 mm, ordem da spec) e `FichaTrabalho.vue` (A4, 5 blocos e quadro de acompanhamento por etapa do fluxo), e a regra `@media print` e `@page` em `index.css`; verificar na janela de impressão do navegador que só o conteúdo pré-visualizado aparece, nas medidas corretas, e que cada impressão gera evento no histórico

## 4. Não conformidade e devolução

- [x] 4.1 Criar `NaoConformidadeModal.vue` em 2 passos (contexto automático, tipo, CMCE opcional, detalhamento, unidade de origem quando não há solicitação nem caso, quem recebeu e nova amostra), com validação zod; verificar os cenários de validação da spec `nonconformity-return`
- [x] 4.2 Ligar o modal aos efeitos do serviço: sem caso (solicitação devolvida, conferência rejeitada, volta ao passo 1) e com caso (status Devolvido, histórico, bloqueio), com situação inicial conforme "nova amostra"; verificar os dois caminhos com a carga inicial

## 5. Recepção de amostras

- [x] 5.1 Criar `RecepcaoAmostras.vue` com o `Stepper` e o passo 1 (campo com foco e Enter, mensagens de já recebida, devolvida e inexistente, lista de pendentes com "Ler etiqueta", botão de material sem etiqueta e aviso de AGHU indisponível); verificar os cenários de leitura da spec `sample-reception`
- [x] 5.2 Implementar o passo "Conferir" (dados do AGHU só para leitura, 4 itens obrigatórios, "Registrar não conformidade" e "Ler outra etiqueta"); verificar os cenários de conferência
- [x] 5.3 Implementar o passo "Completar e confirmar" para os casos principais (tipo sugerido, quantidade, urgência e motivo, procedimento, observações, resumo de erros com links, Ctrl+Enter); verificar a validação e a confirmação HP, CG, CCV e CO, incluindo a numeração por tipo e o encaminhamento
- [x] 5.4 Implementar o vínculo da IHQ (busca de caso elegível, bloqueio de devolvido ou cancelado, alerta e confirmação de prontuário divergente, sem criação de caso); verificar com as duas IHQ da carga inicial
- [x] 5.5 Implementar o passo "Etiquetas e ficha" (número com copiar, encaminhamento, URGENTE, lembrete do AGHU, alerta e registro único do plantão para CO, impressão, abrir caso, receber próxima); verificar os cenários de resultado e de congelação

## 6. Consulta de casos

- [x] 6.1 Criar `ConsultaCasos.vue` com busca, filtros (status, tipo, período, urgentes), `FilterChips`, `DataTable` paginada (10), ordenação urgentes e depois entrada mais recente, destaque, badges e clique ou Enter abrindo o detalhe, sem exportação; verificar os cenários da spec `case-search`

## 7. Detalhe do caso

- [x] 7.1 Criar `DetalheCaso.vue` com o cabeçalho (copiar, status, URGENTE com motivo), "Caso não encontrado", indicador do fluxo (com IHQ e etapa interrompida) e faixa de bloqueio; verificar com casos ativo, urgente, devolvido, cancelado e arquivado da carga inicial
- [x] 7.2 Implementar as 12 abas (Resumo com últimas movimentações, Solicitação AGHU, Recepção com conferência, etapas posteriores só para leitura, IHQ, Materiais em árvore com totais e item destacado por `query`, Não conformidades e Histórico imutável) e a seleção de aba por `query`; verificar cada aba com a carga inicial e após uma entrada nova
- [x] 7.3 Implementar as ações (Não conformidade, Imprimir e Cancelar caso com motivo obrigatório e confirmação), visíveis conforme o bloqueio; verificar os cenários de cancelamento e de ações da spec `case-detail`

## 8. Rejeições e devoluções

- [x] 8.1 Criar `RejeicoesDevolucoes.vue` com a lista (natureza, link do caso ou "AGHU nº"), os filtros (período, natureza, tipo, origem, etapa), o total, a paginação e o vazio; verificar os cenários de listagem e filtro da spec `nonconformity-return`
- [x] 8.2 Implementar a alteração inline da situação da devolução, com auditoria (anterior e novo) e não conformidade resolvida nas situações finais; verificar o cenário de atualização inspecionando a auditoria na store

## 9. Verificação integrada

- [x] 9.1 Rodar `npx vue-tsc --noEmit` sem erros, `npx vite build --outDir <diretório temporário>` com sucesso e `python audit_framework.py .` com 11/11 (100%)
- [x] 9.2 Percorrer o roteiro ponta a ponta com `admin`/`admin`:
  - receber uma HP urgente com 2 frascos, imprimir as etiquetas e a ficha e ler a etiqueta no F2;
  - receber uma CO e registrar o plantão;
  - vincular as duas IHQ;
  - devolver uma solicitação sem etiqueta e outra na conferência;
  - registrar uma não conformidade em um caso ativo e cancelar outro;
  - conferir na Consulta de casos, no Detalhe e em Rejeições e devoluções;
  - verificar hover, clique e foco nos novos elementos clicáveis.

  Registrar qualquer desvio no resumo da entrega.
