<template>
  <div class="relative h-screen overflow-hidden md:flex">
    <!-- Mobile Menu Header -->
    <div class="bg-paper-sidebar text-gray-100 flex justify-between md:hidden shrink-0">
      <router-link to="/" :title="SYSTEM_TITLE" class="focus-ring [--focus-ring-offset:-2px] block min-w-0 truncate p-4 text-white font-bold hover:text-gray-200 active:text-gray-300 transition">{{ SYSTEM_TITLE }}</router-link>
      <button
        type="button"
        aria-label="Abrir ou fechar o menu"
        :aria-expanded="sidebarOpen"
        @click="sidebarOpen = !sidebarOpen"
        class="focus-ring [--focus-ring-offset:-2px] p-4 hover:bg-paper-active-link active:bg-black/30 transition-colors"
      >
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
      <div>
        <!-- Identidade do sistema (informativa) + botão próprio para recolher/expandir o menu -->
        <div
          :class="isCollapsed ? 'flex-col items-center gap-3' : 'items-start gap-2'"
          class="flex mb-6 px-1"
        >
          <p v-if="!isCollapsed" class="flex-1 min-w-0 px-2 py-1 text-base font-extrabold leading-snug break-words text-white">
            {{ SYSTEM_TITLE }}
          </p>
          <span v-else class="sr-only">{{ SYSTEM_TITLE }}</span>
          <button
            type="button"
            :aria-label="isCollapsed ? 'Expandir menu' : 'Recolher menu'"
            :title="isCollapsed ? 'Expandir menu' : 'Recolher menu'"
            :aria-expanded="!isCollapsed"
            class="focus-ring hidden md:inline-flex shrink-0 items-center justify-center rounded-md p-2 text-gray-300 transition hover:bg-white/10 hover:text-white active:bg-white/20"
            @click="toggleSidebar"
          >
            <PanelRight class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div class="px-3 my-4">
          <div class="border-t border-white border-opacity-20"></div>
        </div>

        <!-- Links de Navegação, agrupados em seções -->
        <nav aria-label="Menu principal" class="space-y-5">
          <div v-for="secao in secoesVisiveis" :key="secao.titulo">
            <p
              v-if="!isCollapsed"
              class="px-4 mb-2 text-[11px] font-bold uppercase tracking-wider text-gray-400 select-none"
            >
              {{ secao.titulo }}
            </p>
            <div v-else class="mx-3 mb-2 border-t border-white/20" aria-hidden="true"></div>

            <div class="space-y-1">
              <router-link
                v-for="item in secao.itens"
                :key="item.chave"
                :to="item.para"
                active-class=""
                exact-active-class=""
                :title="isCollapsed ? item.rotulo : ''"
                :aria-current="itemAtivo(item) ? 'page' : undefined"
                :class="[
                  isCollapsed ? 'justify-center px-2' : 'px-4',
                  itemAtivo(item) ? 'bg-paper-active-link text-white' : '',
                ]"
                class="focus-ring relative flex items-center gap-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white active:bg-black/30"
              >
                <component :is="item.icone" class="h-6 w-6 shrink-0" aria-hidden="true" />
                <span v-if="!isCollapsed" class="flex-1 min-w-0 leading-snug">{{ item.rotulo }}</span>
                <span
                  v-if="item.contador && !isCollapsed"
                  class="rounded-full bg-paper-warning px-2 py-0.5 text-xs font-bold text-gray-900"
                  :aria-label="`${item.contador} solicitações aguardando recebimento`"
                >
                  {{ item.contador }}
                </span>
                <span
                  v-else-if="item.contador"
                  class="absolute top-1 right-2 min-w-4 rounded-full bg-paper-warning px-1 text-[10px] font-bold leading-4 text-center text-gray-900"
                  :aria-label="`${item.contador} solicitações aguardando recebimento`"
                >
                  {{ item.contador }}
                </span>
              </router-link>
            </div>
          </div>
        </nav>
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
      <header class="flex flex-wrap justify-between items-center gap-4 p-6 bg-white/80 backdrop-blur-md border-b border-gray-300 sticky top-0 z-10">
        <div class="min-w-0">
          <h1 class="text-2xl font-semibold text-paper-text truncate">{{ $route.name }}</h1>
        </div>
        <div class="flex items-center gap-4 ml-auto">
          <BuscaCasoField v-if="authStore.isAuthenticated" />
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
import { useRoute } from 'vue-router';
import {
  HomeIcon,
  CubeIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  Bars3Icon,
  ArrowRightOnRectangleIcon,
  SparklesIcon,
  InboxArrowDownIcon,
  MagnifyingGlassIcon,
  ArrowUturnLeftIcon,
} from '@heroicons/vue/24/outline';
import { PanelRight } from 'lucide-vue-next';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import Button from '../components/Button.vue';
import BuscaCasoField from '../components/ap/BuscaCasoField.vue';
import { useAuthStore } from '../stores/auth';
import { useRecepcaoStore } from '../stores/recepcao';
import { APP_VERSION, APP_NAME, SYSTEM_TITLE } from '../config/version';

interface ItemMenu {
  /** Identificador comparado com `route.meta.menu`. */
  chave: string;
  rotulo: string;
  para: string;
  icone: Component;
  /** Exibido apenas para usuários autenticados. */
  requerLogin?: boolean;
  contador?: number;
}

interface SecaoMenu {
  titulo: string;
  itens: ItemMenu[];
}

const sidebarOpen = ref(false);
const isCollapsed = ref(false);

const route = useRoute();
const authStore = useAuthStore();
const recepcaoStore = useRecepcaoStore();

const secoes = computed<SecaoMenu[]>(() => [
  {
    titulo: 'Recepção',
    itens: [
      {
        chave: 'recepcao',
        rotulo: 'Recepção de amostras',
        para: '/recepcao',
        icone: InboxArrowDownIcon,
        requerLogin: true,
        contador: recepcaoStore.contagemPendentes,
      },
      { chave: 'consulta', rotulo: 'Consulta de casos', para: '/casos', icone: MagnifyingGlassIcon, requerLogin: true },
      {
        chave: 'devolucoes',
        rotulo: 'Rejeições e devoluções',
        para: '/rejeicoes-devolucoes',
        icone: ArrowUturnLeftIcon,
        requerLogin: true,
      },
    ],
  },
  {
    titulo: 'Outros',
    itens: [
      { chave: 'inicio', rotulo: 'Início', para: '/', icone: HomeIcon },
      { chave: 'componentes', rotulo: 'Componentes', para: '/componentes', icone: CubeIcon },
      // Vitrine das mudanças do change evolve-base-components.
      { chave: 'novidades', rotulo: 'Novidades dos Componentes', para: '/novidades-componentes', icone: SparklesIcon },
      { chave: 'exemplo', rotulo: 'Exemplo', para: '/exemplo', icone: DocumentTextIcon, requerLogin: true },
      { chave: 'configuracoes', rotulo: 'Configurações', para: '/configuracoes', icone: Cog6ToothIcon, requerLogin: true },
    ],
  },
]);

/** Seções com os itens permitidos para a sessão atual (seções vazias são omitidas). */
const secoesVisiveis = computed(() =>
  secoes.value
    .map((secao) => ({
      ...secao,
      itens: secao.itens.filter((item) => !item.requerLogin || authStore.isAuthenticated),
    }))
    .filter((secao) => secao.itens.length > 0),
);

/** Item ativo: o da rota atual ou o indicado em `meta.menu` (subtelas). */
const itemAtivo = (item: ItemMenu): boolean => route.meta.menu === item.chave || route.path === item.para;

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

/** Mantém o contador de solicitações pendentes atualizado a cada navegação. */
const atualizarContador = () => {
  if (authStore.isAuthenticated) recepcaoStore.atualizarContagem();
};

// Close mobile sidebar on route change
watch(() => route.path, () => {
  sidebarOpen.value = false;
  atualizarContador();
}, { immediate: true });
</script>