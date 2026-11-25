<template>
  <div class="space-y-5">
    <div class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      Relatórios calculados sobre o export AGHUX com referência em {{ formatarDataHora(REFERENCIA_EM) }}.
    </div>

    <Card>
      <template #header>
        <h2 class="text-xl font-bold text-paper-text">Relatórios</h2>
      </template>
      <div class="grid grid-cols-1 gap-5 md:grid-cols-3">
        <ul class="space-y-2">
          <li v-for="relatorio in store.relatorios" :key="relatorio.id">
            <button
              class="w-full rounded-lg border p-3 text-left transition"
              :class="relatorio.id === store.selecionado ? 'border-paper-primary bg-paper-primary/10' : 'border-gray-200 bg-white hover:bg-gray-50'"
              @click="selecionar(relatorio.id)"
            >
              <span class="block text-sm font-semibold text-paper-text">{{ relatorio.nome }}</span>
              <span class="mt-1 block text-xs text-gray-500">{{ relatorio.descricao }}</span>
            </button>
          </li>
        </ul>

        <div class="md:col-span-2">
          <div class="flex flex-col gap-2 sm:flex-row">
            <select v-model="store.filtros.periodo" class="form-control" aria-label="Período do relatório">
              <option value="24">Últimas 24 h</option>
              <option value="72">Últimas 72 h</option>
              <option value="168">Últimos 7 dias</option>
              <option value="720">Últimos 30 dias</option>
              <option value="todos">Todo o período</option>
            </select>
            <select v-model="store.filtros.tipoExame" class="form-control" aria-label="Tipo de exame">
              <option value="">Todos os tipos</option>
              <option v-for="tipo in tiposExame" :key="tipo" :value="tipo">{{ tipo }}</option>
            </select>
            <Button variant="primary" :loading="store.carregando" @click="store.gerar()">Gerar</Button>
            <Button variant="success" :disabled="!store.resultado" @click="exportarCsv">Exportar CSV</Button>
          </div>

          <p v-if="store.erro" class="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ store.erro }}</p>

          <div v-if="store.resultado" class="mt-4 overflow-x-auto">
            <DataTable
              :headers="store.resultado.colunas.map((coluna) => ({ text: coluna, value: coluna }))"
              :items="store.resultado.linhas"
            />
            <p class="mt-2 text-xs text-gray-500">{{ store.resultado.linhas.length }} linha(s) encontrada(s).</p>
          </div>
          <p v-else class="mt-6 text-center text-sm text-gray-500">Selecione um relatório e clique em Gerar.</p>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import DataTable from '../components/DataTable.vue';
import { REFERENCIA_EM } from '../config/tempo';
import { tiposExameDisponiveis } from '../mocks/fixtures';
import { useRelatoriosStore } from '../stores/relatorios';
import { formatarDataHora } from '../utils/format';

const store = useRelatoriosStore();
const tiposExame = tiposExameDisponiveis;

onMounted(() => {
  void store.carregarCatalogo();
  void store.gerar();
});

async function selecionar(id: string): Promise<void> {
  store.selecionado = id;
  await store.gerar();
}

function exportarCsv(): void {
  const resultado = store.resultado;
  if (!resultado) return;
  const linhas = [
    resultado.colunas,
    ...resultado.linhas.map((linha) => resultado.colunas.map((coluna) => String(linha[coluna] ?? ''))),
  ];
  const conteudo = linhas
    .map((linha) => linha.map((valor) => `"${valor.replace(/"/g, '""')}"`).join(';'))
    .join('\n');
  const url = URL.createObjectURL(new Blob([`\ufeff${conteudo}`], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `relatorio-${store.selecionado}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
</script>
