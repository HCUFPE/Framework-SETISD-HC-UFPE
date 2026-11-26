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
            <th class="px-2 py-2">
              <input
                v-if="podeEditar"
                type="checkbox"
                :checked="selecionadosTodas"
                @change="alternarSelecaoTodas"
                class="rounded border-gray-300 text-paper-primary focus:ring-paper-primary"
              />
            </th>
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
          <tr
            v-for="(proposta, indice) in propostas"
            :key="proposta.agendamentoId"
            :class="{ 'bg-gray-50/50': selecionados.has(proposta.agendamentoId) }"
          >
            <td class="px-2 py-2">
              <input
                v-if="podeEditar"
                type="checkbox"
                :checked="selecionados.has(proposta.agendamentoId)"
                @change="alternarSelecao(proposta.agendamentoId)"
                class="rounded border-gray-300 text-paper-primary focus:ring-paper-primary"
              />
            </td>
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

    <!-- Barra de ação em lote -->
    <div
      v-if="podeEditar && selecionados.size > 0"
      class="mt-3 rounded border border-amber-200 bg-amber-50 p-3"
    >
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-semibold text-amber-800">
          {{ selecionados.size }} item(ns) selecionado(s)
        </span>
        <select
          v-model="loteNovoStatus"
          class="campo-lote text-xs border border-amber-300 rounded px-2 py-1"
        >
          <option value="PROPOSTO">Proposta</option>
          <option value="ATIVO">Ativo</option>
          <option value="CANCELADO">Cancelado</option>
          <option value="CONCLUIDO">Concluído</option>
        </select>
        <input
          v-model="loteJustificativa"
          type="text"
          placeholder="Justificativa (obrigatória)"
          class="campo-lote text-xs border border-amber-300 rounded px-2 py-1 w-48"
        />
        <Button variant="warning" :loading="ocupado" @click="abrirConfirmacaoLote">
          Aplicar em lote
        </Button>
        <button
          type="button"
          @click="limparSelecao"
          class="text-xs text-gray-600 hover:underline px-2 py-1"
        >
          Limpar seleção
        </button>
      </div>
      <p class="mt-1 text-xs text-amber-700">
        A justificativa será aplicada a todos os itens selecionados.
      </p>
    </div>

    <!-- Modal de confirmação da edição em lote -->
    <ModalLote
      v-if="modalLoteAberto"
      :selecionados="selecionadosArray"
      :novoStatus="loteNovoStatus"
      :justificativa="loteJustificativa"
      :ocupado="ocupado"
      @confirmar="aplicarLote"
      @cancelar="modalLoteAberto = false"
    />
  </Card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import Button from '../Button.vue';
import Card from '../Card.vue';
import PriorityBadge from '../PriorityBadge.vue';
import StatusBadge from '../StatusBadge.vue';
import ModalLote from './ModalLote.vue';
import { formatarDataHora, formatarDuracao } from '../../utils/format';
import type { PropostaAgendamentoFila } from '../../types/sae';

const props = defineProps<{
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
  'lote-aplicado': [resultado: any];
}>();

const selecionados = ref<Set<string>>(new Set());
const modalLoteAberto = ref(false);
const loteNovoStatus = ref('ATIVO');
const loteJustificativa = ref('');

const selecionadosArray = computed(() => Array.from(selecionados.value));
const selecionadosTodas = computed(() =>
  selecionados.value.size > 0 && selecionados.value.size === props.propostas.length,
);

function alternarSelecao(id: string): void {
  if (selecionados.value.has(id)) selecionados.value.delete(id);
  else selecionados.value.add(id);
}

function alternarSelecaoTodas(): void {
  if (selecionadosTodas.value) {
    selecionados.value.clear();
  } else {
    props.propostas.forEach((p: PropostaAgendamentoFila) =>
      selecionados.value.add(p.agendamentoId),
    );
  }
}

function limparSelecao(): void {
  selecionados.value.clear();
}

function abrirConfirmacaoLote(): void {
  if (!loteJustificativa.value.trim()) return;
  modalLoteAberto.value = true;
}

async function aplicarLote(): Promise<void> {
  const ids = selecionadosArray.value;
  emit('lote-aplicado', {
    agendamentoIds: ids,
    novoStatus: loteNovoStatus.value,
    justificativa: loteJustificativa.value,
  });
  modalLoteAberto.value = false;
  limparSelecao();
  loteJustificativa.value = '';
}
</script>

<style scoped>
.campo-lote {
  width: 100%;
  border-radius: 0.25rem;
  border: 1px solid #d1d5db;
  padding: 0.45rem 0.6rem;
  font-size: 0.875rem;
  background: #fffbf0;
}
.campo-lote:focus {
  outline: none;
  border-color: #f59e0b;
  ring: 1px;
}
</style>