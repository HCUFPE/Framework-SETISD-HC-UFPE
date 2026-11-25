<template>
  <Modal :show="show" @close="emit('close')">
    <template #header>{{ titulo }}</template>

    <div class="space-y-3">
      <div class="rounded bg-gray-50 p-3 text-sm">
        <p v-if="solicitacao">
          <strong>Solicitação:</strong> {{ solicitacao.protocolo }} · {{ solicitacao.pacienteNome }}
        </p>
        <p v-else-if="agendamento">
          <strong>Agendamento:</strong> {{ agendamento.protocolo }} · {{ agendamento.pacienteNome }}
        </p>
        <p v-if="agendamento && modo === 'remarcar'">
          <strong>Horário atual:</strong> {{ formatarDataHora(agendamento.dataHora) }}
        </p>
        <p v-if="slot">
          <strong>{{ modo === 'cancelar' ? 'Horário a cancelar:' : 'Novo horário:' }}</strong>
          {{ formatarDataHora(slot.inicio) }} · {{ slot.unidade }} · {{ slot.nomeExame }}
          ({{ slot.livres }}/{{ slot.capacidade }} vagas)
        </p>
        <p v-else-if="agendamento && modo === 'cancelar'">
          <strong>Horário:</strong> {{ formatarDataHora(agendamento.dataHora) }} · {{ agendamento.unidade }}
        </p>
      </div>

      <div>
        <label for="justificativa-agendamento" class="mb-1 block text-sm font-semibold text-gray-700">
          Justificativa {{ obrigatoria ? '*' : '(opcional)' }}
        </label>
        <textarea
          id="justificativa-agendamento"
          v-model="justificativa"
          rows="3"
          class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-paper-primary focus:outline-none"
          :placeholder="obrigatoria ? 'Descreva o motivo da alteração' : 'Informe observações, se houver'"
        ></textarea>
        <p v-if="tentouConfirmar && obrigatoria && !justificativa.trim()" class="mt-1 text-xs text-red-600">
          A justificativa é obrigatória.
        </p>
      </div>
    </div>

    <template #footer>
      <Button variant="secondary" :disabled="salvando" @click="emit('close')">Voltar</Button>
      <Button :variant="modo === 'cancelar' ? 'danger' : 'primary'" :loading="salvando" @click="confirmar">
        {{ modo === 'cancelar' ? 'Confirmar cancelamento' : modo === 'remarcar' ? 'Confirmar remarcação' : 'Confirmar agendamento' }}
      </Button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import Button from '../Button.vue';
import Modal from '../Modal.vue';
import { formatarDataHora } from '../../utils/format';
import type { ModoAcaoAgendamento } from '../../stores/agendamentos';
import type { AgendaSlot, Agendamento, Solicitacao } from '../../types/sae';

const props = defineProps<{
  show: boolean;
  modo: ModoAcaoAgendamento;
  slot: AgendaSlot | null;
  agendamento: Agendamento | null;
  solicitacao: Solicitacao | null;
  salvando?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  confirmar: [justificativa: string];
}>();

const justificativa = ref('');
const tentouConfirmar = ref(false);
const obrigatoria = computed(() => props.modo !== 'agendar');

const titulo = computed(() => {
  if (props.modo === 'remarcar') return 'Remarcar agendamento';
  if (props.modo === 'cancelar') return 'Cancelar agendamento';
  return 'Confirmar agendamento';
});

watch(() => props.show, (aberto) => {
  if (aberto) {
    justificativa.value = '';
    tentouConfirmar.value = false;
  }
});

function confirmar(): void {
  tentouConfirmar.value = true;
  if (obrigatoria.value && !justificativa.value.trim()) return;
  emit('confirmar', justificativa.value.trim());
}
</script>
