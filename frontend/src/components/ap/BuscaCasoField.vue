<template>
  <div class="relative w-full sm:w-96 lg:w-[26.5rem]">
    <label for="busca-caso-global" class="sr-only">Buscar caso por número, prontuário ou paciente</label>
    <div class="relative">
      <MagnifyingGlassIcon class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" aria-hidden="true" />
      <input
        id="busca-caso-global"
        ref="campo"
        v-model="termo"
        type="text"
        role="combobox"
        autocomplete="off"
        spellcheck="false"
        placeholder="Buscar por nº do caso, prontuário ou paciente (F2)"
        aria-autocomplete="list"
        aria-controls="busca-caso-lista"
        :aria-expanded="aberto ? 'true' : 'false'"
        :aria-activedescendant="ativo >= 0 ? `busca-caso-opcao-${ativo}` : undefined"
        aria-describedby="busca-caso-dica"
        class="form-control pl-10 pr-10"
        @input="aoDigitar"
        @keydown.down.prevent="mover(1)"
        @keydown.up.prevent="mover(-1)"
        @keydown.enter.prevent="confirmar"
        @keydown.esc="fechar"
        @focus="reabrir"
        @blur="fechar"
      />
      <span v-if="buscando" class="absolute right-3 top-1/2 -translate-y-1/2" role="status">
        <svg class="h-4 w-4 animate-spin text-paper-primary" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        <span class="sr-only">Buscando casos...</span>
      </span>
    </div>
    <p id="busca-caso-dica" class="sr-only">
      Digite ao menos {{ MINIMO_CARACTERES }} caracteres do número do caso, do prontuário ou do nome do paciente.
    </p>

    <div
      v-show="aberto"
      class="absolute left-0 right-0 top-full z-30 mt-1 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg"
    >
      <ul id="busca-caso-lista" role="listbox" aria-label="Casos encontrados" class="max-h-96 overflow-y-auto py-1">
        <li
          v-for="(caso, indice) in resultado.itens"
          :id="`busca-caso-opcao-${indice}`"
          :key="caso.numeroInterno"
          role="option"
          :aria-selected="indice === ativo"
          :class="indice === ativo ? 'bg-paper-primary-soft' : 'hover:bg-gray-50'"
          class="cursor-pointer px-3 py-2 transition-colors active:bg-gray-100"
          @mousedown.prevent="abrir(caso.numeroInterno)"
          @mousemove="ativo = indice"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="font-bold tabular-nums text-gray-900">{{ caso.numeroInterno }}</span>
            <StatusCasoBadge :status="caso.status" />
          </div>
          <p class="mt-0.5 truncate text-xs text-gray-600">
            <strong>{{ caso.tipoExame }}</strong> · {{ caso.nomePaciente }} · Pront. {{ caso.prontuario }}
          </p>
        </li>
      </ul>
      <p
        v-if="resultado.total === 0"
        class="px-3 py-3 text-sm text-gray-600"
        role="status"
      >
        Nenhum caso encontrado para <strong>{{ termoBuscado }}</strong>.
      </p>
      <p
        v-else-if="resultado.total > resultado.itens.length"
        class="border-t border-gray-100 bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-600"
        role="status"
      >
        {{ resultado.total }} resultados — exibindo {{ resultado.itens.length }}. Refine a busca.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import StatusCasoBadge from './StatusCasoBadge.vue';
import { rotaDoCaso } from '../../helpers/rotas';
import { mensagemDeErro } from '../../services/ap';
import { useCasosStore } from '../../stores/casos';
import type { ResultadoBuscaCasos } from '../../types/ap';

const MINIMO_CARACTERES = 2;
const LIMITE_RESULTADOS = 8;
const ESPERA_DIGITACAO_MS = 250;

const router = useRouter();
const toast = useToast();
const casosStore = useCasosStore();

const campo = ref<HTMLInputElement | null>(null);
const termo = ref('');
/** Texto que gerou o resultado exibido. */
const termoBuscado = ref('');
const resultado = ref<ResultadoBuscaCasos>({ itens: [], total: 0 });
const aberto = ref(false);
const ativo = ref(-1);
const buscando = ref(false);

let temporizador: ReturnType<typeof setTimeout> | undefined;
/** Identifica a busca mais recente, para descartar respostas fora de ordem. */
let ultimaBusca = 0;

const termoValido = (): string | null => {
  const texto = termo.value.trim();
  return texto.length >= MINIMO_CARACTERES ? texto : null;
};

/** Executa a busca do texto atual e abre a lista com o resultado. */
const buscar = async (): Promise<void> => {
  clearTimeout(temporizador);
  const texto = termoValido();
  if (!texto) {
    fechar();
    resultado.value = { itens: [], total: 0 };
    return;
  }
  const id = ++ultimaBusca;
  buscando.value = true;
  try {
    const encontrado = await casosStore.buscar(texto, LIMITE_RESULTADOS);
    if (id !== ultimaBusca) return;
    resultado.value = encontrado;
    termoBuscado.value = texto;
    ativo.value = -1;
    aberto.value = true;
  } catch (e) {
    toast.error(mensagemDeErro(e));
  } finally {
    if (id === ultimaBusca) buscando.value = false;
  }
};

const aoDigitar = () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(buscar, ESPERA_DIGITACAO_MS);
};

const fechar = () => {
  aberto.value = false;
  ativo.value = -1;
};

/** Ao voltar o foco, reabre a lista se o resultado ainda corresponde ao texto. */
const reabrir = () => {
  if (termoValido() && termoBuscado.value === termo.value.trim()) aberto.value = true;
};

/** Move o destaque pela lista com as setas. */
const mover = (passo: number) => {
  const total = resultado.value.itens.length;
  if (!aberto.value || total === 0) {
    reabrir();
    return;
  }
  ativo.value = (ativo.value + passo + total) % total;
};

/** Abre o detalhe do caso e limpa o campo. */
const abrir = async (numeroInterno: string) => {
  clearTimeout(temporizador);
  ultimaBusca++;
  buscando.value = false;
  fechar();
  termo.value = '';
  resultado.value = { itens: [], total: 0 };
  campo.value?.blur();
  await router.push(rotaDoCaso(numeroInterno));
};

/** Enter: abre o caso destacado ou, sem destaque, o caso cujo número é exatamente o texto. */
const confirmar = async () => {
  if (aberto.value && ativo.value >= 0) {
    const caso = resultado.value.itens[ativo.value];
    if (caso) await abrir(caso.numeroInterno);
    return;
  }
  await buscar();
  const texto = termo.value.trim().toUpperCase();
  const exato = resultado.value.itens.find((c) => c.numeroInterno.toUpperCase() === texto);
  if (exato) await abrir(exato.numeroInterno);
};

/** F2 coloca o foco no campo a partir de qualquer tela. */
const aoTeclar = (evento: KeyboardEvent) => {
  if (evento.key === 'F2') {
    evento.preventDefault();
    campo.value?.focus();
    campo.value?.select();
  }
};

onMounted(() => document.addEventListener('keydown', aoTeclar));
onUnmounted(() => {
  document.removeEventListener('keydown', aoTeclar);
  clearTimeout(temporizador);
});
</script>
