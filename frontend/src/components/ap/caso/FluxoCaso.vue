<template>
  <nav aria-label="Etapas do fluxo do caso">
    <ol class="flex flex-wrap items-start gap-y-3">
      <li
        v-for="(etapa, i) in etapas"
        :key="etapa.codigo"
        :aria-current="etapa.estado === 'atual' || etapa.estado === 'interrompida' ? 'step' : undefined"
        class="flex items-start"
      >
        <div class="flex w-28 flex-col items-center text-center">
          <span
            :class="classesCirculo[etapa.estado]"
            class="flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-bold"
          >
            <CheckIcon v-if="etapa.estado === 'concluida'" class="h-4 w-4" aria-hidden="true" />
            <XMarkIcon v-else-if="etapa.estado === 'interrompida'" class="h-4 w-4" aria-hidden="true" />
            <span v-else aria-hidden="true">{{ i + 1 }}</span>
          </span>
          <span :class="classesRotulo[etapa.estado]" class="mt-1.5 text-xs leading-tight">{{ ETAPAS[etapa.codigo] }}</span>
          <span v-if="etapa.detalhe" class="mt-0.5 text-[11px] font-semibold leading-tight" :class="classesDetalhe[etapa.estado]">
            {{ etapa.detalhe }}
          </span>
          <span class="sr-only">({{ textoEstado[etapa.estado] }})</span>
        </div>
        <span
          v-if="i < etapas.length - 1"
          :class="etapa.estado === 'concluida' ? 'bg-paper-success' : 'bg-gray-300'"
          class="mt-4 h-0.5 w-6 shrink-0 rounded"
          aria-hidden="true"
        ></span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { CheckIcon, XMarkIcon } from '@heroicons/vue/24/outline';
import { ETAPAS, STATUS_CASO, fluxoDoCaso } from '../../../constants/ap';
import type { CasoAp, EtapaCodigo } from '../../../types/ap';

type Estado = 'concluida' | 'atual' | 'futura' | 'interrompida';

const props = defineProps<{ caso: CasoAp }>();

const classesCirculo: Record<Estado, string> = {
  concluida: 'border-paper-success bg-paper-success text-white',
  atual: 'border-paper-primary bg-paper-primary text-white ring-4 ring-paper-primary-soft',
  futura: 'border-gray-300 bg-white text-gray-400',
  interrompida: 'border-paper-danger bg-paper-danger-soft text-paper-danger-strong',
};
const classesRotulo: Record<Estado, string> = {
  concluida: 'font-semibold text-paper-success-strong',
  atual: 'font-bold text-gray-900',
  futura: 'text-gray-400',
  interrompida: 'font-bold text-paper-danger-strong',
};
const classesDetalhe: Record<Estado, string> = {
  concluida: 'text-paper-success-strong',
  atual: 'text-paper-primary-strong',
  futura: 'text-gray-400',
  interrompida: 'text-paper-danger-strong',
};
const textoEstado: Record<Estado, string> = {
  concluida: 'concluída',
  atual: 'etapa atual',
  futura: 'futura',
  interrompida: 'interrompida',
};

/** Etapas do fluxo do tipo com o estado de cada uma conforme a etapa atual e o status do caso. */
const etapas = computed(() => {
  const caso = props.caso;
  const fluxo = fluxoDoCaso(caso.tipoExame, caso.ihqs.length > 0);
  const atual = caso.etapaAtual === null ? fluxo.length : fluxo.indexOf(caso.etapaAtual);
  const interrompido = caso.status === 'DEVOLVIDO' || caso.status === 'CANCELADO';
  const aguardando = caso.status === 'RECEBIDO' || caso.status === 'LAUDO_CONCLUIDO';

  return fluxo.map((codigo: EtapaCodigo, i): { codigo: EtapaCodigo; estado: Estado; detalhe?: string } => {
    if (i < atual) return { codigo, estado: 'concluida' };
    if (i > atual) return { codigo, estado: 'futura' };
    if (interrompido) return { codigo, estado: 'interrompida', detalhe: STATUS_CASO[caso.status].rotulo };
    return { codigo, estado: 'atual', detalhe: aguardando ? 'Aguardando chegada' : 'Em andamento' };
  });
});
</script>
