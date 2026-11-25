<template>
  <div class="bg-white rounded-lg shadow-paper p-5">
    <p class="text-sm font-semibold text-paper-text">{{ titulo }}</p>
    <svg class="mt-3 w-full h-32" viewBox="0 0 300 110" role="img" :aria-label="titulo">
      <template v-if="tipo === 'bar'">
        <rect
          v-for="(barra, indice) in barras"
          :key="indice"
          :x="barra.x"
          :y="barra.y"
          :width="barra.largura"
          :height="barra.altura"
          rx="3"
          class="fill-paper-primary"
        />
        <text
          v-for="(ponto, indice) in serie"
          :key="`rotulo-${indice}`"
          :x="indice * espacamento + espacamento / 2"
          y="106"
          text-anchor="middle"
          class="fill-gray-500 text-[8px]"
        >{{ ponto.rotulo }}</text>
      </template>
      <template v-else>
        <polyline :points="pontos" fill="none" stroke="var(--color-paper-info)" stroke-width="3" />
        <circle
          v-for="(ponto, indice) in serie"
          :key="`ponto-${indice}`"
          :cx="indice * espacamento + espacamento / 2"
          :cy="coordenadaY(ponto.valor)"
          r="3"
          class="fill-paper-info"
        />
        <text
          v-for="(ponto, indice) in serie"
          :key="`eixo-${indice}`"
          :x="indice * espacamento + espacamento / 2"
          y="106"
          text-anchor="middle"
          class="fill-gray-500 text-[8px]"
        >{{ ponto.rotulo }}</text>
      </template>
    </svg>
    <p v-if="serie.length === 0" class="text-xs text-gray-400">Sem dados no período selecionado.</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Serie } from '../types/sae';

const props = withDefaults(defineProps<{
  titulo: string;
  serie: Serie[];
  tipo?: 'bar' | 'line';
}>(), { tipo: 'bar' });

const espacamento = computed(() => (props.serie.length ? 300 / props.serie.length : 300));
const maximo = computed(() => Math.max(1, ...props.serie.map((ponto) => ponto.valor)));

function coordenadaY(valor: number): number {
  return 95 - (valor / maximo.value) * 80;
}

const barras = computed(() => props.serie.map((ponto, indice) => {
  const altura = (ponto.valor / maximo.value) * 80;
  return {
    x: indice * espacamento.value + espacamento.value * 0.2,
    y: 95 - altura,
    altura,
    largura: espacamento.value * 0.6,
  };
}));

const pontos = computed(() => props.serie
  .map((ponto, indice) => `${indice * espacamento.value + espacamento.value / 2},${coordenadaY(ponto.valor)}`)
  .join(' '));
</script>
