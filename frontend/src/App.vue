<template>
  <component :is="layout">
    <router-view />
  </component>
  <LoadingIndicator />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, computed } from 'vue';
import { useAuthStore } from './stores/auth';
import AppShell from './layouts/appShell.vue';
import LoginLayout from './layouts/loginLayout.vue';
import LoadingIndicator from './components/loadingIndicator/loadingIndicator.vue';

const route = useRoute();

const layout = computed(() => {
  return route.meta.layout === 'LoginLayout' ? LoginLayout : AppShell;
});

const authStore = useAuthStore();
onMounted(async () => {
  await authStore.initializeAuth();
});
</script>