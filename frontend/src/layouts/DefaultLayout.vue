<template>
  <div class="relative h-screen overflow-hidden md:flex">
    <!-- Mobile Menu -->
    <div class="bg-paper-sidebar text-gray-100 flex justify-between md:hidden shrink-0">
      <router-link to="/" class="block p-4 text-white font-bold">Nome do Sistema</router-link>
      <button @click="sidebarOpen = !sidebarOpen" class="p-4 focus:outline-none focus:bg-paper-active-link">
        <Bars3Icon class="h-6 w-6" />
      </button>
    </div>

    <!-- Sidebar -->
    <aside :class="{ '-translate-x-full': !sidebarOpen }" class="bg-paper-sidebar text-gray-100 w-64 pt-7 pb-2 px-2 absolute inset-y-0 left-0 transform md:relative md:translate-x-0 transition duration-200 ease-in-out z-20 h-full shrink-0 flex flex-col justify-between">
      <div>
        <div @click="() => router.push('/')" class="cursor-pointer text-white flex items-center space-x-2 px-4 mb-6">
          <CubeTransparentIcon class="h-8 w-8"/>
          <span class="text-2xl font-extrabold">{{ SYSTEM_TITLE }}</span>
        </div>
        <div class="px-4 my-4">
          <div class="border-t border-white border-opacity-20"></div>
        </div>

        <nav class="space-y-2">
          <router-link to="/" class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-paper-active-link hover:text-white">
            <HomeIcon class="h-6 w-6"/>
            <span>Início</span>
          </router-link>

          <router-link to="/componentes" class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-paper-active-link hover:text-white">
            <CubeIcon class="h-6 w-6" />
            <span>Componentes</span>
          </router-link>

          <router-link v-if="authStore.isAuthenticated" to="/exemplo" class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-paper-active-link hover:text-white">
            <DocumentTextIcon class="h-6 w-6" />
            <span>Exemplo</span>
          </router-link>
          
          <router-link v-if="authStore.isAuthenticated" to="/configuracoes" class="flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 hover:bg-paper-active-link hover:text-white">
            <Cog6ToothIcon class="h-6 w-6"/>
            <span>Configurações</span>
          </router-link>
        </nav>
      </div>

      <!-- Rodapé de Versão da Sidebar -->
      <div class="px-4 pt-3 pb-1 border-t border-white/10 text-xs text-gray-400 mt-auto">
        <p class="font-semibold text-gray-200">{{ APP_NAME }}</p>
        <p class="text-[11px] text-gray-400">Versão {{ APP_VERSION }} | HC-UFPE</p>
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
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  HomeIcon,
  CubeIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  CubeTransparentIcon,
  Bars3Icon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/vue/24/outline';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import Button from '../components/Button.vue';
import { useAuthStore } from '../stores/auth';
import { APP_VERSION, APP_NAME, SYSTEM_TITLE } from '../config/version';

const sidebarOpen = ref(false);
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();


// Close sidebar on route change
watch(() => route.path, () => {
  sidebarOpen.value = false;
});
</script>