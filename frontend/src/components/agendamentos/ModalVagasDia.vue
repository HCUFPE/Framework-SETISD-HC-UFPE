<template>
  <Modal :show="show" @close="emit('close')">
    <template #header>Vagas de {{ formatarData(data) }}</template>

    <p class="mb-3 text-xs text-gray-500">
      Horários disponíveis para o exame selecionado no filtro do calendário.
      A marcação só é concluída após a confirmação da vaga.
    </p>

    <div class="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
      <label class="mb-1 block text-xs font-semibold text-gray-700" for="busca-solicitacao-popup">
        Paciente a marcar
      </label>
      <div class="flex gap-2">
        <input
          id="busca-solicitacao-popup"
          v-model="termo"
          type="search"
          class="form-control"
          placeholder="Nome, prontuário ou protocolo"
          @keyup.enter="buscar"
        />
        <Button variant="secondary" @click="buscar">Buscar</Button>
      </div>

      <div v-if="solicitacao" class="mt-2 flex items-center justify-between rounded border border-paper-primary/30 bg-white px-3 py-2 text-sm">
        <span class="truncate">
          <strong>{{ solicitacao.pacienteNome }}</strong> · {{ solicitacao.protocolo }}
        </span>
        <button
          type="button"
          class="ml-2 shrink-0 text-xs font-semibold text-paper-primary hover:underline"
          @click="emit('limpar')"
        >trocar</button>
      </div>

      <ul v-if="buscaFeita && solicitacoes.length > 0 && !solicitacao" class="mt-2 max-h-32 space-y-1 overflow-y-auto">
        <li v-for="item in solicitacoes" :key="item.id">
          <button
            type="button"
            class="w-full rounded border border-gray-200 bg-white px-2 py-1 text-left text-xs hover:border-paper-primary hover:text-paper-primary"
            @click="emit('selecionar', item.id)"
          >
            {{ item.protocolo }} · {{ item.pacienteNome }} · {{ item.exame }}
          </button>
        </li>
      </ul>
      <p v-else-if="buscaFeita && solicitacoes.length === 0" class="mt-2 text-xs text-gray-500">
        Nenhuma solicitação encontrada para o termo informado.
      </p>
      <p v-else-if="!solicitacao" class="mt-2 text-xs text-gray-500">
        Use a solicitação já selecionada na tela ou busque outra aqui.
      </p>
    </div>

    <ul class="max-h-96 space-y-2 overflow-y-auto">
      <li
        v-for="slot in slots"
        :key="slot.id"
        class="rounded-lg border p-3 text-sm"
        :class="slot.id === selecionadoId ? 'border-paper-primary bg-paper-primary/5' : 'border-gray-200'"
      >
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="font-semibold text-gray-800">{{ formatarHora(slot.inicio) }}–{{ formatarHora(slot.fim) }}</span>
          <span class="rounded-full px-2 py-0.5 text-[11px] font-bold" :class="classeOcupacao(slot)">
            {{ slot.livres }}/{{ slot.capacidade }} vagas
          </span>
        </div>
        <p class="truncate text-xs text-gray-600">{{ slot.unidade }} · {{ slot.nomeExame }}</p>
        <div class="mt-2 flex justify-end gap-2">
          <button
            type="button"
            class="text-xs font-semibold text-paper-primary hover:underline"
            @click="emit('selecionar-slot', slot)"
          >Selecionar vaga</button>
          <Button
            v-if="podeEditar && slot.livres > 0 && slot.status !== 'ENCERRADO'"
            variant="success"
            :disabled="!solicitacao || ocupado"
            :loading="ocupado"
            @click="emit('marcar', slot)"
          >{{ modo === 'remarcar' ? 'Remarcar para aqui' : 'Marcar paciente' }}</Button>
        </div>
      </li>
      <li v-if="slots.length === 0" class="rounded border border-gray-200 p-4 text-center text-sm text-gray-500">
        Nenhuma vaga livre nesta data para o exame selecionado.
      </li>
    </ul>

    <p v-if="erro" class="mt-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">{{ erro }}</p>
  </Modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import Button from '../Button.vue';
import Modal from '../Modal.vue';
import { diaLocal } from '../../utils/datetime';
import type { AgendaSlot, Solicitacao } from '../../types/sae';

const props = defineProps<{
  show: boolean;
  data: string;
  slots: AgendaSlot[];
  solicitacao: Solicitacao | null;
  solicitacoes: Solicitacao[];
  selecionadoId?: string;
  modo?: 'agendar' | 'remarcar';
  podeEditar: boolean;
  ocupado?: boolean;
  erro?: string;
}>();

const emit = defineEmits<{
  close: [];
  buscar: [termo: string];
  selecionar: [id: string];
  limpar: [];
  'selecionar-slot': [slot: AgendaSlot];
  marcar: [slot: AgendaSlot];
}>();

const termo = ref('');
const buscaFeita = ref(false);

watch(() => props.show, (aberto) => {
  if (aberto) {
    termo.value = props.solicitacao?.prontuario ?? '';
    buscaFeita.value = false;
  }
});

function buscar(): void {
  buscaFeita.value = true;
  emit('buscar', termo.value.trim());
}

function formatarData(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
    .format(new Date(`${diaLocal(iso)}T12:00:00`));
}

function formatarHora(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
    .format(new Date(iso));
}

function classeOcupacao(slot: AgendaSlot): string {
  if (slot.status === 'ENCERRADO' || slot.livres === 0) return 'bg-red-100 text-red-800';
  if (slot.capacidade > 0 && slot.livres / slot.capacidade <= 0.4) return 'bg-amber-100 text-amber-800';
  return 'bg-emerald-100 text-emerald-800';
}
</script>
