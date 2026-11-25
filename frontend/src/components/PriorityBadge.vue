<template>
  <span :class="classes" class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold">
    {{ texto }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Prioridade } from '../types/sae';

const props = defineProps<{ prioridade: Prioridade }>();

const classes = computed(() => ({
  ALTA: 'bg-red-100 text-red-700',
  MEDIA: 'bg-amber-100 text-amber-700',
  BAIXA: 'bg-emerald-100 text-emerald-700',
}[props.prioridade]));

const texto = computed(() => ({
  ALTA: 'Alta',
  MEDIA: 'Média',
  BAIXA: 'Baixa',
}[props.prioridade]));
</script>
