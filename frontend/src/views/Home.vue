<template>
  <section class="space-y-6">
    <div class="space-y-3 mb-12">
      <div class="flex items-center justify-between">
        <h2 class="text-3xl font-bold text-slate-900">Resumo dos Leitos</h2>
      </div>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <div
          v-for="card in overviewCards"
          :key="card.title"
          class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
        >
          <p class="text-sm font-medium text-slate-600">{{ card.title }}</p>
          <p :class="['mt-2 text-3xl font-bold', card.color]">{{ card.value }}</p>
          <p v-if="card.caption" class="mt-1 text-xs text-slate-500">{{ card.caption }}</p>
        </div>
      </div>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">Visao Geral dos Leitos</h2>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <TransitionGroup
          name="fade-scale"
          tag="div"
          class="flex flex-wrap items-center gap-2"
        >
          <button
            v-for="option in statusFilterOptions"
            v-if="filtrosAbertos"
            :key="option.value"
            class="flex items-center gap-2 rounded-lg border px-3 py-1 text-sm font-medium transition"
            :class="
              statusFilter === option.value
                ? 'border-blue-200 bg-blue-50 text-blue-700 shadow-sm'
                : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            "
            @click="setStatusFilter(option.value)"
          >
            <span class="h-2 w-2 rounded-full" :class="dotColor(option.value)" />
            {{ option.label }}
          </button>
        </TransitionGroup>
        <UiButton
          variant="outline"
          size="sm"
          class="shadow-sm"
          @click="toggleFiltros"
        >
          <FunnelIcon class="h-5 w-5 text-slate-600" />
          <ChevronRightIcon
            class="h-4 w-4 text-slate-500 transition-transform duration-200"
            :class="filtrosAbertos ? 'rotate-180' : ''"
          />
        </UiButton>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <BedCard
        v-for="leito in leitosFiltrados"
        :key="leito.leitoNumero"
        v-bind="leito"
        @solicitar-alta="handleSolicitarAlta(leito)"
        @cancelar-alta="handleCancelarAlta(leito)"
        @cancelar-reserva="handleCancelarReserva(leito)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { FunnelIcon } from '@heroicons/vue/24/outline';
import { computed, ref, onMounted } from 'vue';
import { ChevronRightIcon } from '@heroicons/vue/20/solid';
import BedCard from '../components/BedCard.vue';
import UiButton from '../components/ui/Button.vue';
import { useToast } from 'vue-toastification';
import { getLeitosFormatados, getEstatisticasLeitos } from '../services/api';
import type { LeitoFormatado, BedStatus } from '../types';

type StatusFilter = BedStatus | 'todos';

const leitos = ref<LeitoFormatado[]>([]);

const overviewCards = ref([
  { title: 'Taxa de Ocupacao Global', value: '0%', color: 'text-emerald-600', caption: '0 de 0 leitos ocupados' },
  { title: 'Leitos Disponiveis', value: '0', color: 'text-emerald-600' },
  { title: 'Leitos em Uso', value: '0', color: 'text-emerald-600' },
  { title: 'Leitos em Higienizacao', value: '0', color: 'text-emerald-600' },
  { title: 'Leitos Desativados', value: '0', color: 'text-emerald-600' },
  { title: 'Reservas Pendentes', value: '0', color: 'text-emerald-600' },
]);

const toast = useToast();

// Carrega os dados mockados ao montar o componente
onMounted(async () => {
  try {
    // Carrega os leitos
    const leitosData = await getLeitosFormatados();
    leitos.value = leitosData;

    // Carrega as estatísticas
    const stats = await getEstatisticasLeitos();
    overviewCards.value = [
      { 
        title: 'Taxa de Ocupacao Global', 
        value: `${stats.taxaOcupacao}%`, 
        color: 'text-emerald-600', 
        caption: `${stats.ocupados} de ${stats.total - stats.desativados} leitos ocupados` 
      },
      { title: 'Leitos Disponiveis', value: String(stats.disponiveis), color: 'text-emerald-600' },
      { title: 'Leitos em Uso', value: String(stats.ocupados), color: 'text-emerald-600' },
      { title: 'Leitos em Higienizacao', value: String(stats.higienizacao), color: 'text-emerald-600' },
      { title: 'Leitos Desativados', value: String(stats.desativados), color: 'text-slate-400' },
      { title: 'Reservas Pendentes', value: String(stats.comReserva), color: 'text-emerald-600' },
    ];
  } catch (error) {
    toast.error('Erro ao carregar dados dos leitos.');
  }
});

const statusFilterOptions: { label: string; value: StatusFilter }[] = [
  { label: 'Todos', value: 'todos' },
  { label: 'Disponiveis', value: 'disponivel' },
  { label: 'Ocupados', value: 'ocupado' },
  { label: 'Higienizacao', value: 'higienizacao' },
  { label: 'Desativados', value: 'desativado' },
  { label: 'Alta', value: 'alta' },
];

const statusFilter = ref<StatusFilter>('todos');
const filtrosAbertos = ref(false);

const leitosFiltrados = computed(() => {
  if (statusFilter.value === 'todos') return leitos.value;
  return leitos.value.filter(leito => leito.status === statusFilter.value);
});

const setStatusFilter = (valor: StatusFilter) => {
  statusFilter.value = statusFilter.value === valor ? 'todos' : valor;
};

const toggleFiltros = () => {
  filtrosAbertos.value = !filtrosAbertos.value;
};

const dotColor = (valor: StatusFilter) => {
  switch (valor) {
    case 'disponivel':
      return 'bg-emerald-500';
    case 'ocupado':
      return 'bg-amber-500';
    case 'higienizacao':
      return 'bg-blue-500';
    case 'desativado':
      return 'bg-slate-400';
    case 'alta':
      return 'bg-fuchsia-500';
    default:
      return 'bg-slate-300';
  }
};

const handleSolicitarAlta = (leito: LeitoFormatado) => {
  toast.info(`Alta solicitada para o leito ${leito.leitoNumero}.`);
};

const handleCancelarAlta = (leito: LeitoFormatado) => {
  toast.warning(`Alta cancelada para o leito ${leito.leitoNumero}.`);
};

const handleCancelarReserva = (leito: LeitoFormatado) => {
  toast.error(`Reserva cancelada para o leito ${leito.leitoNumero}.`);
};
</script>

<style scoped>
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.18s ease;
}
.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
