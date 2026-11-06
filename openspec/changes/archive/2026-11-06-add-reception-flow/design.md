# Design

## Context

- O frontend (Vue 3, TypeScript strict, Pinia, Vue Router, Tailwind 4, vee-validate + zod, Heroicons, vue-toastification) já tem a biblioteca de componentes evoluída pelo change `evolve-base-components`:
  - `Button` (variantes, `size`, `type`, `loading`);
  - `DataTable` (slots `cell-<chave>`, `clickable`/`row-click`, `highlight`, `pageSize`, `loading`, `emptyText`);
  - `Modal` (`size`, `closeOnBackdrop`);
  - `Badge`, `Stepper` (`steps`, `current`), `Tabs` (`v-model`, contador), `Alert` e `FilterChips`;
  - o utilitário `focus-ring` e os tokens `paper-*-soft/strong`.
- O backend não tem os domínios de AP. Toda a lógica deste change roda no navegador, com dados mockados.
- A autenticação mock aceita apenas `admin`/`admin` (`src/auth/auth.py`). O usuário autenticado (`useAuthStore().user`) é o "responsável" de todos os registros.
- O menu lateral (`DefaultLayout.vue`) tem links fixos no template, sem seções. As rotas atuais estão em `frontend/src/router/index.ts`.
- O modelo de dados de referência é `docs/especificacao/04-modelo-dados.md`. Os nomes de entidades, campos e domínios seguem esse documento, convertidos para camelCase.

## Goals / Non-Goals

**Goals:**
- Telas que já usem um contrato de dados próximo do futuro backend, para que trocar o mock pela API não mexa nas views.
- Toda mutação (entrada, conferência, não conformidade e devolução, cancelamento, situação da devolução, impressão, acionamento do plantão) gera evento no histórico do caso e registro de auditoria em memória.
- Impressão funcional no navegador, sem dependências novas.

**Non-Goals:**
- Persistência entre recarregamentos de página: os dados voltam à carga inicial ao recarregar.
- RBAC e perfis: não há verificação de perfil no frontend; o `admin` atua como recepcionista.
- Vínculo da nova amostra a um novo caso (`devolucao.novo_caso_id`): a situação da devolução é atualizada manualmente.
- Tela de auditoria, telas de outros setores, solicitação complementar, exportação de dados e escrita no AGHU.

## Decisions

### 1. Camadas: tipos → serviços (interface + mock) → stores → views
- `frontend/src/types/ap.ts`: tipos de domínio, como `SolicitacaoAghu`, `CasoAp`, `ConferenciaRecebimento`, `ItemMaterial`, `HistoricoCaso`, `NaoConformidade`, `Devolucao`, `Cancelamento`, `ExameIhq` e `AuditLog`, além das uniões de domínio (`StatusCaso`, `TipoExame`, `EtapaCodigo`, `SituacaoDevolucao` e outras), com os códigos da especificação (`RECEBIDO`, `AGUARDANDO_NOVA_AMOSTRA` etc.).
- `frontend/src/constants/ap.ts`: fluxo de etapas por tipo (equivalente a `config_fluxo_etapa`), rótulos e variante de `Badge` por status, catálogo de tipos de não conformidade, procedimentos, unidades de origem e prazos padrão por etapa.
- `frontend/src/services/ap/`: uma interface por domínio (`AghuService`, `CasoService`, `NaoConformidadeService`) e implementações em `services/ap/mock/`. O `services/ap/index.ts` exporta as instâncias, que hoje são as mock.
  - Os métodos são `async` e simulam latência curta (≈300 ms).
  - Os erros usam uma classe `ServiceError` com `detail`, no mesmo formato `{"detail": ...}` que o backend usa.
- `frontend/src/mocks/ap/`: carga inicial (`seed.ts`) e o "banco" em memória (`db.ts`), usados apenas pelas implementações mock.
- Stores Pinia: `recepcao` (estado do assistente de 4 passos), `casos` (lista, detalhe, cancelamento) e `devolucoes`. As views falam só com as stores.
- **Por quê:** espelha o padrão Provider do backend (ADR 03/06). Trocar o mock pela API é criar uma implementação HTTP com `services/api.ts` e mudar o `index.ts`.
- **Alternativa descartada:** dados direto nas stores. Seria mais rápido, mas acopla views e regras ao mock.

### 2. Regras de negócio nos serviços mock
Ficam nos serviços mock:
- geração do número interno (sequência por tipo e ano, e uma sequência `IH` própria);
- elegibilidade do caso de origem da IHQ;
- efeitos da não conformidade (com caso ou sem caso);
- a regra "situação final ⇒ não conformidade resolvida";
- os registros de histórico e auditoria.

As views só validam formulário.
- **Por quê:** essas regras vão para o backend (controllers). Mantê-las atrás da interface deixa claro o que migra.

### 3. Formulários com vee-validate + zod
O passo 3 da recepção usa um schema zod com união discriminada pelo tipo:
- os casos principais exigem quantidade, urgência e procedimento, e o motivo quando há urgência;
- a IHQ exige o caso de origem e a confirmação de divergência quando o prontuário difere.

O modal de não conformidade usa um schema por passo. O resumo de erros é montado a partir de `errors` do `useForm`, com links por âncora (`#campo`).
- **Por quê:** é o padrão já demonstrado em `Exemplos.vue` (ADR 02).

### 4. Rotas e menu
- Rotas novas, todas com `meta.requiresAuth`:
  - `/recepcao`;
  - `/casos`;
  - `/casos/:numero(.*)`, onde o parâmetro aceita a barra do número interno (`/casos/HP-0003/26`);
  - `/rejeicoes-devolucoes`.
- Um campo `meta.menu` indica o item do menu a destacar. O detalhe usa `consulta`.
- O menu passa a ser montado a partir de uma lista de seções (`{ titulo, itens[] }`) dentro do `DefaultLayout.vue`, mantendo o visual atual e o rodapé de versão. O contador da recepção vem da store `recepcao`.

### 5. Leitura global de código
- Componente `CodeScanField.vue` no cabeçalho do layout. Um listener de `keydown` (F2) no layout coloca o foco nele.
- A resolução do código fica em `CasoService.resolverCodigo(codigo)`. Ela retorna uma união: solicitação pendente, solicitação devolvida, caso (com aba e item opcionais) ou não encontrado. Assim, o campo e o passo 1 da recepção usam a mesma regra.
- Uma solicitação pendente leva à store `recepcao`, que carrega a solicitação e vai ao passo 2, e depois à navegação para `/recepcao`. Um caso leva a `router.push` com `query` `aba` e `item`.

### 6. Impressão sem dependências
- **Código de barras:** um helper `frontend/src/helpers/barcode.ts` gera Code 128 (subconjunto B, com dígito verificador) como lista de barras, desenhada em `<svg>` pelo componente `Barcode.vue`.
  - **Por quê:** não adiciona dependência e o Code 128 é lido por leitores comuns.
  - **Alternativa descartada:** JsBarcode, uma dependência não prevista no documento de arquitetura (`06-arquitetura.md`).
- **Pré-visualização:** `PrintPreview.vue` usa `Teleport` para um contêiner `#print-root`. Os componentes `EtiquetaFrasco.vue` (50×25 mm) e `FichaTrabalho.vue` (A4) usam medidas em `mm`. Uma regra `@media print` em `index.css` oculta tudo exceto `#print-root`, e `@page` define a margem.
- O tamanho físico depende da impressora; a etiqueta usa a regra `@page` com `size: 50mm 25mm` quando o conteúdo impresso for de etiquetas.

### 7. Histórico e auditoria em memória
- Cada mutação acrescenta um `HistoricoCaso`, quando há caso, e um `AuditLog`.
- O `AuditLog` tem categoria `NEGOCIO_CLINICO`, ação, recurso, `dadosAnteriores` e `dadosNovos` (JSON) e usuário. Os nomes seguem `src/models/audit_log.py` e `registrar_auditoria()`.
- Não há tela de auditoria. Os registros ficam acessíveis pela store, para inspeção e para a futura integração.

### 8. Carga inicial fictícia
Todos os dados são inventados para este change. Não se reaproveita nada do protótipo nem de `data/pacientes.csv`.
- Nomes de pacientes, médicos e funcionários são fictícios.
- Prontuários têm 7 dígitos e números de solicitação AGHU têm 7 dígitos com prefixo `77`.
- Datas são relativas ao momento da carga.

A carga cobre:
- 6 solicitações pendentes: HP, CG, CCV, CO e duas IHQ, uma com prontuário igual ao de um caso existente e outra com prontuário divergente;
- casos em todos os 13 status, com urgentes e todos os tipos principais;
- registros de etapas posteriores para as abas só de leitura;
- árvores de materiais;
- duas rejeições na recepção e uma devolução de caso.

## Risks / Trade-offs

- [Os dados se perdem ao recarregar a página] → Aceitável para a validação com usuários. A carga inicial é rica o bastante para demonstrar todos os estados.
- [As medidas de impressão variam por navegador e impressora] → As medidas usam `mm` e há pré-visualização. A validação na impressora térmica do setor fica registrada como pendência na entrega.
- [Erro no gerador de Code 128 deixa o código ilegível para o leitor] → A tarefa de verificação lê o código impresso ou exibido com um leitor ou aplicativo de celular e confere com o número interno.
- [Parâmetro de rota com barra] → O padrão `(.*)` aceita a barra. O link é sempre gerado por `router.push({ name, params })`.
- [Regras no mock divergirem do backend futuro] → As regras ficam isoladas nos serviços, com nomes e domínios da especificação.
- [Sem testes automatizados, as regras dos serviços dependem do roteiro manual] → Cada tarefa traz a sua verificação. Adotar o Vitest continua sendo uma decisão pendente do time.
