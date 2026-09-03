<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <div class="flex items-center space-x-3">
          <Cog6ToothIcon class="h-7 w-7 text-paper-text" />
          <h1 class="text-2xl font-bold text-paper-text">Configurações do Sistema</h1>
        </div>
      </template>

      <div v-if="authStore.isAdmin" class="space-y-6">
        <p class="text-gray-600">
          Painel de gestão de perfil, permissões e status dos serviços do **Framework-SETISD-HC-UFPE**.
        </p>

        <!-- Informações do Usuário (Active Directory) -->
        <div v-if="authStore.user" class="p-5 bg-white border border-gray-200 rounded-xl shadow-sm space-y-3">
          <div class="flex items-center space-x-2 text-paper-text font-bold text-lg border-b pb-2">
            <UserCircleIcon class="h-6 w-6 text-gray-500" />
            <span>Perfil de Acesso Corporativo (Active Directory)</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm pt-2">
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">Usuário / Login</p>
              <p class="font-medium text-gray-800">{{ authStore.user.username }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">Nome Completo</p>
              <p class="font-medium text-gray-800">{{ authStore.user.displayName?.[0] || authStore.user.username }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">E-mail Corporativo</p>
              <p class="font-medium text-gray-800">{{ authStore.user.email?.[0] || 'Não cadastrado' }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-400 uppercase">Setor / Departamento</p>
              <p class="font-medium text-gray-800">{{ authStore.user.department?.[0] || 'SETISD / HC-UFPE' }}</p>
            </div>
          </div>

          <div class="pt-3">
            <p class="text-xs font-semibold text-gray-400 uppercase mb-2">Grupos de Segurança (AD Groups)</p>
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="group in authStore.user.groups" 
                :key="group" 
                class="px-2.5 py-1 text-xs font-semibold bg-gray-100 text-gray-700 rounded-lg border border-gray-200"
              >
                {{ group }}
              </span>
            </div>
          </div>
        </div>

        <!-- Debug JSON Data -->
        <div class="p-4 bg-gray-900 text-gray-100 rounded-xl text-xs overflow-x-auto">
          <p class="font-bold text-gray-400 mb-2">// Raw Token Claims (JSON)</p>
          <pre>{{ JSON.stringify(authStore.user, null, 2) }}</pre>
        </div>
      </div>

      <div v-else class="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
        <h2 class="text-lg font-bold">Acesso Restrito</h2>
        <p class="text-sm mt-1">Você precisa de privilégios de administrador ou do grupo SETISD para visualizar as configurações avançadas.</p>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import Card from '../components/Card.vue';
import { useAuthStore } from '../stores/auth';
import { Cog6ToothIcon, UserCircleIcon } from '@heroicons/vue/24/outline';

const authStore = useAuthStore();
</script>
