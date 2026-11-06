<template>
  <div class="space-y-4">
    <p class="text-sm text-gray-600">Todos os casos, inclusive devolvidos, cancelados e arquivados.</p>

    <Card>
      <!-- Filtros -->
      <div class="flex flex-wrap items-end gap-3">
        <div class="min-w-64 flex-1">
          <label for="consulta-busca" class="form-label">Buscar</label>
          <div class="relative">
            <MagnifyingGlassIcon class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" aria-hidden="true" />
            <input
              id="consulta-busca"
              v-model="filtros.busca"
              type="search"
              autocomplete="off"
              class="form-control pl-10"
              placeholder="Nº interno, nº AGHU, prontuário ou nome"
            />
          </div>
        </div>
        <div>
          <label for="consulta-status" class="form-label">Status</label>
          <select id="consulta-status" v-model="filtros.status" class="form-control">
            <option value="">Todos</option>
            <option v-for="s in ORDEM_STATUS_CASO" :key="s" :value="s">{{ STATUS_CASO[s].rotulo }}</option>
          </select>
        </div>
        <div>
          <label for="consulta-tipo" class="form-label">Tipo</label>
          <select id="consulta-tipo" v-model="filtros.tipo" class="form-control">
            <option value="">Todos</option>
            <option v-for="t in TIPOS_CASO_PRINCIPAL" :key="t" :value="t">{{ t }} · {{ TIPOS_EXAME[t].nome }}</option>
          </select>
        </div>
        <div>
          <label for="consulta-periodo" class="form-label">Período de entrada</label>
          <select id="consulta-periodo" v-model.number="filtros.periodoDias" class="form-control">
            <option v-for="p in PERIODOS" :key="p.dias" :value="p.dias">{{ p.rotulo }}</option>
          </select>
        </div>
        <button
          type="button"
          :aria-pressed="filtros.somenteUrgentes"
          :class="
            filtros.somenteUrgentes
              ? 'border-paper-danger bg-paper-danger-soft text-paper-danger-strong'
              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
          "
          class="focus-ring inline-flex h-[38px] items-center gap-2 rounded-md border px-3 text-sm font-semibold transition active:scale-95"
          @click="filtros.somenteUrgentes = !filtros.somenteUrgentes"
        >
          <ExclamationTriangleIcon class="h-4 w-4" aria-hidden="true" />
          Somente urgentes
        </button>
      </div>

      <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
        <FilterChips :chips="chips" @remove="removerFiltro" @clear="limparFiltros" />
        <p class="ml-auto text-sm text-gray-500" aria-live="polite">{{ resultado.length }} caso(s)</p>
      </div>

      <div class="mt-4">
        <DataTable
          :key="assinaturaFiltros"
          :headers="colunas"
          :items="linhas"
          :page-size="10"
          :loading="casosStore.carregando"
          clickable
          :highlight="(item) => item.urgente"
          empty-text="Nenhum caso encontrado. Revise a busca ou limpe os filtros."
          @row-click="abrir"
        >
          <template #cell-numeroInterno="{ item }">
            <span class="font-bold text-gray-900 tabular-nums">{{ item.numeroInterno }}</span>
            <Badge v-if="item.urgente" variant="danger" size="sm" class="ml-2">URGENTE</Badge>
          </template>
          <template #cell-paciente="{ item }">
            <span class="block font-semibold text-gray-800">{{ item.paciente }}</span>
            <span class="text-xs text-gray-500">Pront. {{ item.prontuario }}</span>
          </template>
          <template #cell-status="{ item }">
            <StatusCasoBadge :status="item.status" />
          </template>
        </DataTable>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { ExclamationTriangleIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import Badge from '../../components/Badge.vue';
import Card from '../../components/Card.vue';
import DataTable from '../../components/DataTable.vue';
import FilterChips, { type FilterChip } from '../../components/FilterChips.vue';
import StatusCasoBadge from '../../components/ap/StatusCasoBadge.vue';
import { ORDEM_STATUS_CASO, STATUS_CASO, TIPOS_CASO_PRINCIPAL, TIPOS_EXAME } from '../../constants/ap';
import { formatarDataHora } from '../../helpers/formato';
import { rotaDoCaso } from '../../helpers/rotas';
import { filtrosConsultaVazios, useCasosStore, type FiltrosConsulta } from '../../stores/casos';

const PERIODOS = [
  { dias: 0, rotulo: 'Qualquer data' },
  { dias: 7, rotulo: 'Últimos 7 dias' },
  { dias: 30, rotulo: 'Últimos 30 dias' },
  { dias: 90, rotulo: 'Últimos 90 dias' },
];

const router = useRouter();
const casosStore = useCasosStore();
const { filtros } = storeToRefs(casosStore);

const colunas = [
  { text: 'Nº interno', value: 'numeroInterno' },
  { text: 'Tipo', value: 'tipo' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Nº AGHU', value: 'aghu' },
  { text: 'Material', value: 'material' },
  { text: 'Status', value: 'status' },
  { text: 'Entrada', value: 'entrada' },
];

/** Casos que atendem à busca e aos filtros, com urgentes primeiro e entrada mais recente primeiro. */
const resultado = computed(() => {
  const f = filtros.value;
  const termo = f.busca.trim().toUpperCase();
  const limite = f.periodoDias > 0 ? Date.now() - f.periodoDias * 86_400_000 : null;
  return casosStore.casos
    .filter((c) => {
      if (termo) {
        const alvo = [c.numeroInterno, c.solicitacao.codigoSolicitacao, c.solicitacao.prontuario, c.solicitacao.nomePaciente];
        if (!alvo.some((valor) => valor.toUpperCase().includes(termo))) return false;
      }
      if (f.status && c.status !== f.status) return false;
      if (f.tipo && c.tipoExame !== f.tipo) return false;
      if (limite !== null && new Date(c.dataEntradaSap).getTime() < limite) return false;
      if (f.somenteUrgentes && !c.urgente) return false;
      return true;
    })
    .sort((a, b) => Number(b.urgente) - Number(a.urgente) || b.dataEntradaSap.localeCompare(a.dataEntradaSap));
});

const linhas = computed(() =>
  resultado.value.map((c) => ({
    id: c.numeroInterno,
    numeroInterno: c.numeroInterno,
    urgente: c.urgente,
    tipo: c.tipoExame,
    paciente: c.solicitacao.nomePaciente,
    prontuario: c.solicitacao.prontuario,
    aghu: c.solicitacao.codigoSolicitacao,
    material: c.solicitacao.descricaoMaterial,
    status: c.status,
    entrada: formatarDataHora(c.dataEntradaSap),
  })),
);

/** Muda a cada alteração de filtro e recria a tabela, voltando à primeira página. */
const assinaturaFiltros = computed(() => JSON.stringify(filtros.value));

const chips = computed<FilterChip[]>(() => {
  const f = filtros.value;
  const lista: FilterChip[] = [];
  if (f.busca.trim()) lista.push({ key: 'busca', label: `Busca: "${f.busca.trim()}"` });
  if (f.status) lista.push({ key: 'status', label: `Status: ${STATUS_CASO[f.status].rotulo}` });
  if (f.tipo) lista.push({ key: 'tipo', label: `Tipo: ${f.tipo}` });
  if (f.periodoDias) lista.push({ key: 'periodoDias', label: `Período: últimos ${f.periodoDias} dias` });
  if (f.somenteUrgentes) lista.push({ key: 'somenteUrgentes', label: 'Somente urgentes' });
  return lista;
});

/** Remove apenas o filtro da etiqueta clicada. */
const removerFiltro = (chave: string) => {
  const padrao = filtrosConsultaVazios();
  const k = chave as keyof FiltrosConsulta;
  filtros.value = { ...filtros.value, [k]: padrao[k] };
};

const limparFiltros = () => {
  filtros.value = filtrosConsultaVazios();
};

const abrir = (item: { numeroInterno: string }) => {
  router.push(rotaDoCaso(item.numeroInterno));
};

onMounted(() => {
  casosStore.carregar();
});
</script>
