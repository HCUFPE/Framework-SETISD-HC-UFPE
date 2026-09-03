<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <div class="flex items-center space-x-3">
          <HomeIcon class="h-7 w-7 text-paper-text" />
          <h1 class="text-2xl font-bold text-paper-text">Painel Inicial (Início)</h1>
        </div>
      </template>
      <div class="space-y-4">
        <p class="text-gray-700 leading-relaxed">
          Bem-vindo ao **Framework-SETISD-HC-UFPE**! Esta é a página inicial padrão (Início) do seu novo sistema.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div class="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-1">
            <h3 class="font-bold text-gray-800 flex items-center gap-2">
              <CubeIcon class="h-5 w-5 text-gray-600" />
              Componentes
            </h3>
            <p class="text-xs text-gray-500">Acesse o menu <strong>Componentes</strong> para visualizar botões, modais, cards e formulários reusáveis.</p>
          </div>

          <div class="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-1">
            <h3 class="font-bold text-gray-800 flex items-center gap-2">
              <DocumentTextIcon class="h-5 w-5 text-gray-600" />
              Exemplo
            </h3>
            <p class="text-xs text-gray-500">Acesse o menu <strong>Exemplo</strong> para ver uma demonstração de consulta de dados via PostgreSQL ou CSV.</p>
          </div>

          <div class="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-1">
            <h3 class="font-bold text-gray-800 flex items-center gap-2">
              <Cog6ToothIcon class="h-5 w-5 text-gray-600" />
              Configurações
            </h3>
            <p class="text-xs text-gray-500">Acesse <strong>Configurações</strong> para ver o perfil do usuário logado no Active Directory.</p>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import Card from '../components/Card.vue';
import { HomeIcon, CubeIcon, DocumentTextIcon, Cog6ToothIcon } from '@heroicons/vue/24/outline';
</script>
