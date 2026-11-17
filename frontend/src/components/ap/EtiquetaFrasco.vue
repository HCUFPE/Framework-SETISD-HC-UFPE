<template>
  <!--
    Etiqueta de frasco 50 × 25 mm. Ordem: nº interno + amostra + código, nome completo do paciente,
    recebimento, solicitação, prontuário e exame.
  -->
  <div class="etiqueta-frasco">
    <div class="flex items-baseline justify-between gap-1 leading-none">
      <span class="font-extrabold text-[9pt] tracking-tight">{{ caso.numeroInterno }}</span>
      <span class="flex items-baseline gap-[0.8mm]">
        <span v-if="item.numeroAmostraAghu" class="text-[7pt] font-extrabold">Am. {{ item.numeroAmostraAghu }}</span>
        <span v-if="caso.urgente" class="border border-black px-[0.6mm] text-[5.5pt] font-bold leading-none">URG</span>
      </span>
    </div>
    <Barcode :valor="item.codigo" class="mt-[0.5mm] h-[4.6mm] w-full" />
    <p class="text-center text-[5pt] leading-none mt-[0.4mm]">{{ item.codigo }}</p>
    <!-- Nome completo: sem truncar, até 2 linhas, fonte menor para nomes longos -->
    <p :class="nomeLongo ? 'text-[5.5pt]' : 'text-[6.5pt]'" class="nome-paciente mt-[0.5mm] font-extrabold uppercase">
      {{ caso.solicitacao.nomePaciente || NAO_INFORMADO }}
    </p>
    <dl class="mt-[0.4mm] grid grid-cols-[auto_1fr_auto_1fr] gap-x-[0.8mm] text-[5.5pt] leading-[1.2]">
      <dt class="font-bold">Receb.</dt>
      <dd>{{ formatarData(caso.dataEntradaSap) }}</dd>
      <dt class="font-bold">Solic.</dt>
      <dd class="tabular-nums">{{ caso.solicitacao.codigoSolicitacao }}</dd>
      <dt class="font-bold">Pront.</dt>
      <dd class="tabular-nums">{{ caso.solicitacao.prontuario || '—' }}</dd>
      <dt class="font-bold">Exame</dt>
      <dd>{{ caso.solicitacao.siglaExame }}</dd>
    </dl>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import Barcode from './Barcode.vue';
import { NAO_INFORMADO } from '../../constants/ap';
import { formatarData } from '../../helpers/formato';
import type { CasoAp, ItemMaterial } from '../../types/ap';

const props = defineProps<{ caso: CasoAp; item: ItemMaterial }>();

/** Acima deste tamanho o nome usa a fonte menor para caber em 2 linhas sem cortar. */
const LIMITE_NOME_CURTO = 40;
const nomeLongo = computed(() => props.caso.solicitacao.nomePaciente.length > LIMITE_NOME_CURTO);
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
.nome-paciente {
  line-height: 1.1;
  overflow-wrap: anywhere;
  word-break: normal;
}
</style>
