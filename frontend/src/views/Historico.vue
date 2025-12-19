<template>
  <section class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-3xl font-bold text-slate-900">Historico de Acoes</h2>
    </div>

    <article class="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div class="px-5 py-4">
        <div class="flex flex-wrap gap-2">
          <div class="relative flex-1 min-w-60">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              v-model="busca"
              type="text"
              placeholder="Buscar por prontuario, operador ou acao..."
              class="w-full rounded-md border border-slate-200 bg-white px-10 py-2 text-sm text-slate-800 shadow-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              @keyup.enter="onSearch"
            />
          </div>
          <UiButton class="h-10" @click="onSearch">Buscar</UiButton>
        </div>
      </div>
    </article>

    <div class="space-y-3">
      <article
        v-for="item in historicoFiltrado"
        :key="item.id"
        class="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <div class="p-4">
          <div class="flex items-start justify-between">
            <div class="flex-1 space-y-2">
              <div class="flex flex-wrap items-center gap-3">
                <UiBadge :class="tipoConfig[item.tipo].color">
                  {{ tipoConfig[item.tipo].label }}
                </UiBadge>
                <h3 class="font-semibold text-slate-900">{{ item.acao }}</h3>
              </div>
              <p class="text-sm text-slate-600">{{ item.detalhes }}</p>
              <div class="flex flex-wrap items-center gap-4 pt-2 text-xs text-slate-500">
                <div class="flex items-center gap-1">
                  <UserIcon class="h-3 w-3" />
                  <span>{{ item.operador }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <ClockIcon class="h-3 w-3" />
                  <span>{{ item.dataHora }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { MagnifyingGlassIcon, UserIcon, ClockIcon } from '@heroicons/vue/24/outline';
import { computed, ref } from 'vue';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';

type HistoricoItem = {
  id: string;
  operador: string;
  acao: string;
  detalhes: string;
  dataHora: string;
  tipo: keyof typeof tipoConfig;
};

const historico = ref<HistoricoItem[]>([
  {
    id: '1',
    operador: 'Dr. Silva',
    acao: 'Solicitou alta',
    detalhes: 'Leito 03 - Prontuario 456789',
    dataHora: '2025-11-18 15:30',
    tipo: 'alta',
  },
  {
    id: '2',
    operador: 'Enf. Santos',
    acao: 'Reservou leito',
    detalhes: 'Leito 05 para Prontuario 789012',
    dataHora: '2025-11-18 14:45',
    tipo: 'reserva',
  },
  {
    id: '3',
    operador: 'NIR - Maria',
    acao: 'Definiu destino',
    detalhes: 'Prontuario 234567 -> Enfermaria 2B Leito 12',
    dataHora: '2025-11-18 14:20',
    tipo: 'destino',
  },
  {
    id: '4',
    operador: 'Dr. Costa',
    acao: 'Cancelou solicitacao',
    detalhes: 'Prontuario 567890 - Paciente estavel',
    dataHora: '2025-11-18 13:15',
    tipo: 'cancelamento',
  },
  {
    id: '5',
    operador: 'BC - Joao',
    acao: 'Nova solicitacao',
    detalhes: 'Vaga cirurgica - Prontuario 123456',
    dataHora: '2025-11-18 13:00',
    tipo: 'solicitacao',
  },
  {
    id: '6',
    operador: 'Enf. Lima',
    acao: 'Atualizou status',
    detalhes: 'Leito 08 - Higienizacao concluida',
    dataHora: '2025-11-18 12:30',
    tipo: 'status',
  },
]);

const tipoConfig: Record<
  string,
  {
    color: string;
    label: string;
  }
> = {
  alta: { color: 'border border-rose-300 bg-rose-500/80 text-rose-100', label: 'Alta' },
  reserva: { color: 'border border-emerald-300 bg-emerald-500/80 text-emerald-100', label: 'Reserva' },
  destino: { color: 'border border-blue-300 bg-blue-500/80 text-blue-100', label: 'Destino' },
  cancelamento: { color: 'border border-red-300 bg-red-500/80 text-red-100', label: 'Cancelamento' },
  solicitacao: { color: 'border border-amber-300 bg-amber-500/80 text-amber-800', label: 'Solicitacao' },
  status: { color: 'border border-slate-300 bg-slate-500/80 text-slate-100', label: 'Status' },
};

const busca = ref('');

const historicoFiltrado = computed(() => {
  const termo = busca.value.trim().toLowerCase();
  if (!termo) return historico.value;

  return historico.value.filter(item => {
    return (
      item.operador.toLowerCase().includes(termo) ||
      item.acao.toLowerCase().includes(termo) ||
      item.detalhes.toLowerCase().includes(termo) ||
      item.dataHora.toLowerCase().includes(termo)
    );
  });
});

const onSearch = () => {
  busca.value = busca.value.trimStart();
};
</script>
