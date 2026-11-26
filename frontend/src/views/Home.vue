<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <div>
          <h1 class="text-2xl font-bold text-paper-text">Sistema de Agendamento de Exames</h1>
          <p class="mt-1 text-sm text-gray-500">Central de Marcação de Exames · HC-UFPE / EBSERH</p>
        </div>
      </template>
      <p class="text-gray-700 leading-relaxed">
        Esta é a versão de telas do SAE-HC. O fixture reúne {{ totalSolicitacoes }} solicitações
        ({{ solicitacoesSimuladas }} simuladas recentes, geradas a partir de
        {{ totalRegistros }} itens), com referência em {{ referenciaFormatada }}; prazos e filtros
        usam essa data, não o relógio do computador. A integração com o formulário externo, o AGHUX
        e o backend de domínio segue reservada para entrega futura.
      </p>
    </Card>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <router-link
        v-for="item in atalhos"
        :key="item.rota"
        :to="item.rota"
        class="block rounded-xl border border-gray-200 bg-white p-5 shadow-paper transition hover:border-paper-primary hover:shadow-md"
      >
        <component :is="item.icone" class="h-7 w-7 text-paper-primary" />
        <h3 class="mt-3 font-bold text-gray-800">{{ item.titulo }}</h3>
        <p class="mt-1 text-xs text-gray-500">{{ item.descricao }}</p>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue';
import {
  ChartBarIcon,
  DocumentTextIcon,
  TableCellsIcon,
  AdjustmentsHorizontalIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/Card.vue';
import { REFERENCIA_EM } from '../config/tempo';
import dadosAghuxJson from '../mocks/dadosAghux.json';
import { useAuthStore } from '../stores/auth';
import { formatarDataHora } from '../utils/format';
import type { Perfil } from '../types/sae';

interface Atalho {
  rota: string;
  titulo: string;
  descricao: string;
  icone: Component;
  perfis: Perfil[];
}

const auth = useAuthStore();

const totalRegistros = dadosAghuxJson.totalRegistros;
const totalSolicitacoes = dadosAghuxJson.totalSolicitacoes;
const solicitacoesSimuladas = dadosAghuxJson.solicitacoes.filter(
  (item) => item.codigoSolicitacao.startsWith('SIM-'),
).length;
const referenciaFormatada = formatarDataHora(REFERENCIA_EM);

const todos: Atalho[] = [
  { rota: '/fila', titulo: 'Fila de Marcação', descricao: 'Fila priorizada com conferência e registro de contato.', icone: TableCellsIcon, perfis: ['OPERADOR', 'CHEFIA', 'AREA_GESTORA'] },
  { rota: '/painel', titulo: 'Painel de Gestão', descricao: 'Indicadores operacionais e gargalos da fila.', icone: ChartBarIcon, perfis: ['CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'] },
  { rota: '/relatorios', titulo: 'Relatórios', descricao: 'Consolidações filtráveis com exportação CSV.', icone: DocumentTextIcon, perfis: ['CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'] },
  { rota: '/criterios', titulo: 'Critérios de Priorização', descricao: 'Pesos e versões que definem a ordem da fila.', icone: AdjustmentsHorizontalIcon, perfis: ['AREA_GESTORA'] },
  { rota: '/equipe', titulo: 'Equipe e Perfis', descricao: 'Cadastro local validado no Active Directory.', icone: UsersIcon, perfis: ['AREA_GESTORA', 'ADMIN_TI'] },
];

const atalhos = computed(() => todos.filter((item) => auth.temPerfil(...item.perfis)));
</script>
