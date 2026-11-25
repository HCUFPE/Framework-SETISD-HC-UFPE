<template>
  <span :class="classes" class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold">
    {{ texto }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ quantidade: number }>();

const classes = computed(() => (props.quantidade > 0
  ? 'bg-red-100 text-red-700'
  : 'bg-emerald-100 text-emerald-700'));

const texto = computed(() => (props.quantidade > 0
  ? `${props.quantidade} divergência${props.quantidade > 1 ? 's' : ''}`
  : 'Sem divergências'));
</script>
