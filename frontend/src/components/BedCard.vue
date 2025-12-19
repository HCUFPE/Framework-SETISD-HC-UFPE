<template>
  <article
    class="relative rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
    :class="sinalizacaoTransferencia ? 'ring-2 ring-red-300' : ''"
  >
    <div
      v-if="sinalizacaoTransferencia"
      class="absolute -top-2 -right-2 rounded-full bg-red-100 p-2 text-red-600 shadow"
      title="Alerta de transferencia"
    >
      <ExclamationTriangleIcon class="h-4 w-4" />
    </div>

    <div class="flex items-start justify-between gap-3">
      <div class="space-y-2">
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest text-slate-500">Leito</p>
          <h3 class="text-2xl font-bold text-slate-900">Leito {{ leitoNumero }}</h3>
        </div>
        <UiBadge :class="['border-transparent text-white', tipoClass]">
          {{ tipoConfig.label }}
        </UiBadge>
      </div>

      <StatusBadge :status="status" />
    </div>

    <div class="mt-4 space-y-4 text-sm text-slate-700">
      <div v-if="pacienteAtual" class="space-y-1 border-l-4 border-blue-500 pl-4">
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-500">Paciente Atual</p>
        <p class="text-base font-bold text-slate-900">Prontuario: {{ pacienteAtual.prontuario }}</p>
        <p class="text-slate-600">{{ pacienteAtual.idade }} anos - {{ pacienteAtual.especialidade }}</p>
      </div>

      <div v-if="proximoPaciente" class="space-y-1 border-l-4 border-emerald-500 pl-4">
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-500">Proximo Paciente</p>
        <p class="text-base font-bold text-slate-900">Prontuario: {{ proximoPaciente.prontuario }}</p>
        <p class="text-slate-600">{{ proximoPaciente.idade }} anos - {{ proximoPaciente.especialidade }}</p>
        <UiBadge
          v-if="tipoReserva"
          variant="outline"
          class="border-emerald-200 bg-emerald-50 text-emerald-700"
        >
          {{ tipoReserva }}
        </UiBadge>
      </div>

      <p v-else class="pl-4 text-slate-500">Sem reserva</p>
    </div>

    <div v-if="true" class="mt-5 flex gap-2">
      <button
        v-if="status === 'ocupado'"
        class="inline-flex flex-1 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
        @click="$emit('solicitar-alta')"
      >
        Solicitar Alta
      </button>
      <button
        v-if="status === 'alta'"
        class="inline-flex flex-1 items-center justify-center rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-100"
        @click="$emit('cancelar-alta')"
      >
        Cancelar Alta
      </button>
      <button
        v-if="proximoPaciente"
        class="inline-flex flex-1 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
        @click="$emit('cancelar-reserva')"
      >
        Cancelar Reserva
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import StatusBadge from './StatusBadge.vue';
import UiBadge from './ui/Badge.vue';

type BedStatus = 'disponivel' | 'ocupado' | 'higienizacao' | 'desativado' | 'alta';
type BedType = 'cirurgico' | 'hem' | 'obstetrico' | 'outro' | 'nao_definido';

type Patient = {
  prontuario: string;
  idade: number;
  especialidade: string;
};

const props = defineProps<{
  leitoNumero: string;
  status: BedStatus;
  tipo: BedType;
  pacienteAtual?: Patient;
  proximoPaciente?: Patient;
  tipoReserva?: string;
  sinalizacaoTransferencia?: boolean;
  showActions?: boolean;
}>();

defineEmits<{
  'solicitar-alta': [];
  'cancelar-alta': [];
  'cancelar-reserva': [];
}>();

const tipoPalette: Record<BedType, { label: string; className: string }> = {
  cirurgico: { label: 'Cirúrgico', className: 'bg-blue-600/80' },
  hem: { label: 'HEM', className: 'bg-rose-600/80' },
  obstetrico: { label: 'Obstétrico', className: 'bg-purple-600/80' },
  outro: { label: 'Outro', className: 'bg-slate-700/80' },
  nao_definido: { label: 'Não definido', className: 'bg-slate-400/90' },
};

const tipoConfig = computed(() => tipoPalette[props.tipo]);
const tipoClass = computed(() => tipoConfig.value.className);
</script>
