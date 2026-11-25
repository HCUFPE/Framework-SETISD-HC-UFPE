<template>
  <Card>
    <template #header>
      <div>
        <h2 class="text-lg font-bold text-paper-text">Propostas da simulação</h2>
        <p class="text-xs text-gray-500">
          Pré-alocações dos próximos 30 dias. Reservam vaga, mas só viram agendamento
          após confirmação do operador.
        </p>
      </div>
    </template>

    <div v-if="podeEditar" class="mb-3 flex flex-wrap items-center gap-2">
      <Button variant="primary" :loading="ocupado" @click="emit('gerar')">Simular próximos 30 dias</Button>
      <span class="text-xs text-gray-500">Critérios: prioridade, espera, compatibilidade e capacidade.</span>
    </div>

    <p v-if="!propostas.length" class="text-sm text-gray-500">
      Nenhuma proposta pendente. Gere a simulação para pré-alocar as solicitações elegíveis.
    </p>

    <ul v-else class="max-h-96 space-y-2 overflow-y-auto">
      <li v-for="proposta in propostas" :key="proposta.id" class="rounded-lg border border-sky-200 bg-sky-50 p-3 text-sm">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="font-semibold text-gray-800">{{ proposta.pacienteNome }}</span>
          <span class="rounded-full bg-sky-100 px-2 py-0.5 text-[11px] font-bold text-sky-800">Aguardando confirmação</span>
        </div>
        <p class="mt-1 text-xs text-gray-600">
          {{ formatarDataHora(proposta.dataHora) }} · {{ proposta.unidade }} · {{ proposta.exame }}
        </p>
        <p class="text-xs text-gray-500">{{ proposta.protocolo }}</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <Button variant="success" :loading="ocupado" @click="emit('confirmar', proposta)">Confirmar</Button>
          <Button variant="secondary" @click="emit('remarcar', proposta)">Remarcar</Button>
          <Button variant="secondary" @click="emit('nao-confirmado', proposta)">Paciente não confirmou</Button>
          <Button variant="secondary" @click="emit('cancelar', proposta)">Cancelar</Button>
        </div>
      </li>
    </ul>
  </Card>
</template>

<script setup lang="ts">
import Button from '../Button.vue';
import Card from '../Card.vue';
import { formatarDataHora } from '../../utils/format';
import type { Agendamento } from '../../types/sae';

defineProps<{
  propostas: Agendamento[];
  podeEditar: boolean;
  ocupado?: boolean;
}>();

const emit = defineEmits<{
  gerar: [];
  confirmar: [proposta: Agendamento];
  remarcar: [proposta: Agendamento];
  'nao-confirmado': [proposta: Agendamento];
  cancelar: [proposta: Agendamento];
}>();
</script>
