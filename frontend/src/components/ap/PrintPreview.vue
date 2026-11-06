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
            <p class="text-xs text-gray-500">Pré-visualização em escala real · caso {{ caso.numeroInterno }}</p>
          </div>
        </div>
        <div class="flex gap-2">
          <Button variant="secondary" @click="emit('close')">Fechar</Button>
          <Button variant="primary" :loading="imprimindo" @click="imprimir">
            <PrinterIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Imprimir
          </Button>
        </div>
      </div>

      <!-- Conteúdo impresso -->
      <div class="print-area flex-1 overflow-auto p-8">
        <div v-if="tipo === 'ETIQUETAS'" class="flex flex-wrap justify-center gap-6">
          <div v-for="item in amostras" :key="item.codigo" class="pagina-etiqueta shadow-lg">
            <EtiquetaFrasco :caso="caso" :item="item" />
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
import { useToast } from 'vue-toastification';
import { PrinterIcon } from '@heroicons/vue/24/outline';
import Button from '../Button.vue';
import EtiquetaFrasco from './EtiquetaFrasco.vue';
import FichaTrabalho from './FichaTrabalho.vue';
import { mensagemDeErro } from '../../services/ap';
import { useCasosStore } from '../../stores/casos';
import type { CasoAp, TipoImpressao } from '../../types/ap';

const props = defineProps<{ show: boolean; caso: CasoAp | null; tipo: TipoImpressao }>();
const emit = defineEmits<{ (e: 'close'): void; (e: 'impresso'): void }>();

const toast = useToast();
const casosStore = useCasosStore();
const imprimindo = ref(false);
const emitidaEm = ref(new Date().toISOString());

const titulo = computed(() =>
  props.tipo === 'ETIQUETAS' ? `Etiquetas de frasco · ${amostras.value.length} etiqueta(s)` : 'Ficha de trabalho (A4)',
);

/** Uma etiqueta por amostra-raiz do caso. */
const amostras = computed(() => props.caso?.materiais.filter((m) => m.tipoItem === 'AMOSTRA') ?? []);

watch(
  () => props.show,
  (aberto) => {
    if (aberto) emitidaEm.value = new Date().toISOString();
  },
);

/** Registra a impressão no histórico e abre a janela de impressão do navegador. */
const imprimir = async () => {
  if (!props.caso) return;
  imprimindo.value = true;
  try {
    await casosStore.registrarImpressao(props.caso.numeroInterno, props.tipo);
    emit('impresso');
    window.print();
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível registrar a impressão.'));
  } finally {
    imprimindo.value = false;
  }
};

const aoTeclar = (evento: KeyboardEvent) => {
  if (evento.key === 'Escape' && props.show) emit('close');
};
onMounted(() => document.addEventListener('keydown', aoTeclar));
onUnmounted(() => document.removeEventListener('keydown', aoTeclar));
</script>
