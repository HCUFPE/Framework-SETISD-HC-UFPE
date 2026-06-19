<template>
  <div class="flex flex-col items-center justify-center gap-4 py-20 text-center">
    <FaceFrownIcon class="h-16 w-16 text-lab-text/40" />
    <h1 class="text-2xl font-bold text-lab-text">Página não encontrada</h1>
    <p class="text-gray-500">O endereço acessado não existe ou foi movido.</p>
    <router-link to="/">
      <Button variant="primary">Voltar ao Dashboard</Button>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { FaceFrownIcon } from '@heroicons/vue/24/outline';
import Button from '../components/button/button.vue';
</script>