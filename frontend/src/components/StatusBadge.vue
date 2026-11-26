<template>
  <span :class="classes" class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold">
    {{ ROTULOS_STATUS[status] }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ROTULOS_STATUS, type StatusSolicitacao } from '../types/sae';

const props = defineProps<{ status: StatusSolicitacao }>();

const classes = computed(() => ({
  RECEBIDA: 'bg-slate-100 text-slate-700',
  PENDENTE_CORRECAO: 'bg-amber-100 text-amber-700',
  AGUARDANDO_CONTATO: 'bg-indigo-100 text-indigo-700',
  AGUARDANDO_CONFIRMACAO: 'bg-sky-100 text-sky-700',
  AGUARDANDO_REAGENDAMENTO: 'bg-orange-100 text-orange-700',
  AGENDADA: 'bg-emerald-100 text-emerald-700',
  CANCELADA: 'bg-gray-200 text-gray-600',
  NAO_CONFIRMADO: 'bg-rose-100 text-rose-700',
}[props.status]));
</script>
