<template>
  <div class="relative">
    <Button variant="secondary" @click="aberto = !aberto">Colunas</Button>

    <template v-if="aberto">
      <div class="fixed inset-0 z-20" @click="aberto = false"></div>
      <div class="absolute right-0 z-30 mt-2 w-60 rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Exibir colunas</p>
        <div class="space-y-1">
          <label
            v-for="coluna in colunas"
            :key="coluna.chave"
            class="flex cursor-pointer items-center gap-2 rounded px-1 py-1 text-sm text-gray-700 hover:bg-gray-50"
          >
            <input
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300 text-paper-primary"
              :checked="modelValue.includes(coluna.chave)"
              @change="alternar(coluna.chave)"
            />
            {{ coluna.rotulo }}
          </label>
        </div>
        <button
          type="button"
          class="mt-3 w-full border-t border-gray-100 pt-2 text-left text-xs font-semibold text-paper-primary hover:underline"
          @click="emit('redefinir')"
        >Restaurar colunas padrão</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Button from './Button.vue';
import type { OpcaoColuna } from '../types/sae';

const props = defineProps<{
  colunas: OpcaoColuna[];
  modelValue: string[];
}>();

const emit = defineEmits<{
  'update:modelValue': [valor: string[]];
  redefinir: [];
}>();

const aberto = ref(false);

function alternar(chave: string): void {
  const proximo = props.modelValue.includes(chave)
    ? props.modelValue.filter((item) => item !== chave)
    : [...props.modelValue, chave];
  emit('update:modelValue', proximo);
}
</script>
