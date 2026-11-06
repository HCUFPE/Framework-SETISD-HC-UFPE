<template>
  <div class="w-full rounded-lg shadow-xs">
    <div class="w-full overflow-x-auto">
      <table class="w-full whitespace-no-wrap" :aria-busy="loading || undefined">
        <thead>
          <tr class="text-xs font-semibold tracking-wider text-left text-gray-500 uppercase border-b border-gray-200 bg-gray-50">
            <th v-for="header in headers" :key="header.value" class="px-4 py-2">{{ header.text }}</th>
            <th v-if="$slots.actions" class="px-4 py-2">Ações</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-100">
          <!-- Carregando -->
          <tr v-if="loading">
            <td :colspan="colspan" class="px-6 py-8 text-center text-gray-500">
              <span class="inline-flex items-center gap-2" role="status">
                <svg class="h-5 w-5 animate-spin text-paper-primary" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Carregando...
              </span>
            </td>
          </tr>

          <template v-else>
            <tr
              v-for="item in visibleItems"
              :key="item.id"
              :tabindex="clickable ? 0 : undefined"
              :class="rowClass(item)"
              @click="clickable && emit('row-click', item)"
              @keydown.enter.self="clickable && emit('row-click', item)"
            >
              <td
                v-for="(header, index) in headers"
                :key="header.value"
                :class="{ 'shadow-[inset_4px_0_0_var(--color-paper-danger)]': index === 0 && isHighlighted(item) }"
                class="px-4 py-3 text-sm"
              >
                <slot :name="`cell-${header.value}`" :item="item" :value="item[header.value]">
                  {{ item[header.value] }}
                </slot>
              </td>
              <td v-if="$slots.actions" class="px-4 py-3 text-sm cursor-default" @click.stop @keydown.enter.stop>
                <slot name="actions" :item="item"></slot>
              </td>
            </tr>

            <!-- Vazio -->
            <tr v-if="items.length === 0">
              <td :colspan="colspan" class="px-6 py-4 text-center text-gray-500">
                {{ emptyText }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Paginação -->
    <div
      v-if="isPaginated && !loading && items.length > 0"
      class="flex flex-col sm:flex-row items-center justify-between gap-2 px-4 py-3 bg-white border-t border-gray-100 text-sm text-gray-600"
    >
      <span aria-live="polite">Exibindo {{ rangeStart }}–{{ rangeEnd }} de {{ items.length }}</span>
      <div class="flex items-center gap-2">
        <Button variant="secondary" size="sm" :disabled="page <= 1" aria-label="Página anterior" @click="page--">
          <ChevronLeftIcon class="h-4 w-4 mr-1" /> Anterior
        </Button>
        <span class="px-1 text-xs text-gray-500">Página {{ page }} de {{ totalPages }}</span>
        <Button variant="secondary" size="sm" :disabled="page >= totalPages" aria-label="Próxima página" @click="page++">
          Próxima <ChevronRightIcon class="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends DataTableItem">
import { computed, ref, useSlots, watch } from 'vue';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline';
import Button from './Button.vue';

export interface DataTableHeader {
  text: string;
  value: string;
}

export interface DataTableItem {
  id: number | string;
  [key: string]: any;
}

const props = withDefaults(
  defineProps<{
    headers: DataTableHeader[];
    items: T[];
    /** Torna as linhas clicáveis (mouse e Enter), emitindo `row-click`. */
    clickable?: boolean;
    /** Indica quais linhas recebem destaque (ex.: casos urgentes). */
    highlight?: (item: T) => boolean;
    /** Ativa a paginação no cliente com o tamanho de página informado. */
    pageSize?: number;
    loading?: boolean;
    emptyText?: string;
  }>(),
  {
    clickable: false,
    highlight: undefined,
    pageSize: undefined,
    loading: false,
    emptyText: 'Nenhum dado encontrado.',
  },
);

const emit = defineEmits<{
  (e: 'row-click', item: T): void;
}>();

const slots = useSlots();

const colspan = computed(() => props.headers.length + (slots.actions ? 1 : 0));

const isPaginated = computed(() => props.pageSize !== undefined && props.pageSize > 0);

const page = ref(1);

const totalPages = computed(() =>
  isPaginated.value ? Math.max(1, Math.ceil(props.items.length / props.pageSize!)) : 1,
);

/** Volta à primeira página quando a página atual deixa de existir (ex.: filtro aplicado). */
watch(totalPages, (total) => {
  if (page.value > total) page.value = 1;
});

const visibleItems = computed(() => {
  if (!isPaginated.value) return props.items;
  const start = (page.value - 1) * props.pageSize!;
  return props.items.slice(start, start + props.pageSize!);
});

const rangeStart = computed(() => (props.items.length === 0 ? 0 : (page.value - 1) * props.pageSize! + 1));
const rangeEnd = computed(() => Math.min(page.value * props.pageSize!, props.items.length));

/** Indica se a linha deve receber destaque visual. */
const isHighlighted = (item: T): boolean => !!props.highlight?.(item);

/** Classes da linha conforme destaque e clique. */
const rowClass = (item: T): string[] => {
  const classes = ['text-gray-700', 'transition-colors'];
  if (isHighlighted(item)) classes.push('bg-paper-danger-soft');
  if (props.clickable) {
    classes.push(
      'cursor-pointer',
      'focus-ring',
      '[--focus-ring-offset:-2px]',
      isHighlighted(item) ? 'hover:brightness-95' : 'hover:bg-gray-50',
      'active:bg-gray-100',
    );
  }
  return classes;
};
</script>
