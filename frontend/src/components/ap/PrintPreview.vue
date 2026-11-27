<template>
  <teleport to="body">
    <div
      v-if="show && caso"
      id="print-root"
      class="fixed inset-0 z-50 flex flex-col bg-gray-600/95"
      role="dialog"
      aria-modal="true"
      :aria-label="titulo"
    >
      <!-- Barra de ações (não é impressa) -->
      <div class="no-print flex flex-wrap items-center justify-between gap-3 bg-white px-6 py-3 shadow">
        <div class="flex items-center gap-3">
          <PrinterIcon class="h-6 w-6 text-paper-primary-strong" aria-hidden="true" />
          <div>
            <p class="font-bold text-gray-800">{{ titulo }}</p>
            <p class="text-xs text-gray-500">Pré-visualização em escala real · {{ casoEtiqueta?.numeroInterno ?? caso.numeroInterno }}</p>
          </div>
        </div>
        <div class="flex gap-2">
          <Button variant="secondary" @click="emit('close')">Fechar</Button>
          <Button variant="primary" :disabled="tipo === 'ETIQUETAS' && etiquetas.length === 0" @click="imprimir">
            <PrinterIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Imprimir
          </Button>
        </div>
      </div>

      <!-- Seleção das etiquetas (não é impressa): só para casos com mais de uma amostra -->
      <fieldset
        v-if="tipo === 'ETIQUETAS' && amostras.length > 1"
        class="no-print border-t border-gray-200 bg-white px-6 py-3"
      >
        <legend class="sr-only">Amostras a imprimir</legend>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span class="text-sm font-bold text-gray-700">Imprimir as etiquetas das amostras:</span>
          <label
            v-for="item in amostras"
            :key="item.codigo"
            :class="selecionadas.includes(item.codigo) ? 'border-paper-primary bg-paper-primary-soft' : 'border-gray-300 bg-white hover:bg-gray-50'"
            class="inline-flex max-w-xs cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition active:bg-gray-100"
          >
            <input v-model="selecionadas" type="checkbox" :value="item.codigo" class="focus-ring h-4 w-4 rounded" />
            <span class="truncate">
              <strong>{{ item.numeroAmostraAghu ?? item.rotulo }}</strong>
              <template v-if="item.descricao"> · {{ item.descricao }}</template>
            </span>
          </label>
          <Button size="sm" variant="secondary" :disabled="etiquetas.length === amostras.length" @click="selecionarTodas">
            Todas
          </Button>
        </div>
        <p v-if="etiquetas.length === 0" class="mt-2 text-sm font-semibold text-paper-danger-strong" role="status">
          Selecione ao menos uma amostra para imprimir.
        </p>
      </fieldset>

      <!-- Conteúdo impresso -->
      <div class="print-area flex-1 overflow-auto p-8">
      <div v-if="tipo === 'ETIQUETAS'" class="flex flex-wrap justify-center gap-6">
          <div v-for="item in etiquetas" :key="item.codigo" class="pagina-etiqueta shadow-lg">
            <EtiquetaFrasco :caso="casoEtiqueta" :item="item" />
          </div>
        </div>
        <div v-else class="flex justify-center">
          <div class="pagina-ficha bg-white p-[12mm] shadow-lg">
            <FichaTrabalho :caso="caso" :emitida-em="emitidaEm" />
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { PrinterIcon } from '@heroicons/vue/24/outline';
import Button from '../Button.vue';
import EtiquetaFrasco from './EtiquetaFrasco.vue';
import FichaTrabalho from './FichaTrabalho.vue';
import type { CasoAp, DadosEtiquetaRecepcao, TipoImpressao } from '../../types/ap';

const props = defineProps<{ show: boolean; caso: CasoAp | null; casoEtiqueta?: DadosEtiquetaRecepcao; tipo: TipoImpressao }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const casoEtiqueta = computed(() => props.casoEtiqueta ?? props.caso!);

const emitidaEm = ref(new Date().toISOString());

/** Uma etiqueta por amostra-raiz do caso. */
const amostras = computed(() => casoEtiqueta.value?.materiais.filter((m) => m.tipoItem === 'AMOSTRA') ?? []);

/** Códigos das amostras marcadas para impressão (todas por padrão). */
const selecionadas = ref<string[]>([]);
const selecionarTodas = () => {
  selecionadas.value = amostras.value.map((m) => m.codigo);
};

/** Etiquetas pré-visualizadas e impressas: só as amostras marcadas, na ordem do caso. */
const etiquetas = computed(() => amostras.value.filter((m) => selecionadas.value.includes(m.codigo)));

const titulo = computed(() =>
  props.tipo === 'ETIQUETAS' ? `Etiquetas de frasco · ${etiquetas.value.length} etiqueta(s)` : 'Ficha de trabalho (A4)',
);

watch(
  () => props.show,
  (aberto) => {
    if (!aberto) return;
    emitidaEm.value = new Date().toISOString();
    selecionarTodas();
  },
  { immediate: true },
);

/** Abre a impressão física do conteúdo pré-visualizado no navegador. */
const imprimir = () => {
  if (!props.caso) return;
  if (props.tipo === 'ETIQUETAS' && etiquetas.value.length === 0) return;
  window.print();
};

const aoTeclar = (evento: KeyboardEvent) => {
  if (evento.key === 'Escape' && props.show) emit('close');
};
onMounted(() => document.addEventListener('keydown', aoTeclar));
onUnmounted(() => document.removeEventListener('keydown', aoTeclar));
</script>
