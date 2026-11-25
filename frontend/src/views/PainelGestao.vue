<template>
  <div class="space-y-5">
    <div class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      Indicadores calculados sobre o export AGHUX com referência em {{ formatarDataHora(REFERENCIA_EM) }}; não representam a produção atual do hospital.
    </div>

    <Card>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold text-paper-text">Painel de Gestão</h2>
            <p class="text-sm text-gray-500">Indicadores operacionais da Central de Marcação de Exames</p>
          </div>
          <div class="flex gap-2">
            <select v-model="store.filtros.periodo" class="form-control" aria-label="Período dos indicadores">
              <option value="24">Últimas 24 h</option>
              <option value="72">Últimas 72 h</option>
              <option value="168">Últimos 7 dias</option>
              <option value="todos">Todo o período</option>
            </select>
            <select v-model="store.filtros.tipoExame" class="form-control" aria-label="Tipo de exame">
              <option value="">Todos os tipos</option>
              <option v-for="tipo in tiposExame" :key="tipo" :value="tipo">{{ tipo }}</option>
            </select>
          </div>
        </div>
      </template>

      <p v-if="store.erro" class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ store.erro }}</p>

      <div v-if="store.indicadores" class="space-y-5">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard titulo="Solicitações pendentes" :valor="store.indicadores.pendentes" detalhe="Aguardando validação, contato ou agendamento" cor="primary" />
          <KpiCard titulo="Tempo médio de validação" :valor="`${store.indicadores.tempoMedioValidacao} h`" detalhe="Do recebimento à validação do operador" cor="info" />
          <KpiCard titulo="Exames agendados" :valor="store.indicadores.agendados" :detalhe="`Média de ${store.indicadores.tempoMedioAgendamento} h até a marcação`" cor="success" />
          <KpiCard titulo="Taxa de erro pós-envio" :valor="`${store.indicadores.taxaErro}%`" detalhe="Formulários com inconsistências ou divergências" cor="warning" />
        </div>

        <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <MiniChart titulo="Solicitações por tipo de exame" :serie="store.indicadores.porTipo" tipo="bar" />
          <MiniChart titulo="Volume recebido por dia" :serie="store.indicadores.evolucao" tipo="line" />
        </div>

        <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div class="rounded-lg bg-white p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-paper-text">Gargalos da fila</h3>
            <ul class="space-y-3">
              <li v-for="gargalo in store.indicadores.gargalos" :key="`${gargalo.etapa}-${gargalo.unidadeSolicitante}`" class="rounded border border-gray-100 bg-gray-50 p-3">
                <p class="text-sm font-medium text-gray-800">{{ gargalo.etapa }}</p>
                <p class="text-xs text-gray-500">{{ gargalo.unidadeSolicitante }} · {{ gargalo.quantidade }} solicitação(ões) · {{ gargalo.horas }} h paradas</p>
              </li>
            </ul>
          </div>
          <div class="rounded-lg bg-white p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-paper-text">Distribuição por prioridade</h3>
            <ul class="space-y-2 text-sm">
              <li v-for="serie in store.indicadores.porPrioridade" :key="serie.rotulo" class="flex items-center justify-between border-b border-gray-100 py-1">
                <span class="text-gray-600">{{ serie.rotulo }}</span>
                <span class="font-semibold text-paper-text">{{ serie.valor }}</span>
              </li>
              <li v-if="!store.indicadores.porPrioridade.length" class="text-gray-500">Sem dados no período.</li>
            </ul>
          </div>
          <div class="flex flex-col justify-between rounded-lg bg-white p-5 shadow-paper">
            <div>
              <h3 class="font-semibold text-paper-text">Próxima ação</h3>
              <p class="mt-2 text-sm text-gray-600">Abra a fila para tratar as solicitações mais prioritárias primeiro.</p>
            </div>
            <router-link to="/fila" class="mt-4">
              <Button variant="primary">Abrir fila de marcação</Button>
            </router-link>
          </div>
        </div>
      </div>
      <LoadingIndicator v-else-if="store.carregando" />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import KpiCard from '../components/KpiCard.vue';
import LoadingIndicator from '../components/LoadingIndicator.vue';
import MiniChart from '../components/MiniChart.vue';
import { REFERENCIA_EM } from '../config/tempo';
import { tiposExameDisponiveis } from '../mocks/fixtures';
import { usePainelStore } from '../stores/painel';
import { formatarDataHora } from '../utils/format';

const store = usePainelStore();
const tiposExame = tiposExameDisponiveis;

onMounted(() => { void store.carregar(); });
watch(
  () => [store.filtros.periodo, store.filtros.tipoExame],
  () => { void store.carregar(); },
);
</script>
