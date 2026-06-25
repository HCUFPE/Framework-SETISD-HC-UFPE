<template>
  <div>
    <Button variant="primary" @click="imprimirTodas">
      <template #icon>
        <PrinterIcon class="h-5 w-5" />
      </template>
      Imprimir todas ({{ items.length }})
    </Button>

    <div class="flex flex-wrap gap-4 mt-4">
      <Qrcode
        v-for="item in items"
        :key="item.identificador"
        :identificador="item.identificador"
        :tipo="item.tipo"
        :rotulo="item.rotulo"
      />
    </div>

    <div class="label-sheet-print grid grid-cols-4 gap-2">
      <div v-for="item in items" :key="'print-' + item.identificador" class="flex items-center gap-2 border border-gray-200 rounded p-2">
        <QrcodeVue :value="item.identificador" :size="PRINT_QR_SIZE[item.tipo]" level="M" />
        <div class="flex flex-col">
          <p class="font-mono text-[10px] font-semibold text-lab-text">{{ item.identificador }}</p>
          <p class="text-[9px] text-gray-500">{{ item.rotulo || TIPO_LABEL[item.tipo] }}</p>
          <p class="text-[9px] text-gray-500">{{ dataImpressao }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import QrcodeVue from 'qrcode.vue';
import { PrinterIcon } from '@heroicons/vue/24/outline';
import Button from '../button/button.vue';
import Qrcode from './qrcode.vue';
import { PRINT_QR_SIZE, TIPO_LABEL, type TipoEtiqueta } from '../../constants/qrcodeSizes.js';
import { formatDateShort } from '../../utils/date';

interface LabelItem {
  identificador: string;
  tipo: TipoEtiqueta;
  rotulo?: string;
}

defineProps<{ items: LabelItem[] }>();

const dataImpressao = computed(() => formatDateShort());

function imprimirTodas() {
  document.body.classList.add('printing-label-sheet');
  window.print();
}

window.addEventListener('afterprint', () => {
  document.body.classList.remove('printing-label-sheet');
});
</script>