<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Galeria de Componentes Utilizáveis</h1>

    <!-- Grid System Explanation Card -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Sistema de Grid Responsivo (12 Colunas)</h2>
      </template>
      <p>O layout utiliza um sistema de grid de 12 colunas, similar ao Bootstrap. Use as classes `grid`, `grid-cols-12`, e `col-span-*` para criar layouts. As classes são responsivas, permitindo que você defina diferentes larguras para diferentes tamanhos de tela (ex: `md:col-span-6`).</p>
    </Card>

    <!-- Grid System Example Cards -->
    <div class="grid grid-cols-12 gap-6 mb-6">
      <div class="col-span-12 md:col-span-4">
        <Card>
          <template #header><code>.col-span-4</code></template>
          <p>Este card ocupa 4 das 12 colunas em telas médias e maiores.</p>
        </Card>
      </div>
      <div class="col-span-12 md:col-span-8">
        <Card>
          <template #header><code>.col-span-8</code></template>
          <p>Este card ocupa 8 das 12 colunas em telas médias e maiores.</p>
        </Card>
      </div>
      <div class="col-span-12 md:col-span-6">
        <Card>
          <template #header><code>.col-span-6</code></template>
          <p>Este card ocupa 6 das 12 colunas em telas médias e maiores.</p>
        </Card>
      </div>
      <div class="col-span-12 md:col-span-6">
        <Card>
          <template #header><code>.col-span-6</code></template>
          <p>Este card ocupa 6 das 12 colunas em telas médias e maiores.</p>
        </Card>
      </div>
    </div>

    <!-- Form Example -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Exemplo de Formulário com Validação</h2>
      </template>
      <Form @submit="onSubmit" :validation-schema="validationSchema">
        <div class="grid grid-cols-12 gap-6">
          <div class="col-span-12 md:col-span-6">
            <div class="form-group">
              <label for="name" class="form-label">Nome Completo</label>
              <Field name="name" type="text" id="name" class="form-control" placeholder="Digite seu nome" validate-on-input />
              <ErrorMessage name="name" class="text-red-500 text-sm mt-1" />
            </div>
          </div>
          <div class="col-span-12 md:col-span-6">
            <div class="form-group">
              <label for="email" class="form-label">Endereço de E-mail</label>
              <Field name="email" type="email" id="email" class="form-control" placeholder="seu@email.com" validate-on-input />
              <ErrorMessage name="email" class="text-red-500 text-sm mt-1" />
            </div>
          </div>
          <div class="col-span-12">
            <div class="form-group">
              <label for="message" class="form-label">Mensagem</label>
              <Field as="textarea" name="message" id="message" rows="4" class="form-control" placeholder="Deixe sua mensagem..." validate-on-input />
              <ErrorMessage name="message" class="text-red-500 text-sm mt-1" />
            </div>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-4">
          <Button type="button" variant="default">Cancelar</Button>
          <Button type="submit" variant="primary" :disabled="isSubmitting">Enviar</Button>
        </div>
      </Form>
    </Card>

    <!-- Other Components Example -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Notificações e Modal Simples</h2>
      </template>
      <div class="flex flex-wrap gap-4">
        <!-- Toast Buttons -->
        <Button @click="showSuccessToast">Toast Sucesso</Button>
        <Button @click="showErrorToast" variant="danger">Toast Erro</Button>
        <Button @click="showInfoToast" variant="info">Toast Info</Button>
        <Button @click="showWarningToast" variant="warning">Toast Aviso</Button>

        <!-- Loading Button -->
        <Button @click="showLoadingButton" :loading="isLoadingButton">
          <template #icon>
            <CheckIcon class="h-5 w-5" />
          </template>
          Botão com Ícone
        </Button>

        <!-- Modal Button -->
        <Button @click="showModal = true" variant="secondary">Abrir Modal</Button>
      </div>
    </Card>

    <!-- Botões -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Botões</h2>
        <p class="text-sm text-gray-500 mt-1">Passe o mouse, clique e segure, e navegue com <kbd class="px-1 rounded bg-gray-100 border">Tab</kbd> para ver os estados de hover, pressionado e foco.</p>
      </template>
      <div class="space-y-5">
        <div>
          <h3 class="gallery-label">Variantes</h3>
          <div class="flex flex-wrap gap-3">
            <Button v-for="v in buttonVariants" :key="v" :variant="v">{{ v }}</Button>
          </div>
        </div>
        <div>
          <h3 class="gallery-label">Tamanhos</h3>
          <div class="flex flex-wrap items-center gap-3">
            <Button size="sm">Pequeno (sm)</Button>
            <Button size="md">Médio (md)</Button>
            <Button size="sm" variant="outline">
              <template #icon><PlusIcon class="h-4 w-4" /></template>
              Pequeno com ícone
            </Button>
            <Button size="sm" variant="info" aria-label="Visualizar"><EyeIcon class="h-4 w-4" /></Button>
          </div>
        </div>
        <div>
          <h3 class="gallery-label">Carregamento</h3>
          <div class="flex flex-wrap items-center gap-3">
            <Button :loading="demoLoading" @click="startDemoLoading">Salvar</Button>
            <Button :loading="demoLoading" variant="success" @click="startDemoLoading">
              <template #icon><CheckIcon class="h-5 w-5" /></template>
              Confirmar recebimento
            </Button>
            <Button :loading="demoLoading" size="sm" variant="outline" @click="startDemoLoading">Pequeno</Button>
            <span class="text-xs text-gray-500">Clique em qualquer um para simular 2 s de carregamento.</span>
          </div>
        </div>
        <div>
          <h3 class="gallery-label">Desabilitado</h3>
          <div class="flex flex-wrap gap-3">
            <Button disabled>Primário</Button>
            <Button disabled variant="danger">Perigo</Button>
            <Button disabled variant="outline">Contorno</Button>
            <Button disabled size="sm" variant="secondary">Pequeno</Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- Badges -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Badges</h2>
      </template>
      <div class="flex flex-wrap items-center gap-3">
        <Badge v-for="v in badgeVariants" :key="v" :variant="v">{{ v }}</Badge>
        <Badge variant="danger">URGENTE</Badge>
        <Badge variant="success" size="sm">pequeno</Badge>
      </div>
    </Card>

    <!-- Alertas -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Alertas</h2>
      </template>
      <div class="space-y-3">
        <Alert variant="info" title="Informação">A amostra será encaminhada à macroscopia após a conferência.</Alert>
        <Alert variant="success">Recebimento registrado com sucesso.</Alert>
        <Alert variant="warning" title="Atenção">O pedido médico não informa o CNS do paciente.</Alert>
        <Alert variant="danger" title="Acionar equipe de plantão">Amostra de congelação recebida fora do horário de expediente.</Alert>
        <Alert v-if="showDismissibleAlert" variant="info" title="Alerta fechável" dismissible @dismiss="showDismissibleAlert = false">
          Clique no X para ocultar este alerta.
        </Alert>
        <Button v-else size="sm" variant="outline" @click="showDismissibleAlert = true">Mostrar alerta fechável novamente</Button>
      </div>
    </Card>

    <!-- Passos -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Indicador de Passos</h2>
      </template>
      <div class="space-y-4">
        <Stepper :steps="stepperSteps" :current="currentStep" />
        <div class="flex gap-3">
          <Button size="sm" variant="secondary" :disabled="currentStep === 0" @click="currentStep--">Voltar</Button>
          <Button size="sm" :disabled="currentStep === stepperSteps.length - 1" @click="currentStep++">Avançar</Button>
        </div>
      </div>
    </Card>

    <!-- Abas -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Abas</h2>
        <p class="text-sm text-gray-500 mt-1">Com uma aba em foco, use as setas ← e → para trocar.</p>
      </template>
      <Tabs v-model="activeTab" :tabs="tabItems">
        <template #dados>
          <p>Dados do caso: paciente, prontuário, procedência e tipo de exame.</p>
        </template>
        <template #historico>
          <ul class="list-disc pl-5 space-y-1 text-sm">
            <li>06/11/2026 08:12 — Solicitação registrada</li>
            <li>06/11/2026 09:40 — Amostra recebida</li>
            <li>06/11/2026 10:05 — Encaminhada à macroscopia</li>
          </ul>
        </template>
        <template #anexos>
          <p class="text-gray-500">Nenhum anexo enviado.</p>
        </template>
      </Tabs>
    </Card>

    <!-- Tabela -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Tabela</h2>
        <p class="text-sm text-gray-500 mt-1">Célula personalizada (status), linha clicável, destaque de urgentes, paginação de 10 itens e etiquetas de filtro.</p>
      </template>
      <div class="space-y-4">
        <div class="flex flex-wrap items-end gap-4">
          <div>
            <label for="filtroStatus" class="form-label">Status</label>
            <select id="filtroStatus" v-model="filters.status" class="form-control">
              <option value="">Todos</option>
              <option v-for="st in statusOptions" :key="st" :value="st">{{ st }}</option>
            </select>
          </div>
          <div>
            <label for="filtroTipo" class="form-label">Tipo</label>
            <select id="filtroTipo" v-model="filters.tipo" class="form-control">
              <option value="">Todos</option>
              <option v-for="t in tipoOptions" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <label class="flex items-center gap-2 text-sm text-paper-text pb-2">
            <input v-model="filters.somenteUrgentes" type="checkbox" class="h-4 w-4" />
            Somente urgentes
          </label>
        </div>

        <FilterChips :chips="activeChips" @remove="removeFilter" @clear="clearFilters" />

        <DataTable
          :headers="caseHeaders"
          :items="filteredCases"
          :page-size="10"
          :highlight="(item) => item.urgente"
          clickable
          empty-text="Nenhum caso encontrado para os filtros."
          @row-click="(item) => toast.info(`Caso ${item.codigo} selecionado.`)"
        >
          <template #cell-paciente="{ item }">
            <div class="font-semibold text-gray-800">{{ item.paciente }}</div>
            <div class="text-xs text-gray-500">Prontuário {{ item.prontuario }}</div>
          </template>
          <template #cell-status="{ value }">
            <Badge :variant="statusVariant(value)">{{ value }}</Badge>
          </template>
          <template #cell-urgente="{ value }">
            <Badge v-if="value" variant="danger">URGENTE</Badge>
            <span v-else class="text-gray-400">—</span>
          </template>
          <template #actions="{ item }">
            <Button size="sm" variant="outline" @click="toast.success(`Ação no caso ${item.codigo} (a linha não foi acionada).`)">Ação</Button>
          </template>
        </DataTable>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
          <div>
            <div class="flex items-center justify-between mb-2">
              <h3 class="gallery-label mb-0">Carregamento</h3>
              <Button size="sm" variant="secondary" @click="tableLoading = !tableLoading">
                {{ tableLoading ? 'Concluir carregamento' : 'Simular carregamento' }}
              </Button>
            </div>
            <DataTable :headers="smallHeaders" :items="cases.slice(0, 3)" :loading="tableLoading" />
          </div>
          <div>
            <h3 class="gallery-label">Vazio com mensagem própria</h3>
            <DataTable :headers="smallHeaders" :items="[]" empty-text="Nenhum caso encontrado para os filtros." />
          </div>
        </div>
      </div>
    </Card>

    <!-- Modais -->
    <Card class="mb-6">
      <template #header>
        <h2 class="text-xl font-semibold">Modais</h2>
        <p class="text-sm text-gray-500 mt-1">Fecham com Esc, pelo botão X e (por padrão) ao clicar fora.</p>
      </template>
      <div class="flex flex-wrap gap-3">
        <Button v-for="sz in modalSizes" :key="sz" variant="outline" @click="openDemoModal({ size: sz })">Largura {{ sz }}</Button>
        <Button variant="info" @click="openDemoModal({ size: 'lg', long: true })">Conteúdo longo</Button>
        <Button variant="warning" @click="openDemoModal({ size: 'md', locked: true })">Sem fechar ao clicar fora</Button>
      </div>
    </Card>

    <!-- Modal Component -->
    <Modal :show="showModal" @close="showModal = false">
      <template #header>
        Título do Modal
      </template>

      <p>Este é o conteúdo do modal. Você pode colocar qualquer coisa aqui, como texto, imagens, ou até mesmo um formulário.</p>

      <template #footer>
        <Button @click="showModal = false" variant="default">Cancelar</Button>
        <Button @click="handleModalConfirm" variant="primary">Confirmar</Button>
      </template>
    </Modal>

    <!-- Modal de demonstração (larguras, conteúdo longo e clique fora desativado) -->
    <Modal :show="demoModal.show" :size="demoModal.size" :close-on-backdrop="!demoModal.locked" @close="demoModal.show = false">
      <template #header>Modal {{ demoModal.size }}{{ demoModal.locked ? ' — clique fora desativado' : '' }}</template>
      <p v-if="demoModal.locked">Clicar no fundo escurecido não fecha este modal. Use Esc, o X ou o botão do rodapé.</p>
      <p v-else-if="!demoModal.long">Este modal usa a largura <strong>{{ demoModal.size }}</strong>.</p>
      <template v-if="demoModal.long">
        <p v-for="n in 30" :key="n" class="mb-3">Parágrafo {{ n }}: o corpo rola internamente enquanto o cabeçalho e o rodapé permanecem visíveis.</p>
      </template>
      <template #footer>
        <Button variant="secondary" @click="demoModal.show = false">Fechar</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { Form, Field, ErrorMessage } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as z from 'zod';
import { useToast } from 'vue-toastification';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';
import Modal, { type ModalSize } from '../components/Modal.vue';
import Badge, { type BadgeVariant } from '../components/Badge.vue';
import Alert from '../components/Alert.vue';
import Stepper from '../components/Stepper.vue';
import Tabs from '../components/Tabs.vue';
import FilterChips, { type FilterChip } from '../components/FilterChips.vue';
import DataTable from '../components/DataTable.vue';
import { type ButtonVariant } from '../components/Button.vue';
import { CheckIcon, EyeIcon, PlusIcon } from '@heroicons/vue/24/outline';

const toast = useToast();
const isSubmitting = ref(false);
const isLoadingButton = ref(false);
const showModal = ref(false);

const validationSchema = toTypedSchema(
  z.object({
    name: z.string().nonempty('O nome é obrigatório'),
    email: z.string().nonempty('O e-mail é obrigatório').email('O e-mail é inválido'),
    message: z.string().nonempty('A mensagem é obrigatória').min(10, 'A mensagem deve ter no mínimo 10 caracteres'),
  })
);

function onSubmit(values: any) {
  isSubmitting.value = true;
  setTimeout(() => {
    isSubmitting.value = false;
    toast.success('Formulário enviado com sucesso!');
    console.log(JSON.stringify(values, null, 2));
  }, 2000);
}

function showSuccessToast() {
  toast.success('Esta é uma notificação de sucesso!');
}

function showErrorToast() {
  toast.error('Esta é uma notificação de erro!');
}

function showInfoToast() {
  toast.info('Esta é uma notificação de informação.');
}

function showWarningToast() {
  toast.warning('Esta é uma notificação de aviso.');
}

function showLoadingButton() {
  isLoadingButton.value = true;
  setTimeout(() => {
    isLoadingButton.value = false;
  }, 2000);
}

function handleModalConfirm() {
  toast.info('Ação do modal confirmada!');
  showModal.value = false;
}

// ---- Botões ----
const buttonVariants: ButtonVariant[] = ['primary', 'secondary', 'info', 'success', 'warning', 'danger', 'default', 'outline'];
const demoLoading = ref(false);

/** Simula uma ação de 2 segundos nos botões de carregamento. */
function startDemoLoading() {
  demoLoading.value = true;
  setTimeout(() => {
    demoLoading.value = false;
  }, 2000);
}

// ---- Badges e alertas ----
const badgeVariants: BadgeVariant[] = ['default', 'primary', 'info', 'success', 'warning', 'danger'];
const showDismissibleAlert = ref(true);

// ---- Passos ----
const stepperSteps = [
  { label: 'Identificação' },
  { label: 'Amostras' },
  { label: 'Conferência' },
  { label: 'Confirmação' },
];
const currentStep = ref(1);

// ---- Abas ----
const tabItems = [
  { key: 'dados', label: 'Dados' },
  { key: 'historico', label: 'Histórico', count: 3 },
  { key: 'anexos', label: 'Anexos', count: 0 },
];
const activeTab = ref('dados');

// ---- Tabela (dados fictícios) ----
interface CasoExemplo {
  id: number;
  codigo: string;
  paciente: string;
  prontuario: string;
  tipo: string;
  status: string;
  urgente: boolean;
}

const statusOptions = ['Recebido', 'Em análise', 'Liberado', 'Rejeitado'];
const tipoOptions = ['HP', 'CP', 'IHQ'];
const nomes = ['Maria Souza', 'José Lima', 'Ana Ferreira', 'Carlos Melo', 'Paula Rocha', 'João Alves', 'Rita Barros'];

const cases: CasoExemplo[] = Array.from({ length: 42 }, (_, i) => ({
  id: i + 1,
  codigo: `AP-2026-${String(i + 1).padStart(4, '0')}`,
  paciente: nomes[i % nomes.length],
  prontuario: String(100200 + i * 7),
  tipo: tipoOptions[i % tipoOptions.length],
  status: statusOptions[i % statusOptions.length],
  urgente: i % 9 === 0,
}));

const caseHeaders = [
  { text: 'Código', value: 'codigo' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Tipo', value: 'tipo' },
  { text: 'Status', value: 'status' },
  { text: 'Urgência', value: 'urgente' },
];

const smallHeaders = [
  { text: 'Código', value: 'codigo' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Status', value: 'status' },
];

const filters = reactive({ status: '', tipo: '', somenteUrgentes: false });

const filteredCases = computed(() =>
  cases.filter(
    (c) =>
      (!filters.status || c.status === filters.status) &&
      (!filters.tipo || c.tipo === filters.tipo) &&
      (!filters.somenteUrgentes || c.urgente),
  ),
);

const activeChips = computed<FilterChip[]>(() => {
  const chips: FilterChip[] = [];
  if (filters.status) chips.push({ key: 'status', label: `Status: ${filters.status}` });
  if (filters.tipo) chips.push({ key: 'tipo', label: `Tipo: ${filters.tipo}` });
  if (filters.somenteUrgentes) chips.push({ key: 'somenteUrgentes', label: 'Somente urgentes' });
  return chips;
});

/** Remove um único filtro a partir da etiqueta. */
function removeFilter(key: string) {
  if (key === 'status') filters.status = '';
  else if (key === 'tipo') filters.tipo = '';
  else if (key === 'somenteUrgentes') filters.somenteUrgentes = false;
}

/** Remove todos os filtros. */
function clearFilters() {
  filters.status = '';
  filters.tipo = '';
  filters.somenteUrgentes = false;
}

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

const tableLoading = ref(true);

// ---- Modais ----
const modalSizes: ModalSize[] = ['sm', 'md', 'lg', 'xl'];
const demoModal = reactive({ show: false, size: 'lg' as ModalSize, long: false, locked: false });

/** Abre o modal de demonstração com a configuração informada. */
function openDemoModal(opts: { size: ModalSize; long?: boolean; locked?: boolean }) {
  demoModal.size = opts.size;
  demoModal.long = !!opts.long;
  demoModal.locked = !!opts.locked;
  demoModal.show = true;
}
</script>

<style scoped>
@reference '../index.css';

.gallery-label {
  @apply mb-2 text-xs font-bold uppercase tracking-wider text-gray-400;
}
</style>
