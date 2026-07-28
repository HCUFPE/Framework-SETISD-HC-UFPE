<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-if="qtdAtrasados > 0"
        class="flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200"
      >
        <ExclamationTriangleIcon class="h-6 w-6 shrink-0 text-red-600" />
        <div>
          <p class="font-semibold text-red-700">
            Exames fora da meta de 20 dias
          </p>
          <p class="text-sm mt-0.5 text-red-600">
            Há {{ qtdAtrasados }} caso(s) que excederam o prazo máximo estabelecido pela UACAP.
          </p>
        </div>
      </div>

      <div
        v-if="qtdNoAlerta > 0"
        class="flex items-start gap-3 p-4 rounded-lg bg-amber-50 border border-amber-200"
      >
        <ClockIcon class="h-6 w-6 shrink-0 text-amber-600" />
        <div>
          <p class="font-semibold text-amber-700">
            Exames próximos da meta de 20 dias
          </p>
          <p class="text-sm mt-0.5 text-amber-600">
            Há {{ qtdNoAlerta }} caso(s) na zona de alerta precisando de atenção para não estourar o prazo.
          </p>
        </div>
      </div>
    </div>

    <!-- Cards de Status por Etapa -->
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-4">
      <div
        v-for="card in statusCards"
        :key="card.label"
        @click="selecionarEtapaCard(card.label)"
        class="cursor-pointer transition-all duration-200"
      >
        <Card
          :class="[
            'h-full border hover:shadow-md transition-all',
            filtroEtapa === card.label ? 'border-[#173f42] ring-2 ring-[#173f42]/20 bg-teal-50/40' : 'border-gray-200'
          ]"
        >
          <p class="text-xs font-medium text-gray-500 truncate" :title="card.label">{{ card.label }}</p>
          <p class="text-2xl font-bold text-lab-text mt-1">{{ card.count }}</p>
        </Card>
      </div>
    </div>

    <!-- Painel Principal de Exames com Filtros -->
    <Card>
      <template #header>
        <div class="space-y-4">
          <div>
            <h2 class="text-lg font-bold text-lab-text">Últimos exames movimentados</h2>
            <p class="text-sm text-gray-500">Tempo na etapa: atraso na fase atual. Tempo total: relógio do caso desde a entrada (meta: 20 dias).</p>
          </div>

          <!-- Barra de Filtros de Pesquisa -->
          <div class="p-4 bg-gray-50/80 rounded-lg border border-gray-200/80 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-sm font-semibold text-lab-text">
                <FunnelIcon class="h-4 w-4 text-[#173f42]" />
                <span>Filtros de Pesquisa</span>
              </div>
              <button
                v-if="temFiltroAtivo"
                @click="limparFiltros"
                class="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 transition-colors"
              >
                <XMarkIcon class="h-3.5 w-3.5" />
                Limpar filtros
              </button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <!-- Filtro: Nome do Paciente -->
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Nome do Paciente</label>
                <div class="relative">
                  <input
                    v-model="filtroNomePaciente"
                    type="text"
                    placeholder="Buscar por nome..."
                    class="w-full text-xs pl-8 pr-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-[#173f42] focus:border-[#173f42]"
                  />
                  <MagnifyingGlassIcon class="h-4 w-4 text-gray-400 absolute left-2.5 top-2.5" />
                </div>
              </div>

              <!-- Filtro: Código Interno -->
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Código Interno</label>
                <input
                  v-model="filtroCodigoInterno"
                  type="text"
                  placeholder="Ex: HP-0001/26.1"
                  class="w-full text-xs px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-[#173f42] focus:border-[#173f42]"
                />
              </div>

              <!-- Filtro: Código AGHU -->
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Código AGHU</label>
                <input
                  v-model="filtroCodigoAghu"
                  type="text"
                  placeholder="Ex: 123456"
                  class="w-full text-xs px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-[#173f42] focus:border-[#173f42]"
                />
              </div>

              <!-- Filtro: Etapa do Processo -->
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Etapa do Processo</label>
                <select
                  v-model="filtroEtapa"
                  class="w-full text-xs px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-[#173f42] focus:border-[#173f42]"
                >
                  <option value="">Todas as etapas</option>
                  <option v-for="status in EXAM_STATUSES" :key="status" :value="status">
                    {{ status }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </template>

      <DataTable :headers="headers" :items="examesComSla">
        <template #item-codigoAghu="{ item }">
          <span class="text-xs font-mono text-gray-600">{{ item.codigoAghu }}</span>
        </template>

        <template #item-etapa="{ item }">
          <Badge :color="STATUS_COLOR[item.etapa]">{{ item.etapa }}</Badge>
        </template>

        <template #item-tempoNaEtapa="{ item }">
          <span :class="item.atrasado ? 'text-red-600 font-medium' : 'text-gray-500'">
            {{ item.tempoNaEtapa }}
          </span>
        </template>

        <template #item-tempoTotal="{ item }">
          <span class="inline-flex items-center gap-1.5" :class="TEMPO_TOTAL_CLASS[item.slaStatus]">
            <ExclamationTriangleIcon v-if="item.slaStatus === 'atrasado'" class="h-4 w-4" />
            <ClockIcon v-else-if="item.slaStatus === 'alerta'" class="h-4 w-4" />
            {{ item.tempoTotalFormatado }}
          </span>
        </template>

        <template #actions="{ item }">
          <button
            @click="verDetalhes(item)"
            class="text-xs font-medium text-gray-500 hover:text-[#173f42] underline decoration-transparent hover:decoration-[#173f42] underline-offset-4 transition-all duration-200 focus:outline-none"
          >
            Ver detalhes
          </button>
        </template>
      </DataTable>
    </Card>

    <ExamDetailsModal
      :show="modalAberto"
      :detalhe="detalheSelecionado"
      @close="modalAberto = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import {
  ExclamationTriangleIcon,
  ClockIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import DataTable from '../components/dataTable/dataTable.vue';
import Badge from '../components/badge/badge.vue';
import ExamDetailsModal from '../components/examDetailsModal/examDetailsModal.vue';
import { STATUS_COLOR, EXAM_STATUSES } from '../constants/statuses';
import { diasDesde, getSlaStatus, formatTempoTotal, type SlaStatus } from '../utils/sla';
import type { ExamCaseDetail } from '../types/exam';
import { exameService, mapExameDetalhe, type DashboardFilterParams } from '../services/exameService';

const headers = [
  { text: 'Solicitação', value: 'solicitacao' },
  { text: 'Código AGHU', value: 'codigoAghu' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Etapa', value: 'etapa', align: 'center' },
  { text: 'Tempo na etapa', value: 'tempoNaEtapa', align: 'center' },
  { text: 'Tempo total', value: 'tempoTotal', align: 'center' },
];

const TEMPO_TOTAL_CLASS: Record<SlaStatus, string> = {
  ok: 'text-gray-500',
  alerta: 'text-amber-600 font-medium',
  atrasado: 'text-red-600 font-medium',
};

// Estado dos Filtros
const filtroNomePaciente = ref('');
const filtroCodigoInterno = ref('');
const filtroCodigoAghu = ref('');
const filtroEtapa = ref('');

const temFiltroAtivo = computed(() => {
  return (
    filtroNomePaciente.value.trim() !== '' ||
    filtroCodigoInterno.value.trim() !== '' ||
    filtroCodigoAghu.value.trim() !== '' ||
    filtroEtapa.value !== ''
  );
});

function limparFiltros() {
  filtroNomePaciente.value = '';
  filtroCodigoInterno.value = '';
  filtroCodigoAghu.value = '';
  filtroEtapa.value = '';
}

function selecionarEtapaCard(etapa: string) {
  if (filtroEtapa.value === etapa) {
    filtroEtapa.value = '';
  } else {
    filtroEtapa.value = etapa;
  }
}

// Controle de estado do modal
const modalAberto = ref(false);
const detalheSelecionado = ref<ExamCaseDetail | null>(null);

async function verDetalhes(item: any) {
  try {
    const d = await exameService.detalhe(item.id);
    detalheSelecionado.value = mapExameDetalhe(d);
    modalAberto.value = true;
  } catch {
    // O interceptor do axios já exibe o toast de erro.
  }
}

interface ExameDashboardItem {
  id: string;
  solicitacao: string;
  codigoAghu: string;
  paciente: string;
  etapa: string;
  tempoNaEtapa: string;
  atrasado: boolean;
  dataEntrada: Date;
}

const exames = ref<ExameDashboardItem[]>([]);
const todosExamesParaContagem = ref<ExameDashboardItem[]>([]);

async function carregarExames() {
  const params: DashboardFilterParams = {};
  if (filtroEtapa.value) params.etapa = filtroEtapa.value;
  if (filtroCodigoAghu.value.trim()) params.codigo_aghu = filtroCodigoAghu.value.trim();
  if (filtroCodigoInterno.value.trim()) params.codigo_interno = filtroCodigoInterno.value.trim();
  if (filtroNomePaciente.value.trim()) params.nome_paciente = filtroNomePaciente.value.trim();

  const dados = await exameService.dashboard(params);
  exames.value = dados.map(e => ({
    id: e.id,
    solicitacao: e.solicitacao,
    codigoAghu: e.codigo_aghu || '—',
    paciente: e.paciente,
    etapa: e.etapa,
    tempoNaEtapa: '—',
    atrasado: e.atrasado,
    dataEntrada: new Date(e.data_entrada),
  }));

  // Se não houver nenhum filtro aplicado, salva cópia para manter contagens globais nos cards
  if (!temFiltroAtivo.value) {
    todosExamesParaContagem.value = [...exames.value];
  }
}

// Reatividade com Debounce (300ms) para buscas textuais
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  [filtroNomePaciente, filtroCodigoInterno, filtroCodigoAghu],
  () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      carregarExames();
    }, 300);
  }
);

// Alteração de etapa é imediata
watch(filtroEtapa, () => {
  carregarExames();
});

onMounted(() => {
  carregarExames();
});

const examesComSla = computed(() => {
  return exames.value.map(exame => {
    const dias = diasDesde(exame.dataEntrada);
    const slaStatus = getSlaStatus(dias);
    return {
      ...exame,
      tempoTotalFormatado: formatTempoTotal(dias),
      slaStatus,
    };
  });
});

const qtdAtrasados = computed(() => examesComSla.value.filter(e => e.slaStatus === 'atrasado').length);
const qtdNoAlerta = computed(() => examesComSla.value.filter(e => e.slaStatus === 'alerta').length);

const statusCards = computed(() => {
  const listaBase = todosExamesParaContagem.value.length > 0 ? todosExamesParaContagem.value : exames.value;
  return EXAM_STATUSES.map(status => ({
    label: status,
    count: listaBase.filter(e => e.etapa === status).length,
  }));
});
</script>