<template>
  <Card>
    <div class="py-8 text-center">
      <ShieldExclamationIcon class="mx-auto h-12 w-12 text-paper-warning" />
      <h2 class="mt-4 text-xl font-bold text-paper-text">Acesso negado</h2>
      <p class="mx-auto mt-2 max-w-md text-sm text-gray-600">
        Seu perfil não possui permissão para esta área. Solicite à Área Gestora a revisão do seu perfil no sistema.
      </p>
      <router-link to="/" class="mt-5 inline-block">
        <Button variant="primary">Voltar ao início</Button>
      </router-link>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { ShieldExclamationIcon } from '@heroicons/vue/24/outline';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
</script>
