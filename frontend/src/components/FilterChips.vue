<template>
  <div v-if="chips.length > 0" class="flex flex-wrap items-center gap-2" aria-label="Filtros ativos" role="group">
    <span
      v-for="chip in chips"
      :key="chip.key"
      class="inline-flex items-center gap-1 rounded-full border border-paper-primary/40 bg-paper-primary-soft py-1 pl-3 pr-1 text-xs font-semibold text-paper-primary-strong"
    >
      {{ chip.label }}
      <button
        type="button"
        :aria-label="`Remover filtro ${chip.label}`"
        class="focus-ring rounded-full p-0.5 transition hover:bg-paper-primary/25 active:bg-paper-primary/40 active:scale-90"
        @click="emit('remove', chip.key)"
      >
        <XMarkIcon class="h-3.5 w-3.5" />
      </button>
    </span>
    <button
      type="button"
      class="focus-ring rounded-md px-2 py-1 text-xs font-semibold text-gray-500 underline-offset-2 transition hover:text-paper-danger-strong hover:underline active:text-paper-danger"
      @click="emit('clear')"
    >
      Limpar filtros
    </button>
  </div>
</template>

<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/outline';

export interface FilterChip {
  key: string;
  label: string;
}

defineProps<{
  /** Filtros ativos; sem itens, o componente não exibe nada. */
  chips: FilterChip[];
}>();

const emit = defineEmits<{
  (e: 'remove', key: string): void;
  (e: 'clear'): void;
}>();
</script>
