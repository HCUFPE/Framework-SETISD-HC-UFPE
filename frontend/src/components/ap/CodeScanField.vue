<template>
  <div class="relative w-full sm:w-80">
    <label for="leitura-global" class="sr-only">Ler código ou buscar caso</label>
    <div class="relative">
      <QrCodeIcon class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" aria-hidden="true" />
      <input
        id="leitura-global"
        ref="campo"
        v-model="codigo"
        type="text"
        autocomplete="off"
        spellcheck="false"
        placeholder="Ler código ou buscar caso (F2)"
        :aria-invalid="erro ? 'true' : undefined"
        aria-describedby="leitura-global-mensagem"
        :class="erro ? 'border-paper-danger focus:border-paper-danger focus:ring-paper-danger' : ''"
        class="form-control pl-10 pr-10"
        @keydown.enter.prevent="ler"
        @input="mensagem = null"
      />
      <span v-if="lendo" class="absolute right-3 top-1/2 -translate-y-1/2" role="status">
        <svg class="h-4 w-4 animate-spin text-paper-primary" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        <span class="sr-only">Lendo código...</span>
      </span>
    </div>
    <div
      id="leitura-global-mensagem"
      aria-live="polite"
      class="absolute left-0 right-0 top-full z-30 mt-1"
    >
      <p
        v-if="mensagem"
        :class="erro ? 'border-paper-danger/40 bg-paper-danger-soft text-paper-danger-strong' : 'border-paper-warning/50 bg-paper-warning-soft text-paper-warning-strong'"
        class="rounded-md border px-3 py-2 text-xs font-semibold shadow-paper"
      >
        {{ mensagem }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import { QrCodeIcon } from '@heroicons/vue/24/outline';
import { TIPOS_NAO_CONFORMIDADE } from '../../constants/ap';
import { formatarData } from '../../helpers/formato';
import { rotaDoCaso } from '../../helpers/rotas';
import { mensagemDeErro } from '../../services/ap';
import { useCasosStore } from '../../stores/casos';
import { useRecepcaoStore } from '../../stores/recepcao';

const router = useRouter();
const toast = useToast();
const casosStore = useCasosStore();
const recepcaoStore = useRecepcaoStore();

const campo = ref<HTMLInputElement | null>(null);
const codigo = ref('');
const mensagem = ref<string | null>(null);
const erro = ref(false);
const lendo = ref(false);

/** Exibe uma mensagem abaixo do campo, mantendo o texto lido. */
const avisar = (texto: string, ehErro: boolean) => {
  mensagem.value = texto;
  erro.value = ehErro;
};

/** Resolve o código lido/digitado e navega para a recepção ou para o caso. */
const ler = async () => {
  const lido = codigo.value.trim().toUpperCase();
  if (!lido) return;
  lendo.value = true;
  mensagem.value = null;
  try {
    const resolucao = await casosStore.resolverCodigo(lido);
    switch (resolucao.tipo) {
      case 'PENDENTE':
        recepcaoStore.iniciarConferencia(resolucao.solicitacao);
        await router.push('/recepcao');
        toast.info(`Solicitação AGHU ${resolucao.solicitacao.codigoSolicitacao} carregada para conferência.`);
        codigo.value = '';
        break;
      case 'CASO':
        await router.push(rotaDoCaso(resolucao.casoNumero, { aba: resolucao.aba, item: resolucao.itemCodigo }));
        codigo.value = '';
        break;
      case 'RECEBIDA':
        await router.push(rotaDoCaso(resolucao.casoNumero));
        codigo.value = '';
        break;
      case 'DEVOLVIDA':
        avisar(
          `A solicitação ${resolucao.solicitacao.codigoSolicitacao} foi devolvida em ${formatarData(resolucao.devolvidaEm)} por não conformidade: ${TIPOS_NAO_CONFORMIDADE[resolucao.tipoNaoConformidade]}.`,
          false,
        );
        break;
      default:
        avisar(`Nenhum registro encontrado para o código ${lido}. Confira a etiqueta ou digite o número.`, true);
    }
  } catch (e) {
    avisar(mensagemDeErro(e), true);
  } finally {
    lendo.value = false;
  }
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
onUnmounted(() => document.removeEventListener('keydown', aoTeclar));
</script>
