<template>
  <span
    class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold leading-none"
    :class="badgeClass"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type BedStatus = 'disponivel' | 'ocupado' | 'higienizacao' | 'desativado' | 'alta';

const props = defineProps<{
  status: BedStatus;
}>();

const statusConfig: Record<BedStatus, { label: string; className: string }> = {
  disponivel: {
    label: 'Disponivel',
    className: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
  },
  ocupado: {
    label: 'Ocupado',
    className: 'bg-blue-100 text-blue-700 border border-blue-200',
  },
  higienizacao: {
    label: 'Higienizacao',
    className: 'bg-amber-100 text-amber-700 border border-amber-200',
  },
  desativado: {
    label: 'Desativado',
    className: 'bg-slate-100 text-slate-600 border border-slate-300',
  },
  alta: {
    label: 'Alta Solicitada',
    className: 'bg-rose-100 text-rose-700 border border-rose-200',
  },
};

const selectedConfig = computed(() => statusConfig[props.status]);
const label = computed(() => selectedConfig.value.label);
const badgeClass = computed(() => selectedConfig.value.className);
</script>
