<template>
  <Card>
    <template #header>
      <div>
        <h2 class="text-lg font-bold text-paper-text">Fila de propostas da simulação</h2>
        <p class="text-xs text-gray-500">
          Ordenada por prioridade e tempo na fila. Cada proposta reserva uma vaga e só
          se torna agendamento após confirmação do operador.
        </p>
      </div>
    </template>

    <div v-if="podeEditar" class="mb-3 flex flex-wrap items-center gap-2">
      <Button variant="primary" :loading="ocupado" @click="emit('gerar')">Simular próximos 30 dias</Button>
      <span class="text-xs text-gray-500">
        Respeita capacidade, exame específico e as reservas já simuladas.
      </span>
    </div>

    <p v-if="!propostas.length" class="text-sm text-gray-500">
      Nenhuma proposta pendente. Gere a simulação para pré-alocar as solicitações elegíveis.
    </p>

    <div v-else class="max-h-96 overflow-auto rounded border border-gray-200">
      <table class="w-full text-left text-xs">
        <thead class="sticky top-0 bg-gray-50 text-[11px] uppercase tracking-wide text-gray-500">
          <tr>
            <th class="px-2 py-2">#</th>
            <th class="px-2 py-2">Prioridade</th>
            <th class="px-2 py-2">Paciente / Prontuário</th>
            <th class="px-2 py-2">Unidade solicitante</th>
            <th class="px-2 py-2">Exame(s)</th>
            <th class="px-2 py-2">Status</th>
            <th class="px-2 py-2">Tempo na fila</th>
            <th class="px-2 py-2">Horário proposto</th>
            <th v-if="podeEditar" class="px-2 py-2">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 bg-white">
          <tr v-for="(proposta, indice) in propostas" :key="proposta.agendamentoId">
            <td class="px-2 py-2 font-medium text-gray-500">{{ indice + 1 }}</td>
            <td class="px-2 py-2"><PriorityBadge :prioridade="proposta.prioridade" /></td>
            <td class="px-2 py-2">
              <p class="font-semibold text-gray-800">{{ proposta.pacienteNome }}</p>
              <p class="text-gray-500">{{ proposta.protocolo }} · pront. {{ proposta.prontuario }}</p>
            </td>
            <td class="px-2 py-2 text-gray-600">{{ proposta.unidadeSolicitante }}</td>
            <td class="px-2 py-2 text-gray-600">{{ proposta.exames }}</td>
            <td class="px-2 py-2"><StatusBadge :status="proposta.statusSolicitacao" /></td>
            <td class="px-2 py-2 text-gray-600">{{ formatarDuracao(proposta.tempoNaFilaHoras) }}</td>
            <td class="px-2 py-2 text-gray-600">
              {{ formatarDataHora(proposta.dataHora) }}
              <span class="block text-gray-500">{{ proposta.unidade }} · {{ proposta.nomeExame }}</span>
            </td>
            <td v-if="podeEditar" class="px-2 py-2">
              <div class="flex flex-wrap gap-1">
                <Button variant="success" :loading="ocupado" @click="emit('confirmar', proposta)">Confirmar</Button>
                <Button variant="secondary" @click="emit('remarcar', proposta)">Remarcar</Button>
                <Button variant="secondary" @click="emit('nao-confirmado', proposta)">Não confirmou</Button>
                <Button variant="secondary" @click="emit('cancelar', proposta)">Cancelar</Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </Card>
</template>

<script setup lang="ts">
import Button from '../Button.vue';
import Card from '../Card.vue';
import PriorityBadge from '../PriorityBadge.vue';
import StatusBadge from '../StatusBadge.vue';
import { formatarDataHora, formatarDuracao } from '../../utils/format';
import type { PropostaAgendamentoFila } from '../../types/sae';

defineProps<{
  propostas: PropostaAgendamentoFila[];
  podeEditar: boolean;
  ocupado?: boolean;
}>();

const emit = defineEmits<{
  gerar: [];
  confirmar: [proposta: PropostaAgendamentoFila];
  remarcar: [proposta: PropostaAgendamentoFila];
  'nao-confirmado': [proposta: PropostaAgendamentoFila];
  cancelar: [proposta: PropostaAgendamentoFila];
}>();
</script>
