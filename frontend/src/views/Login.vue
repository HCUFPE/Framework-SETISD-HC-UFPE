<template>
  <div class="w-full max-w-md">
    <Card>
      <template #header>
        <h1 class="text-xl font-semibold text-center">Login</h1>
      </template>
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label class="block text-sm font-bold mb-2" for="username">
            Usuário
          </label>
          <input v-model="username" class="shadow-inner appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline" id="username" type="text" placeholder="E.g., EBSERHNET\\user">
        </div>
        <div class="mb-6">
          <label class="block text-sm font-bold mb-2" for="password">
            Senha
          </label>
          <div class="relative">
            <input v-model="password" class="shadow-inner appearance-none border rounded w-full py-2 px-3 pr-10 leading-tight focus:outline-none focus:shadow-outline" id="password" :type="passwordFieldType" placeholder="******************">
            <button type="button" @click="togglePasswordVisibility" class="absolute inset-y-0 right-0 px-3 flex items-center text-gray-500">
              <component :is="passwordFieldType === 'password' ? EyeIcon : EyeSlashIcon" class="h-5 w-5" />
            </button>
          </div>
        </div>
        <div class="mb-6">
          <label class="flex items-center">
            <input type="checkbox" v-model="rememberMe" class="form-checkbox h-5 w-5 text-orange-600">
            <span class="ml-2 text-sm">Lembrar de mim</span>
          </label>
        </div>
        <div class="flex items-center justify-center space-x-4">
          <Button type="button" variant="secondary" @click="clearForm" class="w-1/2 bg-gray-500 hover:bg-gray-600">
            <template #icon>
              <XCircleIcon class="h-5 w-5" />
            </template>
            Limpar
          </Button>
          <Button type="submit" variant="primary" :disabled="loading" class="w-1/2">
            <template #icon>
              <ArrowRightOnRectangleIcon class="h-5 w-5" />
            </template>
            Entrar
          </Button>
        </div>
      </form>
    </Card>
    <div v-if="error" class="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Erro: </strong>
      <span class="block sm:inline">{{ error }}</span>
    </div>

    <!-- Rodapé de Versão -->
    <div class="mt-6 text-center text-xs text-gray-400 space-y-1">
      <p class="font-semibold text-gray-300">Hospital das Clínicas da UFPE (HC-UFPE / EBSERH)</p>
      <p class="text-gray-400">Setor de Tecnologia da Informação e Saúde Digital — SETISD | Versão 1.0.0</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';
import { ArrowRightOnRectangleIcon, EyeIcon, EyeSlashIcon, XCircleIcon } from '@heroicons/vue/24/outline';

const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const error = ref('');
const loading = ref(false);
const passwordVisible = ref(false);

const router = useRouter();
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
    await router.push('/');
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'An unknown error occurred';
  } finally {
    loading.value = false;
  }
};
</script>
