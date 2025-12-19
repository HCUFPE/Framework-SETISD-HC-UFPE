<template>
  <span
    :class="[
      'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
      variantClass,
    ]"
  >
    <slot/>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type Variant = 'default' | 'secondary' | 'destructive' | 'outline';

const props = defineProps<{
  variant?: Variant;
}>();

const variantClass = computed(() => {
  switch (props.variant) {
    case 'secondary':
      return 'border-transparent bg-slate-100 text-slate-800 hover:bg-slate-200';
    case 'destructive':
      return 'border-transparent bg-red-600 text-white hover:bg-red-700';
    case 'outline':
      return 'text-slate-800 border-slate-200';
    case 'default':
    default:
      return 'border-transparent bg-blue-600 text-white hover:bg-blue-700';
  }
});
</script>
