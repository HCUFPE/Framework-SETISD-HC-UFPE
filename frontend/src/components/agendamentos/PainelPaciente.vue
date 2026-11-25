<template>
  <Card>
    <template #header>
      <div>
        <h2 class="text-lg font-bold text-paper-text">Paciente e agendamentos</h2>
        <p class="text-xs text-gray-500">Busca por nome, prontuário ou protocolo — sem endereço do paciente.</p>
      </div>
    </template>

    <div class="flex gap-2">
      <input
        v-model="termo"
        type="search"
        class="min-w-0 flex-1 rounded border border-gray-300 px-3 py-2 text-sm focus:border-paper-primary focus:outline-none"
        placeholder="Nome, prontuário ou protocolo"
        @keyup.enter="buscar"
      />
      <Button variant="info" @click="buscar">Buscar</Button>
    </div>

    <div v-if="pacientes.length > 0" class="mt-3 max-h-48 overflow-y-auto rounded border border-gray-200">
      <button
        v-for="paciente in pacientes"
        :key="paciente.pacienteChave"
        type="button"
        class="block w-full px-3 py-2 text-left text-sm transition hover:bg-gray-50"
        :class="paciente.pacienteChave === pacienteChave ? 'bg-paper-primary/10 font-semibold text-paper-primary' : 'text-gray-700'"
        @click="emit('selecionar', paciente.pacienteChave)"
      >
        {{ paciente.pacienteNome }}
        <span class="block text-xs text-gray-500">
          Pront. {{ paciente.prontuario }} · {{ paciente.agendamentosAtivos }} ativo(s)
        </span>
      </button>
    </div>

    <div class="mt-4 border-t border-gray-200 pt-4">
      <div class="mb-2 flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-700">Histórico de agendamentos</h3>
        <span class="text-xs text-gray-500">{{ agendamentos.length }} registro(s)</span>
      </div>

      <LoadingIndicator v-if="carregando" />
      <p v-if="!carregando && agendamentos.length === 0" class="rounded bg-gray-50 p-3 text-sm text-gray-500">
        Selecione um paciente para ver todos os agendamentos (ativos, cancelados e concluídos).
      </p>

      <ul v-else class="space-y-2">
        <li v-for="agendamento in agendamentos" :key="agendamento.id" class="rounded border border-gray-200 p-3">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p class="text-sm font-semibold text-gray-800">{{ agendamento.exame }}</p>
              <p class="text-xs text-gray-500">{{ agendamento.unidade }}</p>
            </div>
            <span
              class="rounded-full px-2 py-1 text-[11px] font-bold"
              :class="classeStatus(agendamento.status)"
            >{{ rotuloStatus(agendamento.status) }}</span>
          </div>
          <p class="mt-2 text-xs text-gray-600">{{ formatarDataHora(agendamento.dataHora) }}</p>
          <p class="text-xs text-gray-500">{{ agendamento.protocolo }} · {{ agendamento.confirmadoPor }}</p>
          <p v-if="agendamento.justificativa" class="mt-1 text-xs italic text-gray-500">
            Justificativa: {{ agendamento.justificativa }}
          </p>
          <div v-if="podeEditar && agendamento.status === 'ATIVO'" class="mt-3 flex flex-wrap gap-2">
            <Button variant="primary" @click="emit('remarcar', agendamento)">Remarcar</Button>
            <Button variant="danger" @click="emit('cancelar', agendamento)">Cancelar</Button>
            <Button variant="secondary" @click="emit('sugestoes', agendamento)">Ver sugestões</Button>
          </div>
        </li>
      </ul>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Button from '../Button.vue';
import Card from '../Card.vue';
import LoadingIndicator from '../LoadingIndicator.vue';
import { formatarDataHora } from '../../utils/format';
import type { Agendamento, PacienteAgendamentos } from '../../types/sae';

defineProps<{
  pacientes: PacienteAgendamentos[];
  agendamentos: Agendamento[];
  pacienteChave: string;
  carregando: boolean;
  podeEditar: boolean;
}>();

const emit = defineEmits<{
  buscar: [termo: string];
  selecionar: [chave: string];
  remarcar: [agendamento: Agendamento];
  cancelar: [agendamento: Agendamento];
  sugestoes: [agendamento: Agendamento];
}>();

const termo = ref('');

function buscar(): void {
  emit('buscar', termo.value.trim());
}

function rotuloStatus(status: Agendamento['status']): string {
  if (status === 'CANCELADO') return 'Cancelado';
  if (status === 'CONCLUIDO') return 'Concluído';
  return 'Ativo';
}

function classeStatus(status: Agendamento['status']): string {
  if (status === 'CANCELADO') return 'bg-red-100 text-red-800';
  if (status === 'CONCLUIDO') return 'bg-gray-200 text-gray-700';
  return 'bg-teal-100 text-teal-800';
}
</script>
