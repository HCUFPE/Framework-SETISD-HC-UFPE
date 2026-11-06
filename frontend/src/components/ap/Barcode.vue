<template>
  <svg
    :viewBox="`0 0 ${desenho.total} 100`"
    preserveAspectRatio="none"
    role="img"
    :aria-label="`Código de barras ${valor}`"
    class="block"
    shape-rendering="crispEdges"
  >
    <rect :width="desenho.total" height="100" fill="#fff" />
    <rect v-for="(barra, i) in desenho.barras" :key="i" :x="barra.x" y="0" :width="barra.largura" height="100" fill="#000" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { barrasCode128B } from '../../helpers/barcode';

/**
 * Código de barras Code 128-B em SVG. O tamanho é definido pelo CSS do elemento (largura/altura).
 * Deve codificar apenas identificadores opacos (nº interno ou código de item), nunca dados pessoais.
 */
const props = defineProps<{ valor: string }>();

const desenho = computed(() => barrasCode128B(props.valor));
</script>
