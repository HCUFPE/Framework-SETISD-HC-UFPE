<template>
  <!-- Etiqueta de frasco 50 × 25 mm. Ordem: nº interno + código, recebimento, solicitação, prontuário, exame. -->
  <div class="etiqueta-frasco">
    <div class="flex items-baseline justify-between gap-1 leading-none">
      <span class="font-extrabold text-[9pt] tracking-tight">{{ caso.numeroInterno }}</span>
      <span v-if="caso.urgente" class="border border-black px-[0.6mm] text-[5.5pt] font-bold leading-none">URG</span>
    </div>
    <Barcode :valor="item.codigo" class="mt-[0.6mm] h-[6.5mm] w-full" />
    <p class="text-center text-[5.5pt] leading-none mt-[0.3mm]">{{ item.codigo }}</p>
    <dl class="mt-[0.6mm] grid grid-cols-[auto_1fr] gap-x-[1mm] text-[6pt] leading-[1.15]">
      <dt class="font-bold">Receb. SAP</dt>
      <dd>{{ formatarDataHora(caso.dataEntradaSap) }}</dd>
      <dt class="font-bold">Solic. AGHU</dt>
      <dd>{{ caso.solicitacao.codigoSolicitacao }}</dd>
      <dt class="font-bold">Prontuário</dt>
      <dd>{{ caso.solicitacao.prontuario }}</dd>
      <dt class="font-bold">Exame</dt>
      <dd class="truncate">{{ caso.solicitacao.nomeExame }}</dd>
    </dl>
  </div>
</template>

<script setup lang="ts">
import Barcode from './Barcode.vue';
import { formatarDataHora } from '../../helpers/formato';
import type { CasoAp, ItemMaterial } from '../../types/ap';

defineProps<{ caso: CasoAp; item: ItemMaterial }>();
</script>

<style scoped>
.etiqueta-frasco {
  width: 50mm;
  height: 25mm;
  padding: 1.2mm 1.6mm;
  overflow: hidden;
  background: #fff;
  color: #000;
  font-family: 'Nunito', ui-sans-serif, system-ui, sans-serif;
  box-sizing: border-box;
}
</style>
