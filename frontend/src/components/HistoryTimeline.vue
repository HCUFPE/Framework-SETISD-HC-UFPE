<template>
  <ol class="space-y-3">
    <li v-for="evento in eventos" :key="evento.id" class="border-l-2 pl-3" :class="borda(evento.categoria)">
      <p class="text-sm font-medium text-gray-800">{{ evento.acao }}</p>
      <p class="text-xs text-gray-500">{{ formatarDataHora(evento.em) }} · {{ evento.autor }} · {{ evento.categoria }}</p>
      <p class="mt-1 text-xs text-gray-600">{{ evento.detalhes }}</p>
    </li>
    <li v-if="eventos.length === 0" class="text-sm text-gray-500">Nenhum evento registrado.</li>
  </ol>
</template>

<script setup lang="ts">
import { formatarDataHora } from '../utils/format';
import type { CategoriaAuditoria, EventoHistorico } from '../types/sae';

defineProps<{ eventos: EventoHistorico[] }>();

function borda(categoria: CategoriaAuditoria): string {
  return {
    SEGURANCA: 'border-paper-danger',
    NEGOCIO_CLINICO: 'border-paper-info',
    CONFIGURACAO: 'border-paper-warning',
  }[categoria];
}
</script>
