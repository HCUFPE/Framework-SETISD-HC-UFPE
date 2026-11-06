# Tasks

## 1. Dependência de ícones

- [x] 1.1 Instalar `lucide-vue-next` em `frontend/` (D1). Verificar que aparece em `package.json`, que `npm run build` passa e que um import de `PanelRight` e `Scan` compila no `npx vue-tsc --noEmit`.

## 2. Menu lateral e nome do sistema (app-navigation)

- [x] 2.1 Alterar `SYSTEM_TITLE` em `src/version.py`, o fallback em `frontend/src/config/version.ts` e o `<title>` de `frontend/index.html` para "Sistema de Gestão Integrada de Serviços de Anatomia Patológica" (D3). Verificar que `GET /api/health` devolve o novo `system_title` e que o teste de health do pytest continua passando.
- [x] 2.2 Em `layouts/DefaultLayout.vue`, separar a identidade do sistema (sem ação, nome quebrando linha, sem truncar) do novo botão `PanelRight` de recolher/expandir, com `aria-label` e `aria-expanded` conforme o estado (D2). Verificar no navegador: clicar no nome não recolhe; o botão recolhe e expande; com o menu recolhido, o botão continua visível e acessível por teclado.
- [x] 2.3 Fazer o item "Recepção de amostras" do menu chamar `recepcaoStore.reiniciar()` a cada clique. Em `RecepcaoAmostras.vue`, observar `passo` voltando a 0 para recarregar os pendentes, fechar o modal de não conformidade e focar o campo de leitura (D5). Verificar: no passo "Completar e confirmar", clicar no menu volta ao passo de leitura com o campo limpo e em foco, e vindo de outra tela com recebimento em andamento também abre no passo de leitura.

## 3. Busca global de casos (code-scan)

- [x] 3.1 Adicionar `buscar(termo, limite)` ao contrato `services/ap/types.ts`, implementá-lo no mock de casos (número interno, prontuário e nome, sem diferenciar maiúsculas, minúsculas e acentos; número exato primeiro, depois a entrada mais recente; retorna `{ itens, total }`) e expor na store `casos` (D4). Verificar pelo console com `window.apMock` ou chamada direta: o termo do nome de um paciente retorna os casos dele, e o nº de uma solicitação pendente retorna 0 itens.
- [x] 3.2 Reescrever o campo do topo como combobox de busca de casos: placeholder "Buscar por nº do caso, prontuário ou paciente (F2)", só o ícone de busca, mínimo de 2 caracteres, debounce, até 8 resultados com número, tipo, paciente, prontuário e status, aviso "N resultados, refine a busca", setas, Enter, Esc, clique, Enter direto no número exato, mensagem "Nenhum caso encontrado para <texto>." e F2 mantido (D4). Verificar no navegador cada cenário da spec `code-scan`, inclusive que um nº AGHU pendente não navega para a recepção.
- [x] 3.3 Remover `resolverCodigo`, `ResolucaoCodigo` e o código ligado a eles que ficou sem uso. Verificar com `grep -rn "resolverCodigo\|ResolucaoCodigo" frontend/src` sem ocorrências e com `npx vue-tsc --noEmit` sem erros.

## 4. Recepção de amostras (sample-reception)

- [x] 4.1 Exibir o `Stepper` da recepção só quando `recepcao.passo > 0` (D6). Verificar: a tela inicial não mostra o indicador, e ele aparece ao iniciar a conferência com "Ler etiqueta AGHU" concluído.
- [x] 4.2 Trocar o `QrCodeIcon` do passo de leitura pelo `Scan` do Lucide. Verificar visualmente no passo 1.
- [x] 4.3 Adicionar `HORAS_ALERTA_PENDENTE = 2` em `constants/ap.ts` e ajustar o seed para gerar pendentes com espera de minutos e de algumas horas, incluindo pelo menos uma CO e uma acima de 2 h (D7). Verificar que a lista de pendentes do mock tem esses casos.
- [x] 4.4 Substituir a `DataTable` de `PassoLeitura.vue` pela fila de cards "Para receber": contador, badge do tipo e exame, nº AGHU, material e origem, tempo de espera com destaque acima de 2 h, botão "Iniciar recebimento", ordem CO primeiro e depois a mais antiga, estado vazio e AGHU indisponível (D7). Verificar no navegador os cenários "Ler pela lista", "Espera longa" e "Lista vazia" (com `apMock`), e a navegação por teclado até os botões.
- [x] 4.5 Em `PassoComplemento.vue`, implementar a urgência automática para CO: Sim travado com a nota "Automático para Congelação", motivo pré-preenchido com `MOTIVO_URGENCIA_CONGELACAO`, editável e obrigatório, e restauração ao trocar de tipo (D8). Verificar: escolher CO trava Sim e preenche o motivo; apagar o motivo e confirmar mostra o erro de obrigatório; trocar para HP destrava e limpa a sugestão não editada; uma solicitação com tipo sugerido CO já abre travada.

## 5. Detalhe do caso (case-detail)

- [x] 5.1 Reorganizar o cabeçalho de `DetalheCaso.vue`: número, copiar e selos à esquerda e ações à direita na mesma linha, na ordem Não conformidade → Cancelar caso → Imprimir, com o dropdown de impressão alinhado à direita e os metadados abaixo (D11). Verificar em tela larga (ordem e alinhamento) e em tela estreita (quebra sem sobreposição), e que um caso bloqueado mostra só "Imprimir".
- [x] 5.2 Remover o `overflow-x-auto` do wrapper do fluxo e fazer `FluxoCaso.vue` quebrar as etapas em linhas (D11). Verificar com Playwright, em larguras de 1440, 1024 e 390 px, que o indicador não tem rolagem horizontal (`scrollWidth <= clientWidth`) e que o cenário "Caso interrompido" continua correto.

## 6. Não conformidade e devoluções (nonconformity-return)

- [x] 6.1 Remover `cmce` e `recebidoPorNome` dos tipos, do schema e dos campos do `NaoConformidadeModal.vue`, da validação e montagem no mock, do texto do histórico, do seed, da aba Não conformidades do detalhe e da tabela de devoluções. A coluna passa a "Devolvido por" (D9). Verificar com `grep -rni "cmce\|recebidoPor\|quem recebeu" frontend/src` sem ocorrências, `npx vue-tsc --noEmit` sem erros e um registro de devolução completo pela recepção e pelo detalhe.
- [x] 6.2 Em `RejeicoesDevolucoes.vue`, trocar o select da coluna "Situação" por `Badge` e adicionar a coluna de ação com o botão "Alterar situação" (D10). Verificar que a tabela não tem mais campo editável.
- [x] 6.3 Criar `components/ap/AlterarSituacaoDevolucaoModal.vue` sobre `Modal.vue`: dados da devolução só leitura, campo de situação, "Salvar" desabilitado sem mudança, chamada a `store.atualizarSituacao()`, toast e fechamento (D10). Verificar os cenários "Nova amostra recebida" (selo atualizado, auditoria com anterior e novo, NC "Resolvida") e "Cancelar a alteração".

## 7. Verificação integrada

- [x] 7.1 Percorrer o fluxo completo no navegador (Playwright): receber uma CO pela fila, buscar o caso pelo topo com F2, abrir o detalhe, registrar uma não conformidade e alterar a situação da devolução. Confirmar que não há erros no console.
- [x] 7.2 Rodar `npx vue-tsc --noEmit` e `npm run build` em `frontend/`, `pytest` na raiz e `python audit_framework.py .`, com 100% de conformidade.

## Workflow follow-up

- Não commitar sem pedido explícito do usuário. Avisar que as mudanças estão prontas para commit.
- Arquivar o change (`/opsx:archive`) após a revisão do usuário.
