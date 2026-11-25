<template>
  <div class="bg-white rounded-lg shadow-paper p-5 border-l-4" :class="borda">
    <p class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ titulo }}</p>
    <p class="mt-2 text-3xl font-bold text-paper-text">{{ valor }}</p>
    <p class="mt-1 text-xs text-gray-500">{{ detalhe }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  titulo: string;
  valor: string | number;
  detalhe?: string;
  cor?: 'primary' | 'info' | 'success' | 'warning';
}>(), { detalhe: '', cor: 'primary' });

const borda = computed(() => ({
  primary: 'border-paper-primary',
  info: 'border-paper-info',
  success: 'border-paper-success',
  warning: 'border-paper-warning',
}[props.cor]));
</script>
