<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <div class="flex items-center space-x-3">
          <HomeIcon class="h-7 w-7 text-paper-text" />
          <h1 class="text-2xl font-bold text-paper-text">Página Inicial</h1>
        </div>
      </template>
      <div class="space-y-4">
        <p class="text-gray-700 leading-relaxed">
          Bem-vindo ao **Framework-SETISD-HC-UFPE**! Esta é a página inicial padrão do seu novo sistema.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <!-- Card Clicável Componentes -->
          <router-link to="/componentes" class="p-4 bg-gray-50 hover:bg-white border border-gray-200 hover:border-gray-300 rounded-xl space-y-1 hover:shadow-md transition-all duration-200 group block">
            <h3 class="font-bold text-gray-800 group-hover:text-paper-text flex items-center gap-2">
              <CubeIcon class="h-5 w-5 text-gray-600 group-hover:text-paper-text transition-colors" />
              Componentes
            </h3>
            <p class="text-xs text-gray-500">Acesse o menu <strong>Componentes</strong> para visualizar botões, modais, cards e formulários reusáveis.</p>
          </router-link>

          <!-- Card Clicável Exemplo -->
          <router-link to="/exemplo" class="p-4 bg-gray-50 hover:bg-white border border-gray-200 hover:border-gray-300 rounded-xl space-y-1 hover:shadow-md transition-all duration-200 group block">
            <h3 class="font-bold text-gray-800 group-hover:text-paper-text flex items-center gap-2">
              <DocumentTextIcon class="h-5 w-5 text-gray-600 group-hover:text-paper-text transition-colors" />
              Exemplo
            </h3>
            <p class="text-xs text-gray-500">Acesse o menu <strong>Exemplo</strong> para ver uma demonstração de consulta de dados via PostgreSQL ou CSV.</p>
          </router-link>

          <!-- Card Clicável Configurações -->
          <router-link to="/configuracoes" class="p-4 bg-gray-50 hover:bg-white border border-gray-200 hover:border-gray-300 rounded-xl space-y-1 hover:shadow-md transition-all duration-200 group block">
            <h3 class="font-bold text-gray-800 group-hover:text-paper-text flex items-center gap-2">
              <Cog6ToothIcon class="h-5 w-5 text-gray-600 group-hover:text-paper-text transition-colors" />
              Configurações
            </h3>
            <p class="text-xs text-gray-500">Acesse <strong>Configurações</strong> para gerenciar o perfil do usuário, grupos de acesso e informações do sistema.</p>
          </router-link>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import Card from '../components/Card.vue';
import { HomeIcon, CubeIcon, DocumentTextIcon, Cog6ToothIcon } from '@heroicons/vue/24/outline';
</script>
