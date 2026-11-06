<template>
  <Card>
    <div class="mb-4">
      <h2 class="text-lg font-bold text-gray-800">Solicitações do AGHU</h2>
      <p class="text-sm text-gray-500">Das mais recentes para as mais antigas. Clique em uma linha para conferir.</p>
    </div>

    <div class="w-full overflow-x-auto" :class="{ 'opacity-60': store.carregandoLista }">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-xs font-semibold tracking-wider text-left text-gray-500 uppercase border-b border-gray-200 bg-gray-50">
            <th class="px-3 py-2">Código</th>
            <th class="px-3 py-2">Solicitada em</th>
            <th class="px-3 py-2">Paciente</th>
            <th class="px-3 py-2">Prontuário</th>
            <th class="px-3 py-2">Origem</th>
            <th class="px-3 py-2">Clínica</th>
            <th class="px-3 py-2">Bancadas</th>
            <th class="px-3 py-2 text-center">Amostras</th>
            <th class="px-3 py-2">Situação</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="linha in store.lista?.solicitacoes ?? []"
            :key="linha.codigo"
            class="cursor-pointer hover:bg-gray-50"
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
            <td colspan="9" class="px-3 py-8 text-center text-gray-500">Nenhuma solicitação encontrada.</td>
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
import { computed } from 'vue';
import { useToast } from 'vue-toastification';
import Card from '../Card.vue';
import { mensagemDeErro, SITUACOES, useRecebimentoStore } from '../../stores/recebimento';

const emit = defineEmits<{ abrir: [codigo: string] }>();
const store = useRecebimentoStore();
const toast = useToast();

const BASE_PAGINA = 'min-w-9 h-9 px-3 rounded border text-sm disabled:cursor-not-allowed';
const BOTAO_PAGINA = `${BASE_PAGINA} border-gray-300 bg-white font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50`;
const PAGINA_ATUAL = `${BASE_PAGINA} border-paper-primary bg-paper-primary font-bold text-white`;
const VIZINHAS_DA_ATUAL = 1;

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
</script>
