<template>
  <div>
    <div role="tablist" class="flex gap-1 overflow-x-auto overflow-y-hidden shadow-[inset_0_-1px_0_var(--color-gray-200)]">
      <button
        v-for="(tab, index) in tabs"
        :id="tabId(tab.key)"
        :key="tab.key"
        :ref="(el) => setTabRef(el as HTMLButtonElement | null, index)"
        type="button"
        role="tab"
        :aria-selected="tab.key === modelValue"
        :aria-controls="panelId(tab.key)"
        :tabindex="tab.key === modelValue ? 0 : -1"
        :class="
          tab.key === modelValue
            ? 'border-paper-primary text-paper-primary-strong'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
        "
        class="focus-ring [--focus-ring-offset:-2px] inline-flex items-center gap-2 whitespace-nowrap rounded-t-md border-b-2 px-4 py-2.5 text-sm font-semibold transition active:bg-gray-100"
        @click="select(tab.key)"
        @keydown="onKeydown($event, index)"
      >
        {{ tab.label }}
        <span
          v-if="tab.count !== undefined"
          :class="tab.key === modelValue ? 'bg-paper-primary-soft text-paper-primary-strong' : 'bg-gray-100 text-gray-600'"
          class="rounded-full px-2 py-0.5 text-xs font-bold"
        >
          {{ tab.count }}
        </span>
      </button>
    </div>

    <template v-for="tab in tabs" :key="tab.key">
      <div
        v-if="tab.key === modelValue"
        :id="panelId(tab.key)"
        role="tabpanel"
        :aria-labelledby="tabId(tab.key)"
        tabindex="0"
        class="focus-ring pt-4 rounded-sm"
      >
        <slot :name="tab.key"></slot>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { nextTick, useId } from 'vue';

export interface TabItem {
  key: string;
  label: string;
  count?: number;
}

const props = defineProps<{
  tabs: TabItem[];
  /** Chave da aba ativa (`v-model`). */
  modelValue: string;
}>();

const emit = defineEmits<{ (e: 'update:modelValue', key: string): void }>();

const uid = useId();
const tabId = (key: string) => `${uid}-tab-${key}`;
const panelId = (key: string) => `${uid}-panel-${key}`;

const tabRefs: (HTMLButtonElement | null)[] = [];
const setTabRef = (el: HTMLButtonElement | null, index: number) => {
  tabRefs[index] = el;
};

/** Ativa a aba informada. */
const select = (key: string) => {
  if (key !== props.modelValue) emit('update:modelValue', key);
};

/** Setas esquerda/direita (e Home/End) movem o foco e ativam a aba vizinha. */
const onKeydown = async (event: KeyboardEvent, index: number) => {
  const last = props.tabs.length - 1;
  let next: number;
  if (event.key === 'ArrowRight') next = index === last ? 0 : index + 1;
  else if (event.key === 'ArrowLeft') next = index === 0 ? last : index - 1;
  else if (event.key === 'Home') next = 0;
  else if (event.key === 'End') next = last;
  else return;

  event.preventDefault();
  select(props.tabs[next].key);
  await nextTick();
  tabRefs[next]?.focus();
};
</script>
