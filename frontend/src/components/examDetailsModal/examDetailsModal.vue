<template>
  <div v-if="show" class="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true">
    <div class="absolute inset-0 overflow-hidden">

      <div
        class="absolute inset-0 bg-lab-sidebar/40 backdrop-blur-xs transition-opacity duration-200"
        @click="$emit('close')"
      ></div>

      <div class="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div class="pointer-events-auto w-screen max-w-xl md:max-w-2xl lg:max-w-3xl transform bg-lab-bg shadow-2xl flex flex-col h-full border-l border-gray-200 transition-all">

          <div class="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 class="text-base font-bold text-lab-text tracking-tight">Visão Unificada do Caso</h2>
              <p class="text-xs text-gray-400">Dados estruturados do fluxo laboratorial</p>
            </div>
            <button
              @click="$emit('close')"
              class="rounded-md text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 transition-colors focus:outline-none"
            >
              <span class="sr-only">Fechar</span>
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="flex-1 overflow-y-auto p-6 space-y-5">
            <div v-if="detalhe" class="space-y-5">

              <PatientExamHeader
                :codigo-local="detalhe.codigoLocal"
                :aghu="detalhe.aghu"
                :etapa-atual="detalhe.etapaAtual"
                :urgente="detalhe.urgente"
              />

              <div v-if="recepcaoFields.length" class="bg-white border border-gray-200 rounded-md p-5 shadow-xs">
                <div class="flex items-center gap-2 mb-4 border-b border-gray-100 pb-2">
                  <span class="w-1.5 h-3.5 bg-lab-info rounded-xs"></span>
                  <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">1. Recepção</h3>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                  <div v-for="f in recepcaoFields" :key="f.label">
                    <span class="block text-[10px] font-bold text-gray-400 uppercase tracking-wide">{{ f.label }}</span>
                    <span class="text-gray-800 font-semibold block mt-1">{{ f.value }}</span>
                  </div>
                </div>
              </div>

              <div v-if="macroscopiaFields.length" class="bg-white border border-gray-200 rounded-md p-5 shadow-xs">
                <div class="flex items-center gap-2 mb-4 border-b border-gray-100 pb-2">
                  <span class="w-1.5 h-3.5 bg-lab-warning rounded-xs"></span>
                  <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">2. Macroscopia</h3>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs mb-3">
                  <div v-for="f in macroscopiaFields" :key="f.label">
                    <span class="block text-[10px] font-bold text-gray-400 uppercase tracking-wide">{{ f.label }}</span>
                    <span class="text-gray-800 font-semibold block mt-1">{{ f.value }}</span>
                  </div>
                </div>
                <div v-if="detalhe.macroscopia?.cassetes?.length" class="mt-4 pt-3 border-t border-gray-100">
                  <span class="block text-[10px] font-bold text-gray-400 uppercase tracking-wide mb-2">Cassetes Gerados</span>
                  <div class="flex flex-wrap gap-2">
                    <span
                      v-for="c in detalhe.macroscopia.cassetes"
                      :key="c.id"
                      class="text-xs font-mono font-semibold bg-gray-100 text-gray-700 px-2 py-1 rounded"
                      :title="c.estrutura"
                    >
                      {{ c.id }}
                    </span>
                  </div>
                </div>
              </div>

              <div v-if="processamentoFields.length" class="bg-white border border-gray-200 rounded-md p-5 shadow-xs">
                <div class="flex items-center gap-2 mb-4 border-b border-gray-100 pb-2">
                  <span class="w-1.5 h-3.5 bg-lab-primary rounded-xs"></span>
                  <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">3. Processamento Técnico</h3>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                  <div v-for="f in processamentoFields" :key="f.label">
                    <span class="block text-[10px] font-bold text-gray-400 uppercase tracking-wide">{{ f.label }}</span>
                    <span class="text-gray-800 font-semibold block mt-1">{{ f.value }}</span>
                  </div>
                </div>
              </div>

              <div v-if="microscopiaFields.length" class="bg-white border border-gray-200 rounded-md p-5 shadow-xs">
                <div class="flex items-center gap-2 mb-4 border-b border-gray-100 pb-2">
                  <span class="w-1.5 h-3.5 bg-lab-success rounded-xs"></span>
                  <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider">4. Microscopia & Diagnóstico</h3>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs mb-3">
                  <div v-for="f in microscopiaFields" :key="f.label">
                    <span class="block text-[10px] font-bold text-gray-400 uppercase tracking-wide">{{ f.label }}</span>
                    <span class="text-gray-800 font-semibold block mt-1">{{ f.value }}</span>
                  </div>
                </div>
                <div v-if="detalhe.microscopia?.laudo" class="mt-4 pt-3 border-t border-gray-100">
                  <span class="block text-[10px] font-bold text-green-800 uppercase tracking-wide mb-1.5">Conclusão / Laudo Liberado</span>
                  <p class="text-xs text-gray-900 bg-green-50 border border-green-100 rounded p-3 font-mono font-bold leading-relaxed whitespace-pre-wrap">
                    {{ detalhe.microscopia.laudo }}
                  </p>
                </div>
              </div>

            </div>
          </div>

          <div class="px-6 py-3.5 bg-white border-t border-gray-200 flex justify-end">
            <button
              type="button"
              @click="$emit('close')"
              class="px-4 py-2 text-xs font-bold uppercase tracking-wider text-gray-700 bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 transition-colors focus:outline-none"
            >
              Fechar Detalhes
            </button>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PatientExamHeader from '../patientExamHeader/patientExamHeader.vue';
import { formatDateShort } from '../../utils/date';
import type { ExamCaseDetail } from '../../types/exam';

const props = defineProps<{
  show: boolean;
  detalhe: ExamCaseDetail | null;
}>();

defineEmits<{ close: [] }>();

const recepcaoFields = computed(() => {
  const r = props.detalhe?.recepcao;
  if (!r) return [];
  return [
    { label: 'Data de Entrada', value: formatDateShort(r.dataEntrada) },
    { label: 'Qtd. Frascos', value: String(r.quantidadeFrascos) },
    { label: 'Responsável', value: r.responsavel },
  ];
});

const macroscopiaFields = computed(() => {
  const m = props.detalhe?.macroscopia;
  if (!m) return [];
  return [
    { label: 'Data da Macro', value: formatDateShort(m.dataMacro) },
    { label: 'Responsável', value: m.responsavel },
    { label: 'Cassetes Gerados', value: String(m.cassetes.length) },
    { label: 'Sobra de Material', value: m.sobraMaterial ? 'Sim' : 'Não' },
  ];
});

const processamentoFields = computed(() => {
  const p = props.detalhe?.processamentoTecnico;
  if (!p) return [];
  const fields = [
    { label: 'Blocos Gerados', value: String(p.blocos.length) },
    { label: 'Lâminas Geradas', value: String(p.laminas.length) },
    { label: 'Liberado Em', value: formatDateShort(p.dataLiberacao) },
    { label: 'Responsável', value: p.responsavelLiberacao ?? '—' },
  ];
  if (p.materialComplementarDataSaida) {
    fields.push({ label: 'Complemento em', value: formatDateShort(p.materialComplementarDataSaida) });
  }
  return fields;
});

const microscopiaFields = computed(() => {
  const mi = props.detalhe?.microscopia;
  if (!mi) return [];
  const fields = [
    { label: 'Recebido Em', value: formatDateShort(mi.dataRecebimento) },
    { label: 'Complemento Solicitado', value: mi.solicitouComplemento ? 'Sim' : 'Não' },
  ];
  if (mi.dataLiberacaoLaudo) {
    fields.push({ label: 'Laudo Assinado Em', value: formatDateShort(mi.dataLiberacaoLaudo) });
  }
  if (mi.responsavelLiberacao) {
    fields.push({ label: 'Patologista Resp.', value: mi.responsavelLiberacao });
  }
  return fields;
});
</script>