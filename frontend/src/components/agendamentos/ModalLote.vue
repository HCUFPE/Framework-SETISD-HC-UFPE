<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" @click="cancelar" />
    <div class="bg-white rounded-lg border border-gray-200 p-6 w-full max-w-md shadow-xl">
      <div class="flex items-start gap-3">
        <div class="rounded-full bg-amber-100 p-2 text-amber-600 flex-shrink-0">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.859-3.087Z" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-gray-900">Confirmar edição em lote</h3>
          <p class="mt-1 text-sm text-gray-600">
            Você está prestes a alterar <strong>{{ selecionados.length }}</strong>
            agendamento(s) para o status <strong>{{ novoStatus }}</strong>.
          </p>
          <p class="mt-2 text-xs text-gray-500">
            Justificativa: {{ justificativa }}
          </p>
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-2">
        <button
          type="button"
          @click="cancelar"
          class="text-xs text-gray-600 hover:underline px-2 py-1"
        >
          Cancelar
        </button>
        <Button variant="danger" :loading="ocupado" @click="confirmar">
          Confirmar alteração em lote
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '../Button.vue';

defineProps<{
  selecionados: string[];
  novoStatus: string;
  justificativa: string;
  ocupado?: boolean;
}>();

const emit = defineEmits<{
  confirmar: [];
  cancelar: [];
}>();

function cancelar(): void {
  emit('cancelar');
}

function confirmar(): void {
  emit('confirmar');
}
</script>