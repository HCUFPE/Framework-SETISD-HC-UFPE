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

    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-4">
      <Card v-for="card in statusCards" :key="card.label">
        <p class="text-sm text-gray-500">{{ card.label }}</p>
        <p class="text-3xl font-bold text-lab-text mt-1">{{ card.count }}</p>
      </Card>
    </div>

    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-lab-text">Últimos exames movimentados</h2>
        <p class="text-sm text-gray-500">Tempo na etapa: atraso na fase atual. Tempo total: relógio do caso desde a entrada (meta: 20 dias).</p>
      </template>

      <DataTable :headers="headers" :items="examesComSla">
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
import { ref, computed, onMounted } from 'vue';
import { ExclamationTriangleIcon, ClockIcon } from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import DataTable from '../components/dataTable/dataTable.vue';
import Badge from '../components/badge/badge.vue';
import ExamDetailsModal from '../components/examDetailsModal/examDetailsModal.vue';
import { STATUS_COLOR, EXAM_STATUSES } from '../constants/statuses';
import { diasDesde, getSlaStatus, formatTempoTotal, type SlaStatus } from '../utils/sla';
import type { ExamCaseDetail } from '../types/exam';
import { exameService, mapExameDetalhe } from '../services/exameService';

const headers = [
  { text: 'Solicitação', value: 'solicitacao' },
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

// Listagem carregada do backend (banco populado via seed_dados.py).
// Endpoint GET /api/exames/dashboard — mesma estrutura do mock anterior.
interface ExameDashboardItem {
  id: string;
  solicitacao: string;
  paciente: string;
  etapa: string;
  tempoNaEtapa: string;
  atrasado: boolean;
  dataEntrada: Date;
}

const exames = ref<ExameDashboardItem[]>([]);

onMounted(async () => {
  const dados = await exameService.dashboard();
  exames.value = dados.map(e => ({
    id: e.id,
    solicitacao: e.solicitacao,
    paciente: e.paciente,
    etapa: e.etapa,
    // O endpoint do dashboard não expõe o instante de entrada na etapa atual,
    // apenas a data de entrada do caso — por isso o "tempo na etapa" fica neutro.
    tempoNaEtapa: '—',
    atrasado: e.atrasado,
    dataEntrada: new Date(e.data_entrada),
  }));
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

const examesEmAlerta = computed(() => examesComSla.value.filter(e => e.slaStatus !== 'ok'));
const qtdAtrasados = computed(() => examesComSla.value.filter(e => e.slaStatus === 'atrasado').length);
const qtdNoAlerta = computed(() => examesComSla.value.filter(e => e.slaStatus === 'alerta').length);
const temAtrasado = computed(() => qtdAtrasados.value > 0);

const statusCards = computed(() => {
  return EXAM_STATUSES.map(status => ({
    label: status,
    count: exames.value.filter(e => e.etapa === status).length,
  }));
});
</script>