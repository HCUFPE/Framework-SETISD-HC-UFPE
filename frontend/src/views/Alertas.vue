<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-3xl font-bold text-slate-900">Alertas do Sistema</h2>
      <div class="flex flex-wrap gap-2">
        <UiButton
          v-for="filtro in filtros"
          :key="filtro.value"
          :variant="filtroTipo === filtro.value ? 'default' : 'outline'"
          size="sm"
          @click="toggleFiltro(filtro.value)"
        >
          {{ filtro.label }}
        </UiButton>
      </div>
    </div>

    <div class="space-y-3">
      <article
        v-for="alerta in alertasFiltrados"
        :key="alerta.id"
        class="rounded-xl border shadow-sm transition cursor-pointer"
        :class="[
          alerta.lido ? alertConfig[alerta.tipo].readClass : alertConfig[alerta.tipo].cardClass,
          alerta.lido ? 'opacity-60 saturate-50' : 'hover:shadow-md'
        ]"
        role="button"
        tabindex="0"
        @click="openModal(alerta)"
      >
        <div class="p-4">
          <div class="flex items-start gap-4">
            <div
              class="rounded-full p-2"
              :class="alerta.lido ? 'bg-slate-100 text-slate-400' : alertConfig[alerta.tipo].iconBg"
            >
              <component
                :is="alertConfig[alerta.tipo].icon"
                class="h-5 w-5"
                :class="alerta.lido ? 'text-slate-400' : alertConfig[alerta.tipo].iconColor"
              />
            </div>
            <div class="flex-1 space-y-2">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3
                    class="font-semibold"
                    :class="alerta.lido ? 'text-slate-500' : 'text-slate-900'"
                  >
                    {{ alerta.titulo }}
                  </h3>
                  <p
                    class="mt-1 text-sm"
                    :class="alerta.lido ? 'text-slate-400' : 'text-slate-600'"
                  >
                    {{ alerta.mensagem }}
                  </p>
                </div>
                <UiBadge
                  :class="alerta.lido ? 'border-slate-200 bg-slate-100 text-slate-500' : alertConfig[alerta.tipo].badgeClass"
                >
                  {{ formatTipo(alerta.tipo) }}
                </UiBadge>
              </div>
              <div
                class="flex items-center gap-2 text-xs"
                :class="alerta.lido ? 'text-slate-400' : 'text-slate-500'"
              >
                <ClockIcon class="h-3 w-3" />
                <span>{{ alerta.dataHora }}</span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>

    <Modal :show="showModal" @close="closeModal">
      <template #header>
        {{ modalTitle }}
      </template>
      <div v-if="selectedAlert" class="space-y-3">
        <div
          class="rounded-lg border shadow-sm p-3"
          :class="[
            selectedAlert.lido ? alertConfig[selectedAlert.tipo].readClass : alertConfig[selectedAlert.tipo].cardClass,
            selectedAlert.lido ? 'opacity-70 saturate-50' : ''
          ]"
        >
          <div class="flex items-start gap-3">
            <div
              class="rounded-full p-2"
              :class="selectedAlert.lido ? 'bg-slate-100 text-slate-400' : alertConfig[selectedAlert.tipo].iconBg"
            >
              <component
                :is="alertConfig[selectedAlert.tipo].icon"
                class="h-4 w-4"
                :class="selectedAlert.lido ? 'text-slate-400' : alertConfig[selectedAlert.tipo].iconColor"
              />
            </div>
            <div class="flex-1 space-y-1">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h4
                    class="font-semibold text-sm"
                    :class="selectedAlert.lido ? 'text-slate-500' : 'text-slate-900'"
                  >
                    {{ selectedAlert.titulo }}
                  </h4>
                  <p
                    class="text-xs"
                    :class="selectedAlert.lido ? 'text-slate-400' : 'text-slate-600'"
                  >
                    {{ selectedAlert.mensagem }}
                  </p>
                </div>
                <UiBadge
                  :class="selectedAlert.lido ? 'border-slate-200 bg-slate-100 text-slate-500' : alertConfig[selectedAlert.tipo].badgeClass"
                >
                  {{ formatTipo(selectedAlert.tipo) }}
                </UiBadge>
              </div>
              <div
                class="flex items-center gap-2 text-[11px]"
                :class="selectedAlert.lido ? 'text-slate-400' : 'text-slate-500'"
              >
                <ClockIcon class="h-3 w-3" />
                <span>{{ selectedAlert.dataHora }}</span>
              </div>
            </div>
          </div>
        </div>
        <p class="text-sm text-slate-600">
          Confirme para alterar o status do alerta.
        </p>
      </div>
      <template #footer>
        <UiButton variant="outline" @click="closeModal">Não agora</UiButton>
        <UiButton @click="toggleRead">{{ primaryActionLabel }}</UiButton>
      </template>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import {
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';
import Modal from '../components/Modal.vue';
import { computed, ref } from 'vue';
import { useToast } from 'vue-toastification';

type AlertType = 'critico' | 'aviso' | 'info';
type AlertFilter = AlertType | 'todos';

type Alert = {
  id: string;
  tipo: AlertType;
  titulo: string;
  mensagem: string;
  dataHora: string;
  lido?: boolean;
};

const alertas = ref<Alert[]>([
  {
    id: '1',
    tipo: 'critico',
    titulo: 'UTI Fechada para Admissoes',
    mensagem: 'Taxa de ocupacao atingiu 100%. Novas admissoes suspensas.',
    dataHora: '2025-11-18 15:30',
  },
  {
    id: '2',
    tipo: 'aviso',
    titulo: 'Alta Aguardando Destino',
    mensagem: 'Paciente 456789 no Leito 03 aguarda definicao do NIR ha 4 horas.',
    dataHora: '2025-11-18 14:15',
  },
  {
    id: '3',
    tipo: 'info',
    titulo: 'Nova Solicitacao de Vaga',
    mensagem: 'BC solicitou vaga cirurgica para paciente 123456.',
    dataHora: '2025-11-18 13:45',
  },
  {
    id: '4',
    tipo: 'critico',
    titulo: 'Sinalizacao de Transferencia',
    mensagem: 'Leito 08 marcado para transferencia urgente.',
    dataHora: '2025-11-18 12:00',
  },
  {
    id: '5',
    tipo: 'aviso',
    titulo: 'Tempo de Higienizacao Excedido',
    mensagem: 'Leito 12 em higienizacao ha mais de 2 horas.',
    dataHora: '2025-11-18 11:30',
  },
]);

const toast = useToast();
const showModal = ref(false);
const selectedAlert = ref<Alert | null>(null);
const filtroTipo = ref<AlertFilter>('todos');

const alertConfig: Record<
  AlertType,
  {
    icon: any;
    iconColor: string;
    badgeClass: string;
    cardClass: string;
    readClass: string;
    iconBg: string;
  }
> = {
  critico: {
    icon: ExclamationTriangleIcon,
    iconColor: 'text-red-600',
    badgeClass: 'border border-red-200 bg-red-100 text-red-800',
    cardClass: 'border-red-200 bg-red-100',
    readClass: 'border-slate-200 bg-slate-50',
    iconBg: 'bg-red-100',
  },
  aviso: {
    icon: ExclamationCircleIcon,
    iconColor: 'text-amber-600',
    badgeClass: 'border border-amber-200 bg-amber-100 text-amber-800',
    cardClass: 'border-amber-200 bg-amber-100',
    readClass: 'border-slate-200 bg-slate-50',
    iconBg: 'bg-amber-100',
  },
  info: {
    icon: InformationCircleIcon,
    iconColor: 'text-blue-600',
    badgeClass: 'border border-blue-200 bg-blue-100 text-blue-800',
    cardClass: 'border-blue-200 bg-blue-100',
    readClass: 'border-slate-200 bg-slate-50',
    iconBg: 'bg-blue-100',
  },
};

const formatTipo = (tipo: AlertType) => tipo.charAt(0).toUpperCase() + tipo.slice(1);

const filtros = [
  { label: 'Criticos', value: 'critico' },
  { label: 'Avisos', value: 'aviso' },
  { label: 'Informacoes', value: 'info' },
] as const;

const openModal = (alerta: Alert) => {
  selectedAlert.value = alerta;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  selectedAlert.value = null;
};

const modalTitle = computed(() =>
  selectedAlert.value?.lido ? 'Marcar alerta como não lido?' : 'Marcar pendência como lida/resolvida?'
);

const alertasFiltrados = computed(() => {
  if (filtroTipo.value === 'todos') return alertas.value;
  return alertas.value.filter(alerta => alerta.tipo === filtroTipo.value);
});

const toggleFiltro = (valor: AlertFilter) => {
  filtroTipo.value = filtroTipo.value === valor ? 'todos' : valor;
};

const primaryActionLabel = computed(() =>
  selectedAlert.value?.lido ? 'Marcar como não lida' : 'Sim, marcar como lida'
);

const toggleRead = () => {
  if (!selectedAlert.value) return;
  const idx = alertas.value.findIndex(a => a.id === selectedAlert.value?.id);
  if (idx >= 0) {
    const nextStatus = !alertas.value[idx].lido;
    const updated = { ...alertas.value[idx], lido: nextStatus };
    alertas.value[idx] = updated;
    selectedAlert.value = updated;
    toast.success(nextStatus ? 'Alerta marcado como lido/resolvido.' : 'Alerta marcado como não lido.');
  }
  closeModal();
};
</script>
