<template>
  <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium" :class="colorClass">
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { BadgeColor } from '../../constants/statuses';

const props = defineProps({
  color: {
    type: String as () => BadgeColor,
    default: 'gray',
  },
});

const COLOR_CLASSES: Record<BadgeColor, string> = {
  gray: 'bg-gray-100 text-gray-600',
  blue: 'bg-blue-100 text-blue-700',
  purple: 'bg-purple-100 text-purple-700',
  orange: 'bg-orange-100 text-orange-700',
  green: 'bg-green-100 text-green-700',
};

const colorClass = computed(() => COLOR_CLASSES[props.color] || COLOR_CLASSES.gray);
</script>