<template>
  <div class="relative h-screen overflow-hidden md:flex">
    <!-- Mobile Menu Header -->
    <div class="bg-paper-sidebar text-gray-100 flex justify-between md:hidden shrink-0">
      <router-link to="/" class="block p-4 text-white font-bold">{{ SYSTEM_TITLE }}</router-link>
      <button @click="sidebarOpen = !sidebarOpen" class="p-4 focus:outline-none focus:bg-paper-active-link" aria-label="Abrir menu">
        <Bars3Icon class="h-6 w-6" />
      </button>
    </div>

    <!-- Sidebar (Expansível / Recolhível) -->
    <aside
      :class="[
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        isCollapsed ? 'md:w-20' : 'md:w-64'
      ]"
      class="bg-paper-sidebar text-gray-100 pt-7 pb-2 px-2 absolute inset-y-0 left-0 transform md:relative md:translate-x-0 transition-all duration-300 ease-in-out z-20 h-full shrink-0 flex flex-col justify-between"
    >
      <div class="overflow-y-auto">
        <div
          @click="toggleSidebar"
          title="Clique para recolher / expandir o menu"
          class="cursor-pointer text-white flex items-center space-x-3 px-3 mb-6 hover:opacity-90 transition duration-150 group"
        >
          <CubeTransparentIcon class="h-8 w-8 shrink-0 group-hover:scale-105 transition-transform" />
          <span v-if="!isCollapsed" class="text-xl font-extrabold leading-snug break-words select-none">
            {{ SYSTEM_TITLE }}
          </span>
        </div>

        <div class="px-3 my-4">
          <div class="border-t border-white border-opacity-20"></div>
        </div>

        <nav class="space-y-1">
          <div v-for="grupo in gruposVisiveis" :key="grupo.titulo" class="pt-2">
            <p v-if="!isCollapsed && grupo.titulo" class="px-4 pb-1 text-[10px] font-bold uppercase tracking-wider text-gray-400">
              {{ grupo.titulo }}
            </p>
            <router-link
              v-for="item in grupo.itens"
              :key="item.rota"
              :to="item.rota"
              :title="isCollapsed ? item.nome : ''"
              :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
              class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
            >
              <component :is="item.icone" class="h-6 w-6 shrink-0" />
              <span v-if="!isCollapsed" class="truncate">{{ item.nome }}</span>
            </router-link>
          </div>
        </nav>

        <div v-if="USAR_MOCKS && !isCollapsed" class="px-3 mt-5">
          <label for="perfil-mock" class="block text-[10px] font-bold uppercase tracking-wider text-gray-400">
            Visualizar como (mocks)
          </label>
          <select id="perfil-mock" :value="perfilStore.atual" class="mt-1 w-full rounded bg-white/10 px-2 py-1 text-xs text-white" @change="definirPerfil">
            <option v-for="perfil in PERFIS" :key="perfil" :value="perfil" class="text-gray-800">
              {{ ROTULOS_PERFIL[perfil] }}
            </option>
          </select>
        </div>
      </div>

      <!-- Rodapé de Versão da Sidebar -->
      <div v-if="!isCollapsed" class="px-4 pt-3 pb-1 border-t border-white/10 text-xs text-gray-400 mt-auto truncate transition-opacity duration-200">
        <p class="font-semibold text-gray-200 truncate">{{ APP_NAME }}</p>
        <p class="text-[11px] text-gray-400 truncate">Versão {{ APP_VERSION }} | HC-UFPE</p>
      </div>
      <div v-else class="px-2 pt-3 pb-1 border-t border-white/10 text-[10px] text-center text-gray-400 mt-auto">
        v{{ APP_VERSION }}
      </div>
    </aside>

    <!-- Content -->
    <div class="flex-1 flex flex-col bg-paper-bg overflow-y-auto h-full">
      <header class="flex justify-between items-center p-6 bg-white/80 backdrop-blur-md border-b border-gray-300 sticky top-0 z-10">
        <div>
          <h1 class="text-2xl font-semibold text-paper-text">{{ $route.name }}</h1>
        </div>
        <div>
          <router-link v-if="!authStore.isAuthenticated" to="/login">
            <Button variant="primary">
              <template #icon>
                <ArrowRightOnRectangleIcon class="h-5 w-5" />
              </template>
              Login
            </Button>
          </router-link>
          <ProfileDropdown v-else />
        </div>
      </header>
      <main class="flex-1">
        <div class="container py-4 md:py-6">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, type Component } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  HomeIcon,
  CubeIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  TableCellsIcon,
  AdjustmentsHorizontalIcon,
  UsersIcon,
  ArrowPathIcon,
  CubeTransparentIcon,
  Bars3Icon,
  ArrowRightOnRectangleIcon,
  CalendarDaysIcon,
} from '@heroicons/vue/24/outline';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import Button from '../components/Button.vue';
import { useAuthStore } from '../stores/auth';
import { usePerfilStore } from '../stores/perfil';
import { APP_VERSION, APP_NAME, SYSTEM_TITLE } from '../config/version';
import { USAR_MOCKS } from '../config/mocks';
import { papeisAgendamentos, possuiPapel } from '../router';
import { PERFIS, ROTULOS_PERFIL, type Perfil } from '../types/sae';

interface ItemMenu {
  rota: string;
  nome: string;
  icone: Component;
  perfis: typeof papeisAgendamentos;
}

interface GrupoMenu {
  titulo: string;
  itens: ItemMenu[];
}

const sidebarOpen = ref(false);
const isCollapsed = ref(false);

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const perfilStore = usePerfilStore();

const grupos: GrupoMenu[] = [
  {
    titulo: 'Operação',
    itens: [
      { rota: '/fila', nome: 'Fila de Marcação', icone: TableCellsIcon, perfis: ['OPERADOR', 'CHEFIA', 'AREA_GESTORA'] },
      { rota: '/agendamentos', nome: 'Agendamentos', icone: CalendarDaysIcon, perfis: papeisAgendamentos },
    ],
  },
  {
    titulo: 'Gestão',
    itens: [
      { rota: '/painel', nome: 'Painel de Gestão', icone: ChartBarIcon, perfis: ['CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'] },
      { rota: '/relatorios', nome: 'Relatórios', icone: DocumentTextIcon, perfis: ['CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'] },
      { rota: '/criterios', nome: 'Critérios de Priorização', icone: AdjustmentsHorizontalIcon, perfis: ['AREA_GESTORA'] },
      { rota: '/equipe', nome: 'Equipe e Perfis', icone: UsersIcon, perfis: ['AREA_GESTORA', 'ADMIN_TI'] },
    ],
  },
  {
    titulo: 'Sistema',
    itens: [
      { rota: '/', nome: 'Início', icone: HomeIcon, perfis: PERFIS },
      { rota: '/configuracoes', nome: 'Configurações', icone: Cog6ToothIcon, perfis: PERFIS },
      { rota: '/integracoes', nome: 'Integrações', icone: ArrowPathIcon, perfis: ['AREA_GESTORA', 'ADMIN_TI'] },
      { rota: '/componentes', nome: 'Componentes', icone: CubeIcon, perfis: PERFIS },
    ],
  },
];

const gruposVisiveis = computed(() => grupos
  .map((grupo) => ({ ...grupo, itens: grupo.itens.filter((item) => possuiPapel(authStore, item.perfis)) }))
  .filter((grupo) => grupo.itens.length > 0));

function toggleSidebar(): void {
  isCollapsed.value = !isCollapsed.value;
}

function definirPerfil(evento: Event): void {
  perfilStore.definir((evento.target as HTMLSelectElement).value as Perfil);
  const perfis = route.meta.roles as typeof papeisAgendamentos | undefined;
  if (perfis && perfis.length > 0 && !possuiPapel(authStore, perfis)) {
    void router.push({ name: 'Início' });
  }
}

watch(() => route.path, () => {
  sidebarOpen.value = false;
});
</script>
