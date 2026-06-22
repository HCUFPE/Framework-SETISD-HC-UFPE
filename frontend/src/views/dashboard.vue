<template>
  <div class="space-y-6">
    <div
      v-if="examesEmAlerta.length > 0"
      class="flex items-start gap-3 p-4 rounded-lg"
      :class="temAtrasado ? 'bg-red-50 border border-red-200' : 'bg-amber-50 border border-amber-200'"
    >
      <ExclamationTriangleIcon class="h-6 w-6 shrink-0" :class="temAtrasado ? 'text-red-600' : 'text-amber-600'" />
      <div>
        <p class="font-semibold" :class="temAtrasado ? 'text-red-700' : 'text-amber-700'">
          {{ temAtrasado ? 'Exames fora do prazo de 20 dias' : 'Exames se aproximando do prazo de 20 dias' }}
        </p>
        <p class="text-sm mt-0.5" :class="temAtrasado ? 'text-red-600' : 'text-amber-600'">
          {{ qtdAtrasados }} atrasado(s) e {{ qtdNoAlerta }} próximo(s) do limite. Meta da UACAP: liberação em até 20 dias.
        </p>
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
      </DataTable>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ExclamationTriangleIcon, ClockIcon } from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import DataTable from '../components/dataTable/dataTable.vue';
import Badge from '../components/badge/badge.vue';
import { formatExamCode, deriveExamCode } from '../utils/examCode';
import { STATUS_COLOR, EXAM_STATUSES } from '../constants/statuses';
import { diasDesde, getSlaStatus, formatTempoTotal, type SlaStatus } from '../utils/sla';

const headers = [
  { text: 'Solicitação', value: 'solicitacao' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Etapa', value: 'etapa' },
  { text: 'Tempo na etapa', value: 'tempoNaEtapa' },
  { text: 'Tempo total', value: 'tempoTotal' },
];

const TEMPO_TOTAL_CLASS: Record<SlaStatus, string> = {
  ok: 'text-gray-500',
  alerta: 'text-amber-600 font-medium',
  atrasado: 'text-red-600 font-medium',
};

function diasAtras(n: number): Date {
  const data = new Date();
  data.setDate(data.getDate() - n);
  return data;
}

// mocks — dataEntrada simula quando o caso entrou no sistema (Recepção)
const exames = [
  { id: 1, solicitacao: formatExamCode('HP', 1002, 2026, 1), paciente: 'João Batista Oliveira', etapa: 'Liberado', tempoNaEtapa: 'agora', atrasado: false, dataEntrada: diasAtras(3) },
  { id: 2, solicitacao: formatExamCode('HP', 1003, 2026, 1), paciente: 'Ana Carolina Souza', etapa: 'Liberado', tempoNaEtapa: 'agora', atrasado: false, dataEntrada: diasAtras(5) },
  { id: 3, solicitacao: formatExamCode('HP', 1006, 2026, 1), paciente: 'Maria Aparecida Silva', etapa: 'Em Processamento', tempoNaEtapa: 'agora', atrasado: false, dataEntrada: diasAtras(9) },
  { id: 4, solicitacao: formatExamCode('HP', 1001, 2026, 1), paciente: 'Maria Aparecida Silva', etapa: 'Em Macroscopia', tempoNaEtapa: 'agora', atrasado: false, dataEntrada: diasAtras(1) },
  { id: 5, solicitacao: deriveExamCode(1001, 2026, 1, 'IHQ'), paciente: 'Maria Aparecida Silva', etapa: 'Em Macroscopia', tempoNaEtapa: 'agora', atrasado: false, dataEntrada: diasAtras(1) },
  { id: 6, solicitacao: formatExamCode('HP', 1005, 2026, 1), paciente: 'Beatriz Helena Costa', etapa: 'Na Recepção', tempoNaEtapa: '2h', atrasado: false, dataEntrada: diasAtras(0) },
  { id: 7, solicitacao: formatExamCode('HP', 1009, 2026, 1), paciente: 'João Batista Oliveira', etapa: 'Liberado', tempoNaEtapa: '5h', atrasado: false, dataEntrada: diasAtras(12) },
  { id: 8, solicitacao: formatExamCode('HP', 1007, 2026, 1), paciente: 'Ana Carolina Souza', etapa: 'Em Processamento', tempoNaEtapa: '8h', atrasado: false, dataEntrada: diasAtras(17) },
  { id: 9, solicitacao: formatExamCode('HP', 1004, 2026, 1), paciente: 'Carlos Eduardo Lima', etapa: 'Revisão Pendente', tempoNaEtapa: '5d 0h', atrasado: true, dataEntrada: diasAtras(23) },
  { id: 10, solicitacao: formatExamCode('IHQ', 1010, 2026, 1), paciente: 'Rafael Costa', etapa: 'Em Microscopia', tempoNaEtapa: '1h', atrasado: false, dataEntrada: diasAtras(18) },
  { id: 11, solicitacao: formatExamCode('Congela', 1011, 2026, 1), paciente: 'Beatriz Andrade', etapa: 'Em Congelamento', tempoNaEtapa: '15min', atrasado: false, dataEntrada: diasAtras(0) },
];

const examesComSla = computed(() => {
  return exames.map(exame => {
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
    count: exames.filter(e => e.etapa === status).length,
  }));
});
</script>