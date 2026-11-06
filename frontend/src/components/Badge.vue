<template>
  <span :class="[variantClass, sizeClass]" class="inline-flex items-center rounded-md font-bold whitespace-nowrap">
    <slot></slot>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export type BadgeVariant = 'default' | 'primary' | 'info' | 'success' | 'warning' | 'danger';

const props = withDefaults(
  defineProps<{
    variant?: BadgeVariant;
    size?: 'sm' | 'md';
  }>(),
  { variant: 'default', size: 'md' },
);

/** Pares de fundo claro e texto escuro, com contraste AA em todas as variantes. */
const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-paper-default',
  primary: 'bg-paper-primary-soft text-paper-primary-strong',
  info: 'bg-paper-info-soft text-paper-info-strong',
  success: 'bg-paper-success-soft text-paper-success-strong',
  warning: 'bg-paper-warning-soft text-paper-warning-strong',
  danger: 'bg-paper-danger-soft text-paper-danger-strong',
};

const variantClass = computed(() => VARIANT_CLASSES[props.variant]);

const sizeClass = computed(() => (props.size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-xs'));
</script>
