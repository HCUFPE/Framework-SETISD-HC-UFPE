<template>
  <div class="relative h-screen overflow-hidden md:flex">
    <!-- Mobile Menu -->
    <div class="bg-lab-sidebar text-gray-100 flex justify-between md:hidden shrink-0">
      <router-link to="/" class="flex items-center gap-2 p-4 text-white font-bold">
        <Microscope class="h-6 w-6" :stroke-width="1.5" />
        Anatomia Patológica
      </router-link>
      <button @click="sidebarOpen = !sidebarOpen" class="p-4 focus:outline-none focus:bg-lab-active-link">
        <Bars3Icon class="h-6 w-6" />
      </button>
    </div>

    <!-- Sidebar -->
    <aside :class="{ '-translate-x-full': !sidebarOpen }" class="bg-lab-sidebar text-gray-100 w-56 space-y-6 py-7 px-2 absolute inset-y-0 left-0 transform md:relative md:translate-x-0 transition duration-200 ease-in-out z-20 h-full shrink-0">
      <div @click="() => router.push('/')" class="cursor-pointer text-white flex items-center space-x-2 px-4">
        <Microscope class="h-8 w-8 shrink-0" :stroke-width="1.5" />
        <span class="text-lg font-extrabold leading-tight">Anatomia Patológica</span>
      </div>

      <div class="px-4 my-6">
        <div class="border-t border-white border-opacity-20"></div>
      </div>

      <nav class="space-y-1">
        <router-link to="/" class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-lab-active-link hover:text-white">
          <Squares2X2Icon class="h-6 w-6" />
          <span>Dashboard</span>
        </router-link>

        <router-link to="/escaneamento" class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-lab-active-link hover:text-white">
          <QrCodeIcon class="h-6 w-6" />
          <span>Escaneamento</span>
        </router-link>

        <router-link
          v-if="sectorNavItem"
          :to="sectorNavItem.path"
          class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-lab-active-link hover:text-white"
        >
          <component :is="sectorNavItem.icon" class="h-6 w-6" />
          <span>{{ sectorNavItem.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- Content -->
    <div class="flex-1 flex flex-col bg-lab-bg overflow-y-auto h-full">
      <header class="flex justify-between items-center p-6 bg-white/80 backdrop-blur-md border-b border-gray-300 sticky top-0 z-10">
        <div>
          <h1 class="text-2xl font-semibold text-lab-text">{{ $route.meta.title || $route.name }}</h1>
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
import { ref, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Squares2X2Icon,
  QrCodeIcon,
  UsersIcon,
  BeakerIcon,
  Bars3Icon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/vue/24/outline';
import { Microscope } from 'lucide-vue-next';
import ProfileDropdown from '../components/profileDropdown/profileDropdown.vue';
import Button from '../components/button/button.vue';
import { useAuthStore } from '../stores/auth.js';

const sidebarOpen = ref(false);
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// Mapeia o setor do usuário pra rota/ícone/label do 3º item do menu.
// authStore.user.setor ainda não é preenchido (login não está pronto) — vai vir do backend.
const SECTOR_NAV: Record<string, { path: string; label: string; icon: any }> = {
  recepcao: 
  { 
    path: '/recepcao', 
    label: 'Recepção', 
    icon: UsersIcon 
  },
  macroscopia: 
  { 
    path: '/macroscopia', 
    label: 'Macroscopia', 
    icon: BeakerIcon },
  microscopia: 
  { 
    path: '/microscopia', 
    label: 'Microscopia', 
    icon: BeakerIcon 
  },
  processamento_tecnico: 
  { path: '/processamento-tecnico', 
  label: 'Processamento Técnico', 
  icon: BeakerIcon 
},
};

const sectorNavItem = computed(() => {
  const setor = authStore.user?.setor;
  return setor ? SECTOR_NAV[setor] : null;
});

watch(() => route.path, () => {
  sidebarOpen.value = false;
});
</script>