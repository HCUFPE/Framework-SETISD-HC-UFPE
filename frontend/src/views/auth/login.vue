<template>
  <div class="w-full max-w-md">
    <Card>
      <template #header>
        <div class="flex items-center justify-center gap-3 mb-1">
          <Microscope class="h-9 w-9 text-lab-primary" :stroke-width="1.5" />
          <span class="text-2xl font-extrabold text-lab-text tracking-tight">Anatomia Patológica</span>
        </div>
        <p class="text-center text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Login
        </p>
      </template>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-5 mt-6">
        <div>
          <label class="form-label" for="username">Usuário</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="form-control"
            placeholder="Ex: EBSERHNET\usuario"
          >
        </div>

        <div>
          <label class="form-label" for="password">Senha</label>
          <div class="relative">
            <input
              id="password"
              v-model="password"
              :type="passwordFieldType"
              class="form-control pr-10"
              placeholder="********"
            >
            <button
              type="button"
              @click="togglePasswordVisibility"
              class="absolute inset-y-0 right-0 px-3 flex items-center text-gray-400 hover:text-gray-600"
            >
              <component :is="passwordFieldType === 'password' ? EyeIcon : EyeSlashIcon" class="h-5 w-5" />
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between text-sm">
          <label class="flex items-center gap-2">
            <input type="checkbox" v-model="rememberMe" class="h-4 w-4 text-lab-primary rounded border-gray-300">
            <span>Lembrar de mim</span>
          </label>
          <router-link to="/esqueci-senha" class="text-lab-primary hover:underline">
            Esqueceu a senha?
          </router-link>
        </div>

        <div class="flex items-center gap-3">
          <Button type="button" variant="default" @click="clearForm" class="w-1/2">
            <template #icon>
              <XCircleIcon class="h-5 w-5" />
            </template>
            Limpar
          </Button>
          <Button type="submit" variant="primary" :loading="loading" class="w-1/2">
            <template #icon>
              <ArrowRightOnRectangleIcon class="h-5 w-5" />
            </template>
            Entrar
          </Button>
        </div>
      </form>

      <div v-if="error" class="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
        {{ error }}
      </div>

      <p class="mt-6 text-center text-sm text-gray-500">
        Não tem conta?
        <router-link to="/cadastro" class="text-lab-primary font-medium hover:underline">
          Criar conta
        </router-link>
      </p>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import Card from '../../components/card/card.vue';
import Button from '../../components/button/button.vue';
import { ArrowRightOnRectangleIcon, EyeIcon, EyeSlashIcon, XCircleIcon } from '@heroicons/vue/24/outline';
import { Microscope } from 'lucide-vue-next';
import { SECTOR_INFO } from '../../constants/sectors';


const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const error = ref('');
const loading = ref(false);
const passwordVisible = ref(false);

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const passwordFieldType = computed(() => passwordVisible.value ? 'text' : 'password');

const togglePasswordVisibility = () => {
  passwordVisible.value = !passwordVisible.value;
};

const clearForm = () => {
  username.value = '';
  password.value = '';
  rememberMe.value = false;
  error.value = '';
};

const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  try {
    await authStore.login(username.value, password.value, rememberMe.value);

    if (typeof route.query.redirect === 'string') {
      await router.push(route.query.redirect);
      return;
    }

    const setor = authStore.user?.setor;
    const destino = setor && setor !== 'admin' ? SECTOR_INFO[setor].path : '/';
    await router.push(destino);
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Não foi possível entrar. Verifique usuário e senha.';
  } finally {
    loading.value = false;
  }
};
</script>