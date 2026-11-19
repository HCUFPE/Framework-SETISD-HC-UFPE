<template>
  <Card>
    <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
      <div>
        <h2 class="text-lg font-bold text-gray-800">Solicitações do AGHU</h2>
        <p class="text-sm text-gray-500">
          {{ descricaoDaOrdem }} Clique em uma linha para conferir.
        </p>
      </div>
      <button
        v-if="store.filtrosAtivos || store.ordenacaoDaLista"
        type="button"
        class="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-100"
        data-testid="limpar-filtros"
        @click="limparFiltros"
      >
        Limpar filtros e ordenação
      </button>
    </div>

    <div class="w-full overflow-x-auto" :class="{ 'opacity-60': store.carregandoLista }">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-xs font-semibold tracking-wider text-left text-gray-500 uppercase border-b border-gray-200 bg-gray-50">
            <th
              v-for="coluna in COLUNAS"
              :key="coluna.chave"
              class="px-3 py-2"
              :class="{ 'text-center': coluna.chave === 'amostras' }"
              :aria-sort="ariaSort(coluna.ordenavel)"
            >
              <button
                v-if="coluna.ordenavel"
                type="button"
                class="inline-flex items-center gap-1 font-semibold tracking-wider uppercase hover:text-gray-800"
                :data-testid="`ordenar-${coluna.ordenavel}`"
                @click="ordenarPor(coluna.ordenavel)"
              >
                {{ coluna.rotulo }}
                <span :class="seta(coluna.ordenavel).classe" aria-hidden="true">{{ seta(coluna.ordenavel).simbolo }}</span>
              </button>
              <template v-else>{{ coluna.rotulo }}</template>
            </th>
          </tr>
          <tr class="border-b border-gray-200 bg-gray-50">
            <th v-for="coluna in COLUNAS" :key="coluna.chave" class="px-3 pb-2 font-normal normal-case">
              <input
                v-if="coluna.filtro === 'texto'"
                v-model="store.filtrosDaLista[coluna.chave as ColunaDaLista]"
                type="text"
                :aria-label="`Filtrar por ${coluna.rotulo}`"
                placeholder="Filtrar"
                :class="CAMPO_FILTRO"
                :data-testid="`filtro-${coluna.chave}`"
                @input="filtrarDepoisDeDigitar"
              />
              <input
                v-else-if="coluna.filtro === 'data'"
                v-model="store.filtrosDaLista.data"
                type="date"
                aria-label="Filtrar pela data da solicitação"
                :class="CAMPO_FILTRO"
                data-testid="filtro-data"
                @change="aplicarFiltros"
              />
              <select
                v-else-if="coluna.filtro === 'bancada'"
                v-model="store.filtrosDaLista.bancada"
                aria-label="Filtrar por bancada"
                :class="CAMPO_FILTRO"
                data-testid="filtro-bancada"
                @change="aplicarFiltros"
              >
                <option value="">Todas</option>
                <option v-for="bancada in BANCADAS" :key="bancada" :value="bancada">{{ bancada }}</option>
              </select>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="linha in store.lista?.solicitacoes ?? []"
            :key="linha.codigo"
            class="cursor-pointer"
            :class="linha.urgente ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'"
            data-testid="linha-lista"
            @click="emit('abrir', linha.codigo)"
          >
            <td class="px-3 py-3">
              <button
                type="button"
                class="font-bold text-paper-primary-hover hover:underline"
                @click.stop="emit('abrir', linha.codigo)"
              >
                {{ linha.codigo }}
              </button>
              <span
                v-if="linha.urgente"
                class="ml-2 px-2 py-0.5 rounded-full bg-red-600 text-xs font-bold text-white"
                data-testid="urgente-lista"
              >
                Urgente
              </span>
            </td>
            <td class="px-3 py-3 whitespace-nowrap">{{ formatarDia(linha.data_solicitacao) }}</td>
            <td class="px-3 py-3 whitespace-nowrap">
              {{ linha.paciente.nome }}
              <span v-if="linha.paciente.idade !== null" class="text-gray-500">· {{ linha.paciente.idade }} anos</span>
            </td>
            <td class="px-3 py-3 whitespace-nowrap">{{ linha.paciente.prontuario || 'Sem prontuário' }}</td>
            <td class="px-3 py-3 whitespace-nowrap">{{ linha.origem }}</td>
            <td class="px-3 py-3">
              {{ linha.especialidade || 'Não informada' }}
              <p v-if="linha.unidade" class="text-xs text-gray-500">{{ linha.unidade }}</p>
            </td>
            <td class="px-3 py-3 whitespace-nowrap">
              <span
                v-for="bancada in linha.bancadas"
                :key="bancada"
                class="inline-block mr-1 px-2 py-0.5 rounded bg-gray-100 text-xs font-bold text-gray-700"
              >
                {{ bancada }}
              </span>
            </td>
            <td class="px-3 py-3 text-center whitespace-nowrap">
              {{ linha.amostras_recebiveis }} de {{ linha.total_amostras }}
            </td>
            <td class="px-3 py-3 whitespace-nowrap">
              <span class="inline-block px-2 py-0.5 rounded-full text-xs font-semibold" :class="SITUACOES[linha.situacao].classe">
                {{ SITUACOES[linha.situacao].rotulo }}
              </span>
              <p v-if="linha.numeros_internos.length" class="mt-1 text-xs font-medium text-gray-600">
                {{ linha.numeros_internos.join(', ') }}
              </p>
            </td>
          </tr>
          <tr v-if="store.lista && store.lista.solicitacoes.length === 0">
            <td colspan="9" class="px-3 py-8 text-center text-gray-500">
              {{ store.filtrosAtivos ? 'Nenhuma solicitação encontrada com os filtros aplicados.' : 'Nenhuma solicitação encontrada.' }}
            </td>
          </tr>
          <tr v-if="!store.lista">
            <td colspan="9" class="px-3 py-8 text-center text-gray-500">
              {{ store.carregandoLista ? 'Carregando solicitações...' : 'Não foi possível carregar a lista.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="store.lista && store.lista.total > 0" class="flex flex-wrap items-center justify-between gap-3 mt-4">
      <p class="text-sm text-gray-600" data-testid="resumo-lista">
        Mostrando {{ primeiroDaPagina.toLocaleString('pt-BR') }}–{{ ultimoDaPagina.toLocaleString('pt-BR') }} de {{ store.lista.total.toLocaleString('pt-BR') }}
      </p>
      <nav aria-label="Páginas da lista de solicitações" class="flex flex-wrap items-center gap-1" data-testid="paginacao">
        <button
          type="button"
          :class="BOTAO_PAGINA"
          :disabled="store.lista.pagina <= 1 || store.carregandoLista"
          @click="irPara(store.lista!.pagina - 1)"
        >
          Anterior
        </button>
        <template v-for="(item, indice) in paginasVisiveis" :key="indice">
          <span v-if="item === null" class="px-1 text-sm text-gray-400" aria-hidden="true">…</span>
          <button
            v-else
            type="button"
            :class="item === store.lista.pagina ? PAGINA_ATUAL : BOTAO_PAGINA"
            :aria-label="`Página ${item}`"
            :aria-current="item === store.lista.pagina ? 'page' : undefined"
            :disabled="store.carregandoLista"
            @click="item !== store.lista!.pagina && irPara(item)"
          >
            {{ item.toLocaleString('pt-BR') }}
          </button>
        </template>
        <button
          type="button"
          :class="BOTAO_PAGINA"
          :disabled="store.lista.pagina >= store.lista.total_paginas || store.carregandoLista"
          @click="irPara(store.lista!.pagina + 1)"
        >
          Próxima
        </button>
      </nav>
    </div>
  </Card>
</template>

<script setup lang="ts">

import { computed, onBeforeUnmount } from 'vue';
import { useToast } from 'vue-toastification';
import Card from '../Card.vue';
import {
  mensagemDeErro,
  SITUACOES,
  useRecebimentoStore,
  type ColunaDaLista,
} from '../../stores/recebimento';

const emit = defineEmits<{ abrir: [codigo: string] }>();
const store = useRecebimentoStore();
const toast = useToast();

const BASE_PAGINA = 'min-w-9 h-9 px-3 rounded border text-sm disabled:cursor-not-allowed';
const BOTAO_PAGINA = `${BASE_PAGINA} border-gray-300 bg-white font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50`;
const PAGINA_ATUAL = `${BASE_PAGINA} border-paper-primary bg-paper-primary font-bold text-white`;
const VIZINHAS_DA_ATUAL = 1;
const CAMPO_FILTRO = 'w-full min-w-24 px-2 py-1 text-sm font-normal text-gray-700 bg-white border border-gray-300 rounded normal-case';
const ESPERA_DA_DIGITACAO_MS = 400;

/** Bancadas que podem aparecer na lista (as mesmas cadastradas para o recebimento). */
const BANCADAS = ['CCV', 'CG', 'CO', 'HP', 'IHQ'];

interface ColunaDaTabela {
  chave: string;
  rotulo: string;
  /** Coluna que o backend sabe ordenar; as demais vêm do banco local e não são ordenáveis. */
  ordenavel?: ColunaDaLista;
  filtro?: 'texto' | 'data' | 'bancada';
}

const COLUNAS: ColunaDaTabela[] = [
  { chave: 'codigo', rotulo: 'Código', ordenavel: 'codigo', filtro: 'texto' },
  { chave: 'data', rotulo: 'Solicitada em', ordenavel: 'data', filtro: 'data' },
  { chave: 'paciente', rotulo: 'Paciente', ordenavel: 'paciente', filtro: 'texto' },
  { chave: 'prontuario', rotulo: 'Prontuário', ordenavel: 'prontuario', filtro: 'texto' },
  { chave: 'origem', rotulo: 'Origem', ordenavel: 'origem', filtro: 'texto' },
  { chave: 'clinica', rotulo: 'Clínica', ordenavel: 'clinica', filtro: 'texto' },
  { chave: 'bancadas', rotulo: 'Bancadas', filtro: 'bancada' },
  { chave: 'amostras', rotulo: 'Amostras' },
  { chave: 'situacao', rotulo: 'Situação' },
];

const ROTULOS: Record<ColunaDaLista, string> = {
  codigo: 'código',
  data: 'data da solicitação',
  paciente: 'paciente',
  prontuario: 'prontuário',
  origem: 'origem',
  clinica: 'clínica',
};

/** Texto sob o título: diz qual é a ordem atual, para a ordenação nunca ficar implícita. */
const descricaoDaOrdem = computed(() => {
  const ordenacao = store.ordenacaoDaLista;
  if (!ordenacao) return 'Urgências aguardando recebimento primeiro; depois, das mais recentes para as mais antigas.';
  const direcao = ordenacao.direcao === 'asc' ? 'crescente' : 'decrescente';
  return `Ordenadas por ${ROTULOS[ordenacao.coluna]} (${direcao}).`;
});

/** Valor de aria-sort do cabeçalho, para leitores de tela. */
const ariaSort = (coluna?: ColunaDaLista) => {
  const ordenacao = store.ordenacaoDaLista;
  if (!coluna || ordenacao?.coluna !== coluna) return coluna ? 'none' : undefined;
  return ordenacao.direcao === 'asc' ? 'ascending' : 'descending';
};

/** Seta do cabeçalho: ▲ crescente, ▼ decrescente e ↕ (esmaecida) quando a coluna não é a ordenada. */
const seta = (coluna: ColunaDaLista) => {
  const ordenacao = store.ordenacaoDaLista;
  if (ordenacao?.coluna !== coluna) return { simbolo: '↕', classe: 'text-gray-300' };
  return { simbolo: ordenacao.direcao === 'asc' ? '▲' : '▼', classe: 'text-paper-primary-hover' };
};

let temporizador: ReturnType<typeof setTimeout> | undefined;
onBeforeUnmount(() => clearTimeout(temporizador));

/** Espera o usuário parar de digitar antes de consultar, para não fazer uma busca por letra. */
const filtrarDepoisDeDigitar = () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(() => irPara(1), ESPERA_DA_DIGITACAO_MS);
};

/** Primeira, última, a atual e as vizinhas; null marca o salto entre elas, mostrado como reticências. */
const paginasVisiveis = computed<(number | null)[]>(() => {
  const lista = store.lista;
  if (!lista) return [];
  const paginas = new Set([1, lista.total_paginas]);
  for (let pagina = lista.pagina - VIZINHAS_DA_ATUAL; pagina <= lista.pagina + VIZINHAS_DA_ATUAL; pagina++) {
    if (pagina >= 1 && pagina <= lista.total_paginas) paginas.add(pagina);
  }
  const ordenadas = [...paginas].sort((a, b) => a - b);
  return ordenadas.flatMap((pagina, indice) => {
    const anterior = ordenadas[indice - 1];
    if (anterior === undefined || pagina === anterior + 1) return [pagina];
    // Um salto de uma página só mostra o número, que ocupa o mesmo espaço das reticências.
    return pagina === anterior + 2 ? [anterior + 1, pagina] : [null, pagina];
  });
});

const primeiroDaPagina = computed(() => {
  const lista = store.lista;
  return lista ? (lista.pagina - 1) * lista.por_pagina + 1 : 0;
});
const ultimoDaPagina = computed(() => {
  const lista = store.lista;
  return lista ? primeiroDaPagina.value + lista.solicitacoes.length - 1 : 0;
});

/** Mostra uma data AAAA-MM-DD do AGHU como DD/MM/AAAA, sem conversão de fuso. */
const formatarDia = (valor: string | null) =>
  valor ? valor.split('-').reverse().join('/') : 'Não informada';

/** Carrega a página pedida e avisa se a leitura falhar. */
const irPara = async (pagina: number) => {
  try {
    await store.carregarLista(pagina);
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível carregar a lista de solicitações.'));
  }
};
/** Aplica os filtros agora, a partir da primeira página. */
const aplicarFiltros = () => {
  clearTimeout(temporizador);
  return irPara(1);
};

/** Ordena pela coluna do cabeçalho clicado. */
const ordenarPor = async (coluna: ColunaDaLista) => {
  try {
    await store.alternarOrdenacao(coluna);
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível ordenar a lista de solicitações.'));
  }
};

/** Limpa todos os filtros e a ordenação. */
const limparFiltros = async () => {
  clearTimeout(temporizador);
  try {
    await store.limparFiltrosDaLista();
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível carregar a lista de solicitações.'));
  }
};
</script>
