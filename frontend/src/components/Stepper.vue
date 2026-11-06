<template>
  <nav aria-label="Progresso">
    <ol class="flex flex-wrap items-center gap-y-2">
      <li
        v-for="(step, index) in steps"
        :key="index"
        :aria-current="index === current ? 'step' : undefined"
        class="flex items-center"
      >
        <div class="flex items-center gap-2">
          <span
            :class="circleClass(index)"
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold transition-colors"
          >
            <CheckIcon v-if="index < current" class="h-4 w-4" aria-hidden="true" />
            <span v-else>{{ index + 1 }}</span>
          </span>
          <span :class="labelClass(index)" class="text-sm whitespace-nowrap">
            {{ step.label }}
            <span class="sr-only">{{ stateText(index) }}</span>
          </span>
        </div>
        <span
          v-if="index < steps.length - 1"
          :class="index < current ? 'bg-paper-success' : 'bg-gray-300'"
          class="mx-3 h-0.5 w-8 sm:w-12 shrink-0 rounded"
          aria-hidden="true"
        ></span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { CheckIcon } from '@heroicons/vue/24/outline';

export interface StepperStep {
  label: string;
}

const props = defineProps<{
  steps: StepperStep[];
  /** Índice (base 0) do passo atual. */
  current: number;
}>();

/** Classes do círculo numerado conforme o estado do passo. */
const circleClass = (index: number): string => {
  if (index < props.current) return 'bg-paper-success border-paper-success text-white';
  if (index === props.current) return 'bg-paper-primary border-paper-primary text-white ring-4 ring-paper-primary-soft';
  return 'bg-white border-gray-300 text-gray-400';
};

/** Classes do rótulo conforme o estado do passo. */
const labelClass = (index: number): string => {
  if (index < props.current) return 'text-paper-success-strong font-semibold';
  if (index === props.current) return 'text-gray-900 font-bold';
  return 'text-gray-400';
};

/** Texto do estado, lido apenas por leitores de tela. */
const stateText = (index: number): string => {
  if (index < props.current) return '(concluído)';
  if (index === props.current) return '(atual)';
  return '(pendente)';
};
</script>
