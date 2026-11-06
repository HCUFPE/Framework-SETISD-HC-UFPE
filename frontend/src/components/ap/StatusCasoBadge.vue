<template>
  <Badge :variant="STATUS_CASO[status].variante" :size="size">{{ STATUS_CASO[status].rotulo }}</Badge>
</template>

<script setup lang="ts">
import Badge from '../Badge.vue';
import { STATUS_CASO } from '../../constants/ap';
import type { StatusCaso } from '../../types/ap';

/** Selo do status do caso, com a cor da categoria. */
withDefaults(defineProps<{ status: StatusCaso; size?: 'sm' | 'md' }>(), { size: 'sm' });
</script>
