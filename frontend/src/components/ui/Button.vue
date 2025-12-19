<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="[
      'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
      sizeClass,
      variantClass,
    ]"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type Variant = 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
type Size = 'default' | 'sm' | 'lg' | 'icon';

const props = defineProps<{
  variant?: Variant;
  size?: Size;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
}>();

const variantClass = computed(() => {
  switch (props.variant) {
    case 'destructive':
      return 'bg-red-600 text-white hover:bg-red-700';
    case 'outline':
      return 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50';
    case 'secondary':
      return 'bg-slate-100 text-slate-900 hover:bg-slate-200';
    case 'ghost':
      return 'text-slate-700 hover:bg-slate-100';
    case 'link':
      return 'text-blue-600 underline-offset-4 hover:underline';
    case 'default':
    default:
      return 'bg-blue-600 text-white hover:bg-blue-700';
  }
});

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-9 rounded-md px-3';
    case 'lg':
      return 'h-11 rounded-md px-8';
    case 'icon':
      return 'h-10 w-10';
    case 'default':
    default:
      return 'h-10 px-4 py-2';
  }
});
</script>
