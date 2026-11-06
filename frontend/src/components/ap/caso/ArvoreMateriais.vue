<template>
  <ul :class="nivel > 0 ? 'ml-6 border-l border-gray-200 pl-4' : ''" class="space-y-2">
    <li v-for="item in itens" :key="item.codigo">
      <div
        :id="`material-${item.codigo}`"
        :class="item.codigo === destaque ? 'border-paper-warning bg-paper-warning-soft ring-2 ring-paper-warning' : 'border-gray-200 bg-white'"
        class="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-md border px-3 py-2 text-sm"
      >
        <component :is="icones[item.tipoItem]" class="h-5 w-5 shrink-0 text-gray-500" aria-hidden="true" />
        <span class="font-bold tabular-nums text-gray-900">{{ item.codigo }}</span>
        <span class="text-gray-700">{{ item.rotulo }}</span>
        <Badge v-if="item.origem !== 'ROTINA'" variant="info" size="sm">{{ ORIGENS_ITEM[item.origem] }}</Badge>
        <span class="ml-auto text-xs text-gray-500">{{ formatarDataHora(item.criadoEm) }} · {{ item.criadoPor.nome }}</span>
        <span v-if="item.codigo === destaque" class="sr-only">(item lido)</span>
      </div>
      <ArvoreMateriais v-if="item.filhos.length" :itens="item.filhos" :nivel="nivel + 1" :destaque="destaque" />
    </li>
  </ul>
</template>

<script setup lang="ts">
import type { Component } from 'vue';
import { BeakerIcon, CubeIcon, RectangleStackIcon, Squares2X2Icon, StopIcon } from '@heroicons/vue/24/outline';
import Badge from '../../Badge.vue';
import { formatarDataHora } from '../../../helpers/formato';
import type { ItemMaterial, OrigemItemMaterial, TipoItemMaterial } from '../../../types/ap';

/** Árvore recursiva amostra → bloco/cell-block → lâmina. */
withDefaults(defineProps<{ itens: ItemMaterial[]; nivel?: number; destaque?: string }>(), { nivel: 0, destaque: undefined });

const icones: Record<TipoItemMaterial, Component> = {
  AMOSTRA: BeakerIcon,
  FRAGMENTO: Squares2X2Icon,
  BLOCO: CubeIcon,
  CELL_BLOCK: StopIcon,
  LAMINA: RectangleStackIcon,
};

const ORIGENS_ITEM: Record<OrigemItemMaterial, string> = {
  ROTINA: 'Rotina',
  COMPLEMENTAR: 'Solicitação complementar',
  EXTERNA: 'Externa',
  CONGELACAO: 'Congelação',
};
</script>
