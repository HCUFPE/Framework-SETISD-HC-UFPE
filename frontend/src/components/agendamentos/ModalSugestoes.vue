<template>
  <Modal :show="show" @close="emit('close')">
    <template #header>Sugestões automáticas de horário</template>

    <LoadingIndicator v-if="carregando" />
    <p v-if="sugestoes.length === 0 && !carregando" class="text-sm text-gray-500">
      Nenhuma sugestão disponível para esta solicitação no momento.
    </p>

    <ol v-else class="space-y-3">
      <li
        v-for="(sugestao, indice) in sugestoes"
        :key="sugestao.slot.id"
        class="rounded-lg border border-gray-200 p-4"
      >
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p class="text-sm font-bold text-gray-800">
              {{ indice + 1 }}. {{ formatarDataHora(sugestao.slot.inicio) }}
              <span class="ml-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                {{ sugestao.slot.livres }}/{{ sugestao.slot.capacidade }} vagas
              </span>
            </p>
            <p class="text-xs text-gray-500">{{ sugestao.slot.unidade }} · {{ sugestao.slot.nomeExame }}</p>
          </div>
          <span class="rounded bg-paper-primary/10 px-2 py-1 text-xs font-bold text-paper-primary">
            {{ sugestao.pontuacao }} pontos
          </span>
        </div>
        <ul class="mt-3 list-disc space-y-1 pl-5 text-xs text-gray-600">
          <li v-for="motivo in sugestao.motivos" :key="motivo">{{ motivo }}</li>
        </ul>
        <p class="mt-2 text-xs text-gray-500">
          Distância:
          <strong v-if="sugestao.distanciaKm !== null">
            {{ sugestao.distanciaKm.toFixed(1).replace('.', ',') }} km
          </strong>
          <strong v-else>indisponível</strong>
          (origem: {{ sugestao.distanciaOrigem }})
        </p>
        <div class="mt-3 flex justify-end">
          <Button variant="primary" @click="emit('usar', sugestao.slot)">Usar este horário</Button>
        </div>
      </li>
    </ol>
  </Modal>
</template>

<script setup lang="ts">
import Button from '../Button.vue';
import LoadingIndicator from '../LoadingIndicator.vue';
import Modal from '../Modal.vue';
import { formatarDataHora } from '../../utils/format';
import type { AgendaSlot, SugestaoAgendamento } from '../../types/sae';

defineProps<{
  show: boolean;
  sugestoes: SugestaoAgendamento[];
  carregando?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  usar: [slot: AgendaSlot];
}>();
</script>
