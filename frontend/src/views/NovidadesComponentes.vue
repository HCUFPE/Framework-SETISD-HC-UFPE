<template>
  <!--
    Página temporária: apresenta as mudanças do change "evolve-base-components".
    Remover (view, rota e link da sidebar) quando não for mais necessária.
  -->
  <div class="space-y-6">
    <Card>
      <template #header>
        <div class="flex items-center gap-3">
          <SparklesIcon class="h-7 w-7 text-paper-text" />
          <h1 class="text-2xl font-bold text-paper-text">Novidades dos Componentes</h1>
        </div>
        <p class="text-sm text-gray-500 mt-1">
          Página temporária com o que mudou na biblioteca de componentes. Passe o mouse, clique e use
          <kbd class="px-1 rounded bg-gray-100 border">Tab</kbd> para ver o retorno de interação.
        </p>
      </template>

      <Tabs v-model="activeTab" :tabs="tabs">
        <!-- ================= Componentes evoluídos ================= -->
        <template #evoluidos>
          <div class="space-y-6">
            <!-- Retorno de interação -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Retorno de interação (todos os clicáveis)</h2>
                <p class="showcase-desc">
                  O Tailwind 4 tirou o cursor de mão dos botões. Agora todo elemento clicável mostra o cursor de mão,
                  muda de cor no hover, fica "pressionado" no clique, mostra um contorno de foco só na navegação por
                  teclado e usa o cursor de "não permitido" quando está desabilitado. Vale também para o menu lateral,
                  o botão de perfil, os cards da Início, os botões de Configurações e o "mostrar senha" do Login.
                </p>
              </header>
              <div class="flex flex-wrap items-center gap-3">
                <button type="button" class="focus-ring rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 active:bg-gray-200 transition">
                  Botão nativo
                </button>
                <a href="#" class="focus-ring rounded text-sm font-semibold text-paper-info-strong hover:underline" @click.prevent>Link</a>
                <button type="button" disabled class="rounded-md border border-gray-200 px-3 py-1.5 text-sm text-gray-400">
                  Nativo desabilitado
                </button>
              </div>
            </section>

            <!-- Button -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Button</h2>
                <p class="showcase-desc">
                  Novas variantes <code>secondary</code> (antes caía no estilo <code>default</code>) e <code>outline</code>;
                  tamanho <code>sm</code> passou a funcionar; o tipo padrão agora é <code>button</code> (só envia
                  formulário com <code>type="submit"</code>); o carregamento mostra um indicador giratório sem mudar a largura.
                </p>
              </header>
              <div class="space-y-3">
                <div class="flex flex-wrap gap-3">
                  <Button v-for="v in buttonVariants" :key="v" :variant="v">{{ v }}</Button>
                </div>
                <div class="flex flex-wrap items-center gap-3">
                  <Button size="sm">Pequeno (sm)</Button>
                  <Button size="md">Médio (md)</Button>
                  <Button :loading="demoLoading" @click="startDemoLoading">Carregar 2 s</Button>
                  <Button :loading="demoLoading" variant="success" @click="startDemoLoading">
                    <template #icon><CheckIcon class="h-5 w-5" /></template>
                    Com ícone
                  </Button>
                  <Button disabled>Desabilitado</Button>
                </div>
              </div>
            </section>

            <!-- DataTable -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">DataTable</h2>
                <p class="showcase-desc">
                  Mantém o uso antigo (<code>headers</code> + <code>items</code> + slot <code>actions</code>) e ganha:
                  conteúdo por coluna (<code>#cell-status</code>), linha clicável por clique ou Enter
                  (<code>clickable</code> + <code>row-click</code>, sem disparar pelos botões de ação), destaque de linha
                  (<code>highlight</code>), paginação no cliente (<code>page-size</code>), carregamento e mensagem de vazio.
                </p>
              </header>
              <div class="space-y-4">
                <DataTable
                  :headers="caseHeaders"
                  :items="cases"
                  :page-size="5"
                  :highlight="(item) => item.urgente"
                  clickable
                  @row-click="(item) => toast.info(`Caso ${item.codigo} selecionado.`)"
                >
                  <template #cell-status="{ value }">
                    <Badge :variant="statusVariant(value)">{{ value }}</Badge>
                  </template>
                  <template #cell-urgente="{ value }">
                    <Badge v-if="value" variant="danger">URGENTE</Badge>
                    <span v-else class="text-gray-400">—</span>
                  </template>
                  <template #actions="{ item }">
                    <Button size="sm" variant="outline" @click="toast.success(`Ação no caso ${item.codigo}.`)">Ação</Button>
                  </template>
                </DataTable>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <DataTable :headers="smallHeaders" :items="[]" loading />
                  <DataTable :headers="smallHeaders" :items="[]" empty-text="Nenhum caso encontrado para os filtros." />
                </div>
              </div>
            </section>

            <!-- Modal -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Modal</h2>
                <p class="showcase-desc">
                  Larguras <code>sm</code>, <code>md</code>, <code>lg</code> (padrão, igual ao anterior) e <code>xl</code>;
                  conteúdo longo rola por dentro com cabeçalho e rodapé fixos; o clique fora agora fecha de fato (antes não
                  funcionava) e pode ser desativado com <code>:close-on-backdrop="false"</code>. O botão de fechar ganhou
                  rótulo acessível e foco visível.
                </p>
              </header>
              <div class="flex flex-wrap gap-3">
                <Button v-for="sz in modalSizes" :key="sz" variant="outline" @click="openModal({ size: sz })">Largura {{ sz }}</Button>
                <Button variant="info" @click="openModal({ size: 'lg', long: true })">Conteúdo longo</Button>
                <Button variant="warning" @click="openModal({ size: 'md', locked: true })">Sem fechar ao clicar fora</Button>
              </div>
            </section>

            <!-- LoadingIndicator -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">LoadingIndicator</h2>
                <p class="showcase-desc">
                  Correção da classe <code>bg-opacity-50</code> (sintaxe do Tailwind 3) para <code>bg-black/50</code>:
                  o fundo do carregamento global volta a ser semitransparente. Obs.: o componente ainda não está montado no
                  <code>App.vue</code>; aqui ele é montado só nesta página para a demonstração.
                </p>
              </header>
              <Button variant="secondary" @click="showGlobalLoading">Mostrar carregamento global (1,5 s)</Button>
            </section>
          </div>
        </template>

        <!-- ================= Componentes novos ================= -->
        <template #novos>
          <div class="space-y-6">
            <!-- Badge -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Badge</h2>
                <p class="showcase-desc">
                  Etiqueta de texto curto para status e urgência. Variantes <code>default</code>, <code>primary</code>,
                  <code>info</code>, <code>success</code>, <code>warning</code> e <code>danger</code>, sempre com fundo
                  claro e texto escuro (contraste AA). Tamanhos <code>sm</code> e <code>md</code>.
                </p>
              </header>
              <div class="flex flex-wrap items-center gap-3">
                <Badge v-for="v in badgeVariants" :key="v" :variant="v">{{ v }}</Badge>
                <Badge variant="danger">URGENTE</Badge>
                <Badge variant="success" size="sm">pequeno</Badge>
              </div>
            </section>

            <!-- Alert -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Alert</h2>
                <p class="showcase-desc">
                  Aviso em bloco com ícone por variante (<code>info</code>, <code>success</code>, <code>warning</code>,
                  <code>danger</code>), título opcional e opção de fechar (<code>dismissible</code> + evento
                  <code>dismiss</code>).
                </p>
              </header>
              <div class="space-y-3">
                <Alert variant="info" title="Informação">A amostra será encaminhada à macroscopia após a conferência.</Alert>
                <Alert variant="success">Recebimento registrado com sucesso.</Alert>
                <Alert variant="warning" title="Atenção">O pedido médico não informa o CNS do paciente.</Alert>
                <Alert variant="danger" title="Acionar equipe de plantão">Amostra de congelação recebida fora do expediente.</Alert>
                <Alert v-if="showDismissible" variant="info" title="Alerta fechável" dismissible @dismiss="showDismissible = false">
                  Clique no X para ocultar.
                </Alert>
                <Button v-else size="sm" variant="outline" @click="showDismissible = true">Mostrar novamente</Button>
              </div>
            </section>

            <!-- Stepper -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Stepper</h2>
                <p class="showcase-desc">
                  Indicador de passos (somente exibição): passos concluídos com check, passo atual destacado e marcado
                  com <code>aria-current="step"</code>, passos futuros atenuados.
                </p>
              </header>
              <div class="space-y-4">
                <Stepper :steps="steps" :current="currentStep" />
                <div class="flex gap-3">
                  <Button size="sm" variant="secondary" :disabled="currentStep === 0" @click="currentStep--">Voltar</Button>
                  <Button size="sm" :disabled="currentStep === steps.length - 1" @click="currentStep++">Avançar</Button>
                </div>
              </div>
            </section>

            <!-- Tabs -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">Tabs</h2>
                <p class="showcase-desc">
                  Abas com <code>v-model</code>, contador opcional, papéis ARIA e troca por clique ou pelas setas
                  ← → (Home/End também). Um slot por painel (<code>#&lt;chave&gt;</code>). Esta página usa o mesmo componente.
                </p>
              </header>
              <Tabs v-model="demoTab" :tabs="demoTabs">
                <template #dados><p>Dados do caso: paciente, prontuário, procedência e tipo de exame.</p></template>
                <template #historico>
                  <ul class="list-disc pl-5 space-y-1 text-sm">
                    <li>08:12 — Solicitação registrada</li>
                    <li>09:40 — Amostra recebida</li>
                    <li>10:05 — Encaminhada à macroscopia</li>
                  </ul>
                </template>
                <template #anexos><p class="text-gray-500">Nenhum anexo enviado.</p></template>
              </Tabs>
            </section>

            <!-- FilterChips -->
            <section class="showcase">
              <header>
                <h2 class="showcase-title">FilterChips</h2>
                <p class="showcase-desc">
                  Etiquetas dos filtros ativos, removíveis uma a uma (evento <code>remove</code>), com a ação
                  "Limpar filtros" (evento <code>clear</code>). Sem filtros, não exibe nada.
                </p>
              </header>
              <div class="space-y-3">
                <div class="flex flex-wrap items-end gap-4">
                  <div>
                    <label for="novStatus" class="form-label">Status</label>
                    <select id="novStatus" v-model="filters.status" class="form-control">
                      <option value="">Todos</option>
                      <option v-for="st in statusOptions" :key="st" :value="st">{{ st }}</option>
                    </select>
                  </div>
                  <div>
                    <label for="novTipo" class="form-label">Tipo</label>
                    <select id="novTipo" v-model="filters.tipo" class="form-control">
                      <option value="">Todos</option>
                      <option v-for="t in tipoOptions" :key="t" :value="t">{{ t }}</option>
                    </select>
                  </div>
                </div>
                <FilterChips :chips="chips" @remove="(key) => (filters[key as keyof typeof filters] = '')" @clear="filters.status = filters.tipo = ''" />
                <p v-if="chips.length === 0" class="text-xs text-gray-400">Nenhum filtro ativo: o componente fica oculto.</p>
              </div>
            </section>
          </div>
        </template>
      </Tabs>
    </Card>

    <LoadingIndicator />

    <Modal :show="modal.show" :size="modal.size" :close-on-backdrop="!modal.locked" @close="modal.show = false">
      <template #header>Modal {{ modal.size }}{{ modal.locked ? ' — clique fora desativado' : '' }}</template>
      <p v-if="modal.locked">Clicar no fundo escurecido não fecha este modal. Use Esc, o X ou o botão do rodapé.</p>
      <p v-else-if="!modal.long">Este modal usa a largura <strong>{{ modal.size }}</strong>.</p>
      <template v-if="modal.long">
        <p v-for="n in 30" :key="n" class="mb-3">Parágrafo {{ n }}: o corpo rola por dentro e o cabeçalho e o rodapé continuam visíveis.</p>
      </template>
      <template #footer>
        <Button variant="secondary" @click="modal.show = false">Fechar</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useToast } from 'vue-toastification';
import { CheckIcon, SparklesIcon } from '@heroicons/vue/24/outline';
import Card from '../components/Card.vue';
import Button, { type ButtonVariant } from '../components/Button.vue';
import DataTable from '../components/DataTable.vue';
import Modal, { type ModalSize } from '../components/Modal.vue';
import LoadingIndicator from '../components/LoadingIndicator.vue';
import Badge, { type BadgeVariant } from '../components/Badge.vue';
import Alert from '../components/Alert.vue';
import Stepper from '../components/Stepper.vue';
import Tabs from '../components/Tabs.vue';
import FilterChips, { type FilterChip } from '../components/FilterChips.vue';
import { useUiStore } from '../stores/ui';

const toast = useToast();
const uiStore = useUiStore();

const tabs = [
  { key: 'evoluidos', label: 'Componentes evoluídos', count: 5 },
  { key: 'novos', label: 'Componentes novos', count: 5 },
];
const activeTab = ref('evoluidos');

// ---- Button ----
const buttonVariants: ButtonVariant[] = ['primary', 'secondary', 'info', 'success', 'warning', 'danger', 'default', 'outline'];
const demoLoading = ref(false);

/** Simula uma ação de 2 segundos. */
function startDemoLoading() {
  demoLoading.value = true;
  setTimeout(() => (demoLoading.value = false), 2000);
}

// ---- DataTable (dados fictícios) ----
const statusOptions = ['Recebido', 'Em análise', 'Liberado', 'Rejeitado'];
const tipoOptions = ['HP', 'CP', 'IHQ'];
const nomes = ['Maria Souza', 'José Lima', 'Ana Ferreira', 'Carlos Melo', 'Paula Rocha'];

const cases = Array.from({ length: 12 }, (_, i) => ({
  id: i + 1,
  codigo: `AP-2026-${String(i + 1).padStart(4, '0')}`,
  paciente: nomes[i % nomes.length],
  status: statusOptions[i % statusOptions.length],
  urgente: i % 4 === 0,
}));

const caseHeaders = [
  { text: 'Código', value: 'codigo' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Status', value: 'status' },
  { text: 'Urgência', value: 'urgente' },
];

const smallHeaders = [
  { text: 'Código', value: 'codigo' },
  { text: 'Paciente', value: 'paciente' },
];

/** Variante do badge para cada status. */
function statusVariant(status: string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    Recebido: 'info',
    'Em análise': 'warning',
    Liberado: 'success',
    Rejeitado: 'danger',
  };
  return map[status] ?? 'default';
}

// ---- Modal ----
const modalSizes: ModalSize[] = ['sm', 'md', 'lg', 'xl'];
const modal = reactive({ show: false, size: 'lg' as ModalSize, long: false, locked: false });

/** Abre o modal de demonstração com a configuração informada. */
function openModal(opts: { size: ModalSize; long?: boolean; locked?: boolean }) {
  modal.size = opts.size;
  modal.long = !!opts.long;
  modal.locked = !!opts.locked;
  modal.show = true;
}

// ---- LoadingIndicator ----
/** Exibe o carregamento global por 1,5 segundo. */
function showGlobalLoading() {
  uiStore.setLoading(true);
  setTimeout(() => uiStore.setLoading(false), 1500);
}

// ---- Componentes novos ----
const badgeVariants: BadgeVariant[] = ['default', 'primary', 'info', 'success', 'warning', 'danger'];
const showDismissible = ref(true);

const steps = [{ label: 'Identificação' }, { label: 'Amostras' }, { label: 'Conferência' }, { label: 'Confirmação' }];
const currentStep = ref(1);

const demoTabs = [
  { key: 'dados', label: 'Dados' },
  { key: 'historico', label: 'Histórico', count: 3 },
  { key: 'anexos', label: 'Anexos', count: 0 },
];
const demoTab = ref('dados');

const filters = reactive({ status: 'Recebido', tipo: 'HP' });

const chips = computed<FilterChip[]>(() => {
  const list: FilterChip[] = [];
  if (filters.status) list.push({ key: 'status', label: `Status: ${filters.status}` });
  if (filters.tipo) list.push({ key: 'tipo', label: `Tipo: ${filters.tipo}` });
  return list;
});
</script>

<style scoped>
@reference '../index.css';

.showcase {
  @apply rounded-xl border border-gray-200 bg-white p-5 space-y-4;
}

.showcase-title {
  @apply text-lg font-bold text-paper-text;
}

.showcase-desc {
  @apply mt-1 text-sm text-gray-500 leading-relaxed;
}

.showcase-desc code {
  @apply rounded bg-gray-100 px-1 text-[0.8em] text-paper-default;
}
</style>
