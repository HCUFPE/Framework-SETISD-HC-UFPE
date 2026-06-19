<template>
  <div class="w-full max-w-md">
    <Card>
      <template #header>
        <div class="flex items-center justify-center gap-3 mb-1">
          <Microscope class="h-9 w-9 text-lab-primary" :stroke-width="1.5" />
          <span class="text-2xl font-extrabold text-lab-text tracking-tight">Anatomia Patológica</span>
        </div>
        <p class="text-center text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Criar conta
        </p>
      </template>

      <form @submit.prevent="handleRegister" class="flex flex-col gap-5 mt-6">
        <div>
          <label class="form-label" for="fullName">Nome completo</label>
          <input id="fullName" v-model="fullName" type="text" class="form-control" placeholder="Seu nome completo">
        </div>

        <div>
          <label class="form-label" for="username">Usuário</label>
          <input id="username" v-model="username" type="text" class="form-control" placeholder="Crie um nome de usuário">
        </div>

        <div>
          <label class="form-label" for="password">Senha</label>
          <input id="password" v-model="password" type="password" class="form-control" placeholder="********">
        </div>

        <div>
          <label class="form-label" for="confirmPassword">Confirmar senha</label>
          <input id="confirmPassword" v-model="confirmPassword" type="password" class="form-control" placeholder="********">
        </div>

        <Button type="submit" variant="primary" :loading="loading" class="w-full">
          Criar conta
        </Button>
      </form>

      <div v-if="error" class="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
        {{ error }}
      </div>

      <p class="mt-6 text-center text-sm text-gray-500">
        Já tem conta?
        <router-link to="/login" class="text-lab-primary font-medium hover:underline">
          Fazer login
        </router-link>
      </p>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import Card from '../../components/card/card.vue';
import Button from '../../components/button/button.vue';
import { Microscope } from 'lucide-vue-next';

const fullName = ref('');
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const error = ref('');
const loading = ref(false);

const router = useRouter();

// TODO: setor (Recepção/Macroscopia/Microscopia/Processamento Técnico) não está neste formulário — depende de decisão com o hospital sobre como atribuir o setor de cada usuário. Adicionar aqui ou mover pra um fluxo de admin quando isso for definido.
// TODO: endpoint de cadastro ainda não existe no backend.

const handleRegister = async () => {
  error.value = '';

  if (password.value !== confirmPassword.value) {
    error.value = 'As senhas não coincidem.';
    return;
  }

  loading.value = true;
  try {
    // await authStore.register({ fullName: fullName.value, username: username.value, password: password.value });
    await router.push('/login');
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Não foi possível criar a conta.';
  } finally {
    loading.value = false;
  }
};
</script>