<template>
  <div class="w-full max-w-md">
    <Card>
      <template #header>
        <div class="flex items-center justify-center gap-3 mb-1">
          <Microscope class="h-9 w-9 text-lab-primary" :stroke-width="1.5" />
          <span class="text-2xl font-extrabold text-lab-text tracking-tight">Anatomia Patológica</span>
        </div>
        <p class="text-center text-xs font-semibold text-gray-400 uppercase tracking-widest">
          Recuperar senha
        </p>
      </template>

      <form v-if="!sent" @submit.prevent="handleSubmit" class="flex flex-col gap-5 mt-6">
        <p class="text-sm text-gray-500">
          Informe seu usuário e enviaremos instruções para redefinir sua senha.
        </p>

        <div>
          <label class="form-label" for="username">Usuário</label>
          <input id="username" v-model="username" type="text" class="form-control" placeholder="Seu usuário">
        </div>

        <Button type="submit" variant="primary" :loading="loading" class="w-full">
          Enviar instruções
        </Button>
      </form>

      <div v-else class="text-center text-sm text-gray-600 py-4">
        Se o usuário existir, enviamos as instruções de recuperação.
      </div>

      <div v-if="error" class="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
        {{ error }}
      </div>

      <p class="mt-6 text-center text-sm text-gray-500">
        <router-link to="/login" class="text-lab-primary font-medium hover:underline">
          Voltar para o login
        </router-link>
      </p>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Microscope } from 'lucide-vue-next';
import Card from '../../components/card/card.vue';
import Button from '../../components/button/button.vue';

const username = ref('');
const error = ref('');
const loading = ref(false);
const sent = ref(false);

// TODO: endpoint de recuperação de senha ainda não existe no backend.

const handleSubmit = async () => {
  error.value = '';
  loading.value = true;
  try {
    // await api.post('/api/password/forgot', { username: username.value });
    sent.value = true;
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Não foi possível processar a solicitação.';
  } finally {
    loading.value = false;
  }
};
</script>