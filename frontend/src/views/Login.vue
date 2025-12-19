<template>
  <div class="w-full min-h-screen bg-gradient-to-br from-blue-50 via-slate-50 to-blue-100 flex items-center justify-center p-4">
    <div class="max-w-8/12 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl">
      <div class="grid grid-cols-1 lg:grid-cols-5">
        <!-- Lado esquerdo: ilustracao e texto -->
        <div class="relative p-8 md:p-12 lg:col-span-3 flex flex-col justify-center">
          <div class="space-y-8">
            <img
              src="/login_ilustracao.png"
              alt="Ilustracao de equipe medica"
              class="w-full max-w-xl mx-auto"
            />
            <div class="text-center space-y-2">
              <h2 class="text-3xl font-bold text-slate-900">UTI Manager</h2>
              <p class="text-base text-slate-700">
                Sistema de Gestao de Leitos de Terapia Intensiva <br/>
                do Hospital das Clinicas da UFPE
              </p>
            </div>
          </div>
        </div>

        <!-- Lado direito: formulario -->
        <div class="p-8 md:p-12 bg-white lg:col-span-2 flex flex-col justify-center">
          <div class="flex flex-col items-center mb-8 space-y-3">
            <img src="/hc_ufpe_icon.jpeg" alt="Hospital das Clinicas UFPE" class="h-20 w-20 rounded-xl object-cover" />
            <h1 class="text-3xl font-bold text-slate-900">Bem-vindo de Volta</h1>
            <p class="text-center text-slate-600">
              Acesse sua conta para gerenciar os leitos da UTI
            </p>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-6">
            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700" for="username">
                Usuario
              </label>
              <input
                v-model="username"
                id="username"
                type="text"
                placeholder="Seu usuario"
                class="h-12 w-full rounded-lg border border-slate-200 bg-white px-3 text-slate-800 shadow-inner transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                :disabled="loading"
              />
              <p v-if="fieldErrors.username" class="text-sm text-red-600">
                {{ fieldErrors.username }}
              </p>
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-medium text-slate-700" for="password">
                Senha
              </label>
              <div class="relative">
                <input
                  v-model="password"
                  id="password"
                  :type="passwordFieldType"
                  placeholder="********"
                  class="h-12 w-full rounded-lg border border-slate-200 bg-white px-3 pr-12 text-slate-800 shadow-inner transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  :disabled="loading"
                />
                <button
                  type="button"
                  @click="togglePasswordVisibility"
                  class="absolute inset-y-0 right-0 px-3 flex items-center text-gray-500"
                >
                  <component :is="passwordFieldType === 'password' ? EyeIcon : EyeSlashIcon" class="h-5 w-5" />
                </button>
              </div>
              <p v-if="fieldErrors.password" class="text-sm text-red-600">
                {{ fieldErrors.password }}
              </p>
            </div>

            <div class="flex items-center justify-between">
              <label class="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" v-model="rememberMe" class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500">
                <span>Lembrar de mim</span>
              </label>
              <button type="button" class="text-sm font-semibold text-blue-600 hover:text-blue-700">
                Esqueceu a senha?
              </button>
            </div>

            <div class="space-y-3">
              <Button
                type="submit"
                variant="primary"
                :disabled="loading"
                class="w-full h-12 text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.01] text-white hover:bg-blue-700 border border-blue-600"
                :style="primaryButtonStyle"
              >
                <span v-if="loading">Entrando...</span>
                <span v-else>Entrar</span>
              </Button>
              <!--
              <Button
                type="button"
                variant="secondary"
                class="w-full h-11"
                @click="clearForm"
                :disabled="loading"
              >
                <XCircleIcon class="h-5 w-5 mr-2" />
                Limpar
              </Button>
              -->
            </div>

            <p class="text-center text-sm text-slate-500">
              Use qualquer usuario e senha para demonstracao
            </p>
          </form>

          <div v-if="error" class="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            <strong class="font-semibold">Erro:</strong>
            <span class="ml-1">{{ error }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Button from '../components/Button.vue';
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline';
import { useToast } from 'vue-toastification';
import { z } from 'zod';

const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const error = ref('');
const loading = ref(false);
const fieldErrors = ref<{ username?: string; password?: string }>({});
const passwordVisible = ref(false);
const primaryButtonStyle = computed(() => ({
  backgroundColor: '#2563eb',
  borderColor: '#2563eb',
}));
const toast = useToast();

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const passwordFieldType = computed(() => passwordVisible.value ? 'text' : 'password');

const loginSchema = z.object({
  username: z.string().trim()
    .min(3, 'Informe um usuario valido (minimo de 3 caracteres)')
    .regex(/^\S+$/, 'Usuario nao deve conter espacos'),
  password: z.string().min(4, 'Senha deve ter pelo menos 4 caracteres'),
});

const togglePasswordVisibility = () => {
  passwordVisible.value = !passwordVisible.value;
};


const handleLogin = async () => {
  error.value = '';
  fieldErrors.value = {};

  const parsed = loginSchema.safeParse({
    username: username.value,
    password: password.value,
  });

  if (!parsed.success) {
    parsed.error.errors.forEach((err) => {
      const field = err.path[0] as 'username' | 'password';
      fieldErrors.value[field] = err.message;
    });
    error.value = 'Revise os dados do formulario antes de continuar.';
    return;
  }

  loading.value = true;
  try {
    await authStore.login(parsed.data.username, parsed.data.password, rememberMe.value);
    toast.success('Login realizado com sucesso!');
    const redirectPath = (route.query.redirect as string) || '/';
    await router.push(redirectPath);
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'An unknown error occurred';
  } finally {
    loading.value = false;
  }
};
</script>
