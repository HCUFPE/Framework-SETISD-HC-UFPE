<template>
  <div class="relative">
    <button
      @click.stop="isOpen = !isOpen"
      class="relative z-10 inline-flex h-10 w-10 items-center justify-center rounded-lg text-slate-600 transition-colors duration-150 hover:bg-blue-500 hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-200"
      aria-label="Abrir menu do usuario"
    >
      <User class="h-5 w-5" />
    </button>

    <div v-if="isOpen" @click="isOpen = false" class="fixed inset-0 z-10 h-full w-full"></div>

    <div
      v-if="isOpen"
      class="absolute right-0 mt-2 w-72 overflow-hidden rounded-xl bg-white shadow-xl ring-1 ring-slate-200 z-20"
    >
      <div class="p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
            <UserCircle class="h-8 w-8 text-slate-600" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-base font-semibold text-slate-900">{{ displayName }}</p>
            <p class="truncate text-sm text-slate-500">{{ displayEmail }}</p>
            <p class="truncate text-xs text-slate-500">{{ displayRole }}</p>
          </div>
        </div>
      </div>

      <div class="border-t border-slate-200 p-3 space-y-2 text-sm">
        <button
          class="flex w-full items-center gap-3 rounded-lg px-3 py-2 font-semibold text-slate-700 transition hover:bg-slate-50"
          @click="handleProfile"
        >
          <UserCircle class="h-5 w-5 text-slate-500" />
          Acessar perfil
        </button>
        <button
          class="flex w-full items-center gap-3 rounded-lg px-3 py-2 font-semibold text-red-600 transition hover:bg-red-50"
          @click="handleLogout"
        >
          <LogOut class="h-5 w-5" />
          Sair
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { User, UserCircle, LogOut } from 'lucide-vue-next';
import { useAuthStore } from '../stores/auth';
import { useToast } from 'vue-toastification';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const isOpen = ref(false);
const toast = useToast();

const displayName = computed(() => authStore.user?.givenName?.[0] || authStore.user?.username || 'Usuario');
const displayEmail = computed(() => authStore.user?.userPrincipalName?.[0] || 'N/A');
const displayRole = computed(() => authStore.user?.title?.[0] || 'Cargo nao informado');

const handleLogout = async () => {
  await authStore.logout(router);
  toast.success('Logout realizado com sucesso!');
  isOpen.value = false;
};

const handleProfile = () => {
  toast.info('Tela de perfil em desenvolvimento.');
};

// Close dropdown on navigation
watch(() => route.path, () => {
  isOpen.value = false;
});
</script>
