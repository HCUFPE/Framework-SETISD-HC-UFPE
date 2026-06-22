<template>
  <div class="w-full">
    <div class="w-full overflow-x-auto rounded-lg shadow-xs">
      <table class="w-full whitespace-no-wrap">
        <thead>
          <tr class="text-xs font-semibold tracking-wider text-left text-gray-500 uppercase border-b border-gray-200 bg-gray-50">
            <th v-for="header in headers" :key="header.value" class="px-4 py-2">{{ header.text }}</th>
            <th v-if="$slots.actions" class="px-4 py-2">Ações</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-100">
          <tr v-for="item in paginatedItems" :key="item.id" class="text-gray-700 hover:bg-gray-100">
            <td v-for="header in headers" :key="header.value" class="px-4 py-3 text-sm">
              <slot :name="`item-${header.value}`" :item="item">
                {{ item[header.value] }}
              </slot>
            </td>
            <td v-if="$slots.actions" class="px-4 py-3 text-sm">
              <slot name="actions" :item="item"></slot>
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td :colspan="headers.length + ($slots.actions ? 1 : 0)" class="px-6 py-4 text-center text-gray-500">
              Nenhum dado encontrado.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="totalPages > 1" class="flex items-center justify-center gap-4 mt-4">
      <button
        @click="currentPage--"
        :disabled="currentPage === 1"
        class="p-2 rounded-md text-gray-500 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
      >
        <ChevronLeftIcon class="h-5 w-5" />
      </button>

      <span class="text-sm text-gray-500">
        Página {{ currentPage }} de {{ totalPages }}
      </span>

      <button
        @click="currentPage++"
        :disabled="currentPage === totalPages"
        class="p-2 rounded-md text-gray-500 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
      >
        <ChevronRightIcon class="h-5 w-5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline';

interface Header {
  text: string;
  value: string;
}

interface Item {
  id: number | string;
  [key: string]: any;
}

const props = defineProps({
  headers: {
    type: Array as () => Header[],
    required: true,
  },
  items: {
    type: Array as () => Item[],
    required: true,
  },
  pageSize: {
    type: Number,
    default: 7,
  },
});

const currentPage = ref(1);

const totalPages = computed(() => Math.max(1, Math.ceil(props.items.length / props.pageSize)));

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize;
  return props.items.slice(start, start + props.pageSize);
});

// Se a lista de itens mudar (filtro, busca, etc.) e a página atual deixar de existir, volta pra página 1.
watch(() => props.items.length, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = 1;
  }
});
</script>