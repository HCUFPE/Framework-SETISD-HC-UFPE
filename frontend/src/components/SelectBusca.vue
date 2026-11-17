<template>
  <!--
    Campo de seleção com busca por digitação (combobox). Substitui o <select> nativo:
    abre uma lista com campo de busca, filtra sem diferenciar maiúsculas/acentos e aceita teclado.
  -->
  <div ref="raiz" class="relative" @focusout="aoSairDoFoco">
    <button
      :id="id"
      ref="botao"
      type="button"
      class="form-control flex items-center justify-between gap-2 text-left disabled:cursor-not-allowed disabled:bg-gray-100"
      :class="[aberto ? 'border-paper-primary ring-1 ring-paper-primary' : '', invalid ? 'border-paper-danger' : '']"
      :disabled="disabled"
      aria-haspopup="listbox"
      :aria-expanded="aberto ? 'true' : 'false'"
      :aria-controls="`${id}-lista`"
      :aria-invalid="invalid ? 'true' : undefined"
      :aria-describedby="ariaDescribedby"
      @click="alternar"
      @keydown="aoTeclarNoBotao"
    >
      <span :class="selecionada ? 'text-gray-900' : 'text-gray-500'" class="min-w-0 truncate">
        {{ selecionada?.rotulo ?? placeholder }}
      </span>
      <ChevronDownIcon :class="aberto ? 'rotate-180' : ''" class="h-4 w-4 shrink-0 text-gray-500 transition-transform" aria-hidden="true" />
    </button>

    <div
      v-if="aberto"
      :class="paraCima ? 'bottom-full mb-1' : 'top-full mt-1'"
      class="absolute left-0 right-0 z-40 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg"
    >
      <div class="relative border-b border-gray-100 p-2">
        <MagnifyingGlassIcon class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
        <input
          ref="campoBusca"
          v-model="termo"
          type="text"
          role="combobox"
          autocomplete="off"
          spellcheck="false"
          :aria-label="`Buscar em ${rotuloAcessivel}`"
          :aria-controls="`${id}-lista`"
          aria-expanded="true"
          aria-autocomplete="list"
          :aria-activedescendant="ativo >= 0 ? `${id}-opcao-${ativo}` : undefined"
          placeholder="Digite para buscar"
          class="w-full rounded border border-gray-300 py-1.5 pl-8 pr-2 text-sm focus:border-paper-primary focus:outline-none focus:ring-1 focus:ring-paper-primary"
          @input="ativo = filtradas.length > 0 ? 0 : -1"
          @keydown.down.prevent="mover(1)"
          @keydown.up.prevent="mover(-1)"
          @keydown.enter.prevent="escolherAtiva"
          @keydown.esc.prevent="fechar(true)"
          @keydown.tab="fechar(false)"
        />
      </div>
      <ul :id="`${id}-lista`" ref="lista" role="listbox" :aria-label="rotuloAcessivel" class="overflow-y-auto py-1" :style="{ maxHeight: `${alturaLista}px` }">
        <li
          v-for="(opcao, indice) in filtradas"
          :id="`${id}-opcao-${indice}`"
          :key="String(opcao.valor)"
          role="option"
          :aria-selected="opcao.valor === modelValue ? 'true' : 'false'"
          :class="[
            indice === ativo ? 'bg-paper-primary-soft text-paper-primary-strong' : 'text-gray-800',
            opcao.valor === modelValue ? 'font-bold' : '',
          ]"
          class="flex cursor-pointer items-start justify-between gap-2 px-3 py-2 text-sm transition-colors active:bg-paper-primary-soft"
          @mousedown.prevent="escolher(opcao)"
          @mousemove="ativo = indice"
        >
          <span class="min-w-0">{{ opcao.rotulo }}</span>
          <CheckIcon v-if="opcao.valor === modelValue" class="mt-0.5 h-4 w-4 shrink-0 text-paper-primary-strong" aria-hidden="true" />
        </li>
        <li v-if="filtradas.length === 0" class="px-3 py-2 text-sm text-gray-500" role="status">Nenhuma opção encontrada.</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { CheckIcon, ChevronDownIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline';

export interface OpcaoSelect {
  valor: string | number;
  rotulo: string;
}

const props = withDefaults(
  defineProps<{
    id: string;
    modelValue: string | number | null | undefined;
    opcoes: OpcaoSelect[];
    placeholder?: string;
    /** Nome usado pelos leitores de tela na busca e na lista (padrão: o placeholder). */
    rotulo?: string;
    invalid?: boolean;
    disabled?: boolean;
    ariaDescribedby?: string;
  }>(),
  { placeholder: 'Selecione', rotulo: undefined, invalid: false, disabled: false, ariaDescribedby: undefined },
);

const emit = defineEmits<{
  (e: 'update:modelValue', valor: string | number): void;
  (e: 'blur'): void;
}>();

const raiz = ref<HTMLElement | null>(null);
const botao = ref<HTMLButtonElement | null>(null);
const campoBusca = ref<HTMLInputElement | null>(null);
const lista = ref<HTMLElement | null>(null);
const aberto = ref(false);
const termo = ref('');
const ativo = ref(-1);

const rotuloAcessivel = computed(() => props.rotulo ?? props.placeholder);
const selecionada = computed(() => props.opcoes.find((o) => o.valor === props.modelValue));

/** Texto sem acentos e em minúsculas, para a busca. */
const normalizar = (texto: string) => texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

const filtradas = computed(() => {
  const alvo = normalizar(termo.value);
  return alvo ? props.opcoes.filter((o) => normalizar(o.rotulo).includes(alvo)) : props.opcoes;
});

/** Mantém a opção ativa visível ao navegar pelo teclado. */
const rolarParaAtiva = async () => {
  await nextTick();
  lista.value?.querySelector<HTMLElement>(`#${CSS.escape(`${props.id}-opcao-${ativo.value}`)}`)?.scrollIntoView({ block: 'nearest' });
};

/** Altura padrão da lista de opções (px) e mínimo aceitável antes de abrir para cima. */
const ALTURA_PADRAO = 256;
const ALTURA_MINIMA = 140;
/** Espaço ocupado pelo campo de busca e pelas bordas do painel (px). */
const ESPACO_BUSCA = 64;
const alturaLista = ref(ALTURA_PADRAO);
const paraCima = ref(false);

/** Ancestral que recorta o conteúdo (ex.: corpo de um modal com rolagem) ou a própria janela. */
const limitesVisiveis = (el: HTMLElement): { topo: number; base: number } => {
  let atual = el.parentElement;
  while (atual && atual !== document.body) {
    const estilo = getComputedStyle(atual);
    if (/(auto|scroll|hidden)/.test(estilo.overflowY)) {
      const r = atual.getBoundingClientRect();
      return { topo: Math.max(r.top, 0), base: Math.min(r.bottom, window.innerHeight) };
    }
    atual = atual.parentElement;
  }
  return { topo: 0, base: window.innerHeight };
};

/**
 * Ajusta a lista ao espaço visível: abre para baixo limitando a altura e, se faltar espaço
 * embaixo e sobrar em cima, abre para cima. Evita que a lista fique cortada dentro de modais.
 */
const posicionar = () => {
  const el = botao.value;
  if (!el) return;
  const r = el.getBoundingClientRect();
  const { topo, base } = limitesVisiveis(el);
  const abaixo = base - r.bottom - ESPACO_BUSCA - 8;
  const acima = r.top - topo - ESPACO_BUSCA - 8;
  paraCima.value = abaixo < ALTURA_MINIMA && acima > abaixo;
  alturaLista.value = Math.max(ALTURA_MINIMA, Math.min(ALTURA_PADRAO, paraCima.value ? acima : abaixo));
};

const abrir = async (textoInicial = '') => {
  if (props.disabled) return;
  posicionar();
  termo.value = textoInicial;
  aberto.value = true;
  const indiceSelecionado = filtradas.value.findIndex((o) => o.valor === props.modelValue);
  ativo.value = indiceSelecionado >= 0 ? indiceSelecionado : filtradas.value.length > 0 ? 0 : -1;
  await nextTick();
  campoBusca.value?.focus();
  await rolarParaAtiva();
};

const fechar = (devolverFoco: boolean) => {
  if (!aberto.value) return;
  aberto.value = false;
  termo.value = '';
  if (devolverFoco) botao.value?.focus();
};

const alternar = () => (aberto.value ? fechar(true) : abrir());

const escolher = (opcao: OpcaoSelect) => {
  emit('update:modelValue', opcao.valor);
  fechar(true);
};

const escolherAtiva = () => {
  const opcao = filtradas.value[ativo.value];
  if (opcao) escolher(opcao);
};

const mover = (passo: number) => {
  const total = filtradas.value.length;
  if (total === 0) return;
  ativo.value = (ativo.value + passo + total) % total;
  void rolarParaAtiva();
};

/** Setas, Enter e Espaço abrem a lista; digitar uma letra abre já buscando por ela. */
const aoTeclarNoBotao = (evento: KeyboardEvent) => {
  if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(evento.key)) {
    evento.preventDefault();
    void abrir();
  } else if (evento.key.length === 1 && !evento.ctrlKey && !evento.metaKey && !evento.altKey) {
    evento.preventDefault();
    void abrir(evento.key);
  }
};

/** Fecha quando o foco sai do componente (clique fora ou Tab). */
const aoSairDoFoco = (evento: FocusEvent) => {
  const destino = evento.relatedTarget as Node | null;
  if (destino && raiz.value?.contains(destino)) return;
  fechar(false);
  emit('blur');
};
</script>
