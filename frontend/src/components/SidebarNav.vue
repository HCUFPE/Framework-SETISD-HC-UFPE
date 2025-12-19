<template>
  <aside
    class="fixed inset-y-0 left-0 z-30 flex h-screen flex-col border-r border-slate-200 bg-slate-50 text-slate-800 shadow-sm transition-all duration-200"
    :class="collapsed ? 'w-20' : 'w-64'"
  >
    <div
      class="flex items-center gap-3 px-4 py-6 cursor-pointer select-none transition hover:bg-white"
      @click="$emit('toggle')"
    >
      <div class="flex h-11 w-11 items-center justify-center overflow-hidden rounded-xl bg-white">
        <img src="/hc_ufpe_icon.jpeg" alt="UTI Manager" class="h-11 w-11 object-cover" />
      </div>
      <div v-if="!collapsed" class="leading-tight">
        <p class="text-lg font-bold text-slate-600">UTI Manager</p>
      </div>
    </div>

    <nav class="flex-1 space-y-1 px-2 py-4 overflow-y-auto">
      <RouterLink
        v-for="item in activeItems"
        :key="item.to"
        :to="item.to"
        class="group flex items-center gap-3 rounded-lg font-semibold transition"
        :class="[
          isActive(item.to) ? 'sidebar-active' : 'text-slate-700 hover:bg-white hover:text-slate-900',
          collapsed ? 'justify-center px-0 py-3' : 'px-4 py-3'
        ]"
      >
        <component :is="item.icon" class="h-5 w-5" />
        <span v-if="!collapsed">{{ item.label }}</span>
      </RouterLink>

      <div
        v-for="item in disabledItems"
        :key="item.label"
        class="flex cursor-not-allowed items-center justify-between rounded-lg px-4 py-3 text-sm font-semibold text-slate-400"
        :class="collapsed ? 'justify-center px-0' : ''"
      >
        <span class="flex items-center gap-3">
          <component :is="item.icon" class="h-5 w-5" />
          <span v-if="!collapsed">{{ item.label }}</span>
        </span>
        <span v-if="!collapsed" class="flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-500">
          <Lock class="h-4 w-4" />
          Em breve
        </span>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import {
  Bed,
  FileText,
  LogOut,
  AlertCircle,
  BarChart3,
  History,
  Lock,
} from 'lucide-vue-next';

defineProps<{
  collapsed: boolean;
}>();

defineEmits<{
  toggle: [];
}>();

const route = useRoute();
const isActive = (path: string) => route.path === path;

const activeItems = [
  {
    label: 'Leitos',
    to: '/',
    icon: Bed,
  },
  {
    label: 'Solicitações de leito',
    to: '/solicitacoes',
    icon: FileText,
  },
  {
    label: 'Solicitações de alta',
    to: '/altas',
    icon: LogOut,
  },
  {
    label: 'Alertas',
    to: '/alertas',
    icon: AlertCircle,
  },
  {
    label: 'Indicadores',
    to: '/indicadores',
    icon: BarChart3,
  },
  {
    label: 'Historico',
    to: '/historico',
    icon: History,
  },
];

const disabledItems: Array<{ label: string; icon: any }> = [];
</script>

<style scoped>
.sidebar-active {
  background-color: #1173d4;
  color: #ffffff;
}

.sidebar-active :deep(svg) {
  color: inherit;
}
</style>
