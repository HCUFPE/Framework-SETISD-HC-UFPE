<template>
  <div>
    <label :for="id" class="form-label">Caso de origem da IHQ <span class="text-paper-danger">*</span></label>
    <p class="mb-2 text-xs text-gray-500">
      A IHQ é vinculada a um caso já existente e não gera um novo caso. Busque por nº interno, prontuário ou nome.
    </p>

    <div v-if="selecionado" class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-paper-primary bg-paper-primary-soft p-3">
      <div>
        <p class="font-bold text-gray-900">{{ selecionado.numeroInterno }} · {{ selecionado.nomePaciente }}</p>
        <p class="text-sm text-gray-700">Prontuário {{ selecionado.prontuario }} · {{ selecionado.descricaoMaterial }}</p>
      </div>
      <Button variant="secondary" size="sm" @click="limpar">Trocar caso</Button>
    </div>

    <div v-else>
      <div class="relative">
        <MagnifyingGlassIcon class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" aria-hidden="true" />
        <input
          :id="id"
          v-model="termo"
          type="text"
          autocomplete="off"
          class="form-control pl-10"
          placeholder="Ex.: HP-0005, 2340017 ou nome do paciente"
          :aria-invalid="erro ? 'true' : undefined"
          @input="buscar"
        />
      </div>
      <p v-if="buscando" class="mt-2 text-sm text-gray-500" role="status">Buscando casos...</p>
      <p v-else-if="termo.trim().length >= 2 && resultados.length === 0" class="mt-2 text-sm text-gray-500">
        Nenhum caso encontrado para "{{ termo }}".
      </p>
      <ul v-if="resultados.length" class="mt-2 divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white" aria-label="Casos encontrados">
        <li v-for="caso in resultados" :key="caso.numeroInterno">
          <button
            type="button"
            :disabled="!caso.elegivel"
            class="focus-ring [--focus-ring-offset:-2px] flex w-full items-start justify-between gap-3 px-3 py-2 text-left transition enabled:hover:bg-gray-50 enabled:active:bg-gray-100 disabled:opacity-60"
            @click="selecionar(caso)"
          >
            <span>
              <span class="font-bold text-gray-900">{{ caso.numeroInterno }}</span>
              <span class="text-gray-700"> · {{ caso.nomePaciente }} · Pront. {{ caso.prontuario }}</span>
              <span class="block text-xs text-gray-500">{{ caso.descricaoMaterial }}</span>
              <span v-if="!caso.elegivel" class="block text-xs font-semibold text-paper-danger-strong">{{ caso.motivoInelegivel }}</span>
            </span>
            <StatusCasoBadge :status="caso.status" />
          </button>
        </li>
      </ul>
    </div>
    <p v-if="erro" class="mt-1 text-sm text-paper-danger-strong">{{ erro }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import Button from '../../Button.vue';
import StatusCasoBadge from '../StatusCasoBadge.vue';
import { useCasosStore } from '../../../stores/casos';
import type { CasoElegivelIhq } from '../../../types/ap';

defineProps<{ id: string; erro?: string }>();
const selecionado = defineModel<CasoElegivelIhq | null>({ required: true });

const casosStore = useCasosStore();
const termo = ref('');
const resultados = ref<CasoElegivelIhq[]>([]);
const buscando = ref(false);
let temporizador: ReturnType<typeof setTimeout> | undefined;

/** Busca com pequeno atraso enquanto o usuário digita. */
const buscar = () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(async () => {
    const atual = termo.value;
    if (atual.trim().length < 2) {
      resultados.value = [];
      return;
    }
    buscando.value = true;
    try {
      const encontrados = await casosStore.buscarElegiveisIhq(atual);
      if (atual === termo.value) resultados.value = encontrados;
    } finally {
      buscando.value = false;
    }
  }, 250);
};

const selecionar = (caso: CasoElegivelIhq) => {
  if (caso.elegivel) selecionado.value = caso;
};

const limpar = () => {
  selecionado.value = null;
  termo.value = '';
  resultados.value = [];
};
</script>
