<template>
  <!-- Um caso (ou IHQ vinculada) gerado na confirmação da conferência. -->
  <article class="rounded-lg border border-gray-200 p-4 text-center">
    <p class="flex flex-wrap items-center justify-center gap-2 text-sm font-semibold uppercase tracking-wide text-paper-success-strong">
      <Badge :variant="tipoExame === 'CO' ? 'danger' : 'primary'" size="sm">{{ tipoExame }}</Badge>
      {{ resultado.tipo === 'IHQ' ? 'IHQ vinculada ao caso de origem' : 'Entrada confirmada · nº interno gerado' }}
    </p>

    <div class="mt-2 flex items-center justify-center gap-2">
      <p class="text-3xl font-extrabold tracking-tight text-gray-900 tabular-nums">{{ numeroGerado }}</p>
      <button
        type="button"
        class="focus-ring rounded-md p-2 text-gray-500 transition hover:bg-gray-100 hover:text-gray-800 active:bg-gray-200 active:scale-95"
        :aria-label="`Copiar ${numeroGerado}`"
        title="Copiar número"
        @click="copiar"
      >
        <ClipboardDocumentIcon class="h-6 w-6" />
      </button>
    </div>

    <div class="mt-2 flex flex-wrap items-center justify-center gap-2 text-sm text-gray-700">
      <Badge v-if="resultado.tipo === 'CASO' && resultado.caso.urgente" variant="danger" size="md">URGENTE</Badge>
      <span v-if="resultado.tipo === 'CASO'">
        Encaminhado para: <strong>{{ resultado.caso.etapaAtual ? ETAPAS[resultado.caso.etapaAtual] : '—' }}</strong>
        · {{ rotuloQuantidadeAmostras(resultado.caso.quantidade) }}
      </span>
      <span v-else>
        Caso de origem: <strong>{{ resultado.caso.numeroInterno }}</strong> · {{ resultado.caso.solicitacao.nomePaciente }}
      </span>
    </div>

    <!-- Congelação: acionar plantão -->
    <Alert
      v-if="resultado.tipo === 'CASO' && resultado.caso.tipoExame === 'CO'"
      variant="danger"
      title="Congelação: acionar equipe de plantão"
      class="mt-4 text-left"
    >
      <p>A cirurgia está em andamento. Avise o patologista de plantão agora e registre o acionamento.</p>
      <Button
        v-if="authStore.hasPermission('recepcao:acionar_plantao')"
        class="mt-3"
        variant="danger"
        size="sm"
        :loading="registrandoPlantao"
        :disabled="!!resultado.caso.plantaoAcionadoEm"
        @click="registrarPlantao"
      >
        <BellAlertIcon class="h-4 w-4 mr-1.5" aria-hidden="true" />
        {{
          resultado.caso.plantaoAcionadoEm
            ? `Plantão acionado às ${horario(resultado.caso.plantaoAcionadoEm)}`
            : 'Registrar acionamento do plantão'
        }}
      </Button>
    </Alert>

    <div class="mt-4 flex flex-wrap justify-center gap-2">
      <Button variant="outline" size="sm" @click="impressao = 'ETIQUETAS'">
        <PrinterIcon class="h-4 w-4 mr-1.5" aria-hidden="true" /> Imprimir etiqueta(s)
      </Button>
      <Button variant="outline" size="sm" @click="impressao = 'FICHA_TRABALHO'">
        <DocumentTextIcon class="h-4 w-4 mr-1.5" aria-hidden="true" /> Imprimir ficha de trabalho
      </Button>
      <router-link
        :to="rotaDoCaso(resultado.caso.numeroInterno, { aba: resultado.tipo === 'IHQ' ? 'ihq' : undefined })"
        class="focus-ring inline-flex items-center rounded border border-gray-300 bg-white px-3 py-1.5 text-sm font-bold text-gray-700 transition hover:bg-gray-50 active:bg-gray-100"
      >
        <ArrowTopRightOnSquareIcon class="h-4 w-4 mr-1.5" aria-hidden="true" />
        {{ resultado.tipo === 'IHQ' ? 'Abrir caso de origem' : 'Abrir detalhe do caso' }}
      </router-link>
    </div>

    <PrintPreview :show="impressao !== null" :caso="resultado.caso" :tipo="impressao ?? 'ETIQUETAS'" @close="impressao = null" />
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useToast } from 'vue-toastification';
import {
  ArrowTopRightOnSquareIcon,
  BellAlertIcon,
  ClipboardDocumentIcon,
  DocumentTextIcon,
  PrinterIcon,
} from '@heroicons/vue/24/outline';
import Alert from '../../Alert.vue';
import Badge from '../../Badge.vue';
import Button from '../../Button.vue';
import PrintPreview from '../PrintPreview.vue';
import { ETAPAS } from '../../../constants/ap';
import { rotuloQuantidadeAmostras } from '../../../helpers/aghu';
import { rotaDoCaso } from '../../../helpers/rotas';
import { mensagemDeErro } from '../../../services/ap';
import { useAuthStore } from '../../../stores/auth';
import { useRecepcaoStore } from '../../../stores/recepcao';
import type { ResultadoRecepcao, TipoExame, TipoImpressao } from '../../../types/ap';

const props = defineProps<{ resultado: ResultadoRecepcao }>();

const toast = useToast();
const authStore = useAuthStore();
const recepcao = useRecepcaoStore();
const registrandoPlantao = ref(false);
const impressao = ref<TipoImpressao | null>(null);

const tipoExame = computed<TipoExame>(() => (props.resultado.tipo === 'IHQ' ? 'IHQ' : props.resultado.caso.tipoExame));
const numeroGerado = computed(() =>
  props.resultado.tipo === 'IHQ' ? props.resultado.ihq.codigoInternoIhq : props.resultado.caso.numeroInterno,
);

const horario = (iso: string) => new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

const copiar = async () => {
  try {
    await navigator.clipboard.writeText(numeroGerado.value);
    toast.success(`Nº ${numeroGerado.value} copiado.`);
  } catch {
    toast.error('Não foi possível copiar. Selecione o número e copie manualmente.');
  }
};

const registrarPlantao = async () => {
  registrandoPlantao.value = true;
  try {
    await recepcao.registrarPlantao(props.resultado.caso.numeroInterno);
    toast.success('Acionamento da equipe de plantão registrado no histórico do caso.');
  } catch (erro) {
    toast.error(mensagemDeErro(erro));
  } finally {
    registrandoPlantao.value = false;
  }
};
</script>
