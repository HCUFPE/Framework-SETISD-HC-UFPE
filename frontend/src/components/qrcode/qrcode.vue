<template>
  <div ref="cardRef" class="bg-white border border-gray-200 rounded-lg p-3 flex items-center gap-3 w-fit">
    <QrcodeVue class="qr-screen" :value="identificador" :size="96" level="M" />
    <QrcodeVue class="qr-print" :value="identificador" :size="PRINT_QR_SIZE[tipo]" level="M" />

    <div class="flex flex-col gap-1">
      <p class="font-mono text-xs font-semibold text-lab-text">{{ identificador }}</p>
      <p class="text-[11px] text-gray-700">{{ rotulo || TIPO_LABEL[tipo] }}</p>
      <p class="text-[11px] text-gray-700">{{ dataImpressao }}</p>

      <Button variant="primary" :loading="imprimindo" class="qr-no-print text-xs px-2 py-1 mt-1" @click="imprimir">
        <template #icon>
          <PrinterIcon class="h-4 w-4" />
        </template>
        Imprimir
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useToast } from 'vue-toastification';
import QrcodeVue from 'qrcode.vue';
import { PrinterIcon } from '@heroicons/vue/24/outline';
import Button from '../button/button.vue';
import api from '../../services/api';
import { PRINT_QR_SIZE, TIPO_LABEL, type TipoEtiqueta } from '../../constants/qrcodeSizes.js';
import { formatDateShort } from '../../utils/date';

const props = defineProps({
  identificador: { type: String, required: true },
  tipo: { type: String as () => TipoEtiqueta, default: 'frasco' },
  rotulo: { type: String, default: '' },
  dataGeracao: { type: Date, default: () => new Date() },
});

const dataImpressao = computed(() => formatDateShort(props.dataGeracao));

const toast = useToast();
const cardRef = ref<HTMLElement | null>(null);
const imprimindo = ref(false);

async function imprimir() {
  imprimindo.value = true;
  try {
    await api.post('/api/impressoras/imprimir', {
      identificador: props.identificador,
      tipo: props.tipo,
    });
    toast.success('Etiqueta enviada para a impressora.');
  } catch {
    imprimirViaNavegador();
  } finally {
    imprimindo.value = false;
  }
}

function imprimirViaNavegador() {
  cardRef.value?.classList.add('qr-print-target');
  document.body.classList.add('printing-qr-label');
  window.print();
}

function limparEstadoImpressao() {
  document.body.classList.remove('printing-qr-label');
  cardRef.value?.classList.remove('qr-print-target');
}

onMounted(() => {
  window.addEventListener('afterprint', limparEstadoImpressao);
});

onUnmounted(() => {
  window.removeEventListener('afterprint', limparEstadoImpressao);
});
</script>