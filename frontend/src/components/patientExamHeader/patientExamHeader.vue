<template>
  <div class="bg-white border border-gray-200 rounded-md p-5 shadow-xs">
    <!-- Linha Superior: Código, Nome e Badges -->
    <div class="flex items-start justify-between gap-4 border-b border-gray-100 pb-4">
      <div>
        <span class="font-mono text-xs font-bold text-gray-500 bg-gray-100 px-2 py-0.5 rounded-sm">
          {{ codigoLocal }}
        </span>
        <h1 class="text-xl font-bold text-lab-text mt-2 tracking-tight">{{ aghu.nomePaciente }}</h1>
        <div class="flex items-center gap-3 text-xs text-gray-500 mt-1 font-medium">
          <span>Prontuário: <strong class="text-gray-700">{{ aghu.prontuario }}</strong></span>
          <span class="text-gray-300">•</span>
          <span>Idade: <strong class="text-gray-700">{{ aghu.idade }} anos</strong></span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <Badge v-if="urgente" color="red">Urgente</Badge>
        <Badge :color="STATUS_COLOR[etapaAtual]">{{ etapaAtual }}</Badge>
      </div>
    </div>

    <!-- Info do AGHU organizada em Grid Espaçado -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-xs">
      <div>
        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Origem / Clínica</p>
        <p class="text-gray-800 font-semibold mt-1">{{ aghu.origem }}{{ aghu.clinica ? ` · ${aghu.clinica}` : '' }}</p>
      </div>
      <div>
        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Tipo de Exame</p>
        <p class="text-gray-800 font-semibold mt-1">{{ EXAM_TYPE_LABEL[aghu.tipoExame] || aghu.tipoExame }}</p>
      </div>
      <div>
        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Nº Solicitação AGHU</p>
        <p class="text-gray-800 font-mono font-bold mt-1">{{ aghu.numeroSolicitacaoAghu }}</p>
      </div>

      <div class="sm:col-span-3 border-t border-gray-50 pt-2">
        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Procedimento (SUS)</p>
        <p class="text-gray-800 font-medium mt-0.5">{{ aghu.procedimentoSus }}</p>
      </div>

      <!-- Blocos de Texto com Destaque de Fundo Leve para não misturar -->
      <div class="sm:col-span-3 space-y-3 pt-1">
        <div class="bg-gray-50 border border-gray-100 p-3 rounded-sm">
          <p class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Material (AGHU)</p>
          <p class="text-gray-800 font-medium mt-1 text-xs">{{ aghu.tipoMaterial || 'Não informado pelo médico solicitante.' }}</p>
        </div>

        <div class="bg-amber-50 border border-amber-100 p-3 rounded-sm">
          <p class="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Indicação Clínica</p>
          <p class="text-gray-800 mt-1 text-xs leading-relaxed font-sans">{{ aghu.indicacaoClinica || 'Sem indicação cadastrada.' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Badge from '../badge/badge.vue';
import { STATUS_COLOR } from '../../constants/statuses';
import { EXAM_TYPE_LABEL } from '../../constants/examTypes';
import type { AghuData } from '../../types/exam';
import type { ExamStatus } from '../../constants/statuses';

defineProps<{
  codigoLocal: string;
  aghu: AghuData;
  etapaAtual: ExamStatus;
  urgente?: boolean;
}>();
</script>