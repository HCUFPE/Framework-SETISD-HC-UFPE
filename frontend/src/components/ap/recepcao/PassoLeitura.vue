<template>
  <div class="space-y-6">
    <Card>
      <div class="mx-auto max-w-2xl text-center">
        <Scan class="mx-auto h-10 w-10 text-paper-info" aria-hidden="true" />
        <h2 class="mt-2 text-xl font-bold text-gray-800">Ler etiqueta do AGHU</h2>
        <p class="mt-1 text-sm text-gray-500">Leia o código da etiqueta no frasco ou digite o número da solicitação.</p>

        <Alert v-if="recepcao.aghuIndisponivel" variant="warning" title="Recepção bloqueada" class="mt-4 text-left">
          AGHU indisponível no momento. A recepção de novas amostras está bloqueada. O registro de material sem
          etiqueta continua disponível.
        </Alert>

        <form class="mt-5 flex flex-col gap-3 sm:flex-row" novalidate @submit.prevent="ler">
          <label for="recepcao-leitura" class="sr-only">Número da solicitação AGHU</label>
          <input
            id="recepcao-leitura"
            ref="campo"
            v-model="codigo"
            type="text"
            inputmode="numeric"
            autocomplete="off"
            placeholder="Preencha o nº da solicitação AGHU"
            :disabled="recepcao.aghuIndisponivel"
            :aria-invalid="recepcao.mensagemLeitura ? 'true' : undefined"
            aria-describedby="recepcao-leitura-mensagem"
            :class="recepcao.mensagemLeitura ? 'border-2 border-paper-danger' : ''"
            class="form-control h-14 flex-1 text-center text-lg font-bold tracking-wider tabular-nums disabled:cursor-not-allowed disabled:bg-gray-100"
            @input="recepcao.mensagemLeitura = null"
          />
          <Button type="submit" class="h-14 sm:w-36" :loading="recepcao.lendo" :disabled="recepcao.aghuIndisponivel">
            Continuar
          </Button>
        </form>

        <div id="recepcao-leitura-mensagem" aria-live="polite" class="text-left">
          <Alert v-if="recepcao.mensagemLeitura" variant="danger" class="mt-3">
            <p class="font-semibold">{{ recepcao.mensagemLeitura.texto }}</p>
            <p v-if="recepcao.mensagemLeitura.dica" class="mt-1">{{ recepcao.mensagemLeitura.dica }}</p>
            <router-link
              v-if="recepcao.mensagemLeitura.casoNumero"
              :to="rotaDoCaso(recepcao.mensagemLeitura.casoNumero)"
              class="focus-ring mt-2 inline-block rounded font-bold underline hover:no-underline active:opacity-70"
            >
              Abrir o caso {{ recepcao.mensagemLeitura.casoNumero }}
            </router-link>
          </Alert>
        </div>

        <div class="mt-6 border-t border-gray-100 pt-5">
          <Button variant="danger" @click="emit('sem-etiqueta')">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2" aria-hidden="true" />
            Registrar não conformidade de material sem etiqueta do AGHU
          </Button>
        </div>
      </div>
    </Card>

    <Card>
      <template #header>
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 class="text-lg font-bold text-gray-800">Para receber</h2>
            <p class="text-sm text-gray-500">Solicitações do AGHU aguardando recebimento. Congelações primeiro, depois as mais antigas.</p>
          </div>
          <span
            v-if="!recepcao.carregandoPendentes && !recepcao.aghuIndisponivel && fila.length > 0"
            class="rounded-full bg-paper-warning-soft px-3 py-1 text-sm font-bold text-paper-warning-strong"
          >
            {{ fila.length }} {{ fila.length === 1 ? 'pendente' : 'pendentes' }}
          </span>
        </div>
      </template>

      <p v-if="recepcao.carregandoPendentes" class="py-6 text-center text-sm text-gray-500" role="status">
        Carregando solicitações...
      </p>
      <p v-else-if="recepcao.aghuIndisponivel" class="py-6 text-center text-sm text-gray-500">
        Lista indisponível enquanto o AGHU estiver fora do ar.
      </p>
      <div v-else-if="fila.length === 0" class="py-8 text-center">
        <CheckCircleIcon class="mx-auto h-10 w-10 text-paper-success" aria-hidden="true" />
        <p class="mt-2 font-bold text-gray-800">Tudo em dia</p>
        <p class="text-sm text-gray-500">Nenhuma solicitação aguardando recebimento.</p>
      </div>
      <ul v-else class="divide-y divide-gray-100" aria-label="Solicitações aguardando recebimento">
        <li
          v-for="item in fila"
          :key="item.codigoSolicitacao"
          class="flex flex-col gap-3 py-3 sm:flex-row sm:items-center"
        >
          <span
            :class="item.congelacao ? 'border-paper-danger' : 'border-gray-300'"
            class="hidden h-5 w-5 shrink-0 rounded-full border-2 sm:block"
            aria-hidden="true"
          ></span>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <Badge :variant="item.congelacao ? 'danger' : 'primary'" size="sm">{{ item.tipo }}</Badge>
              <span class="font-bold text-gray-900">{{ item.exame }}</span>
              <span class="text-sm tabular-nums text-gray-500">· Nº AGHU {{ item.codigoSolicitacao }}</span>
            </div>
            <p class="mt-1 truncate text-sm text-gray-600">{{ item.material }} · {{ item.origem }}</p>
          </div>
          <div class="flex items-center justify-between gap-4 sm:justify-end">
            <span
              :class="item.atrasada ? 'text-paper-danger-strong font-bold' : 'text-gray-500'"
              class="inline-flex items-center gap-1 whitespace-nowrap text-sm"
              :title="`Solicitada em ${item.data}`"
            >
              <ClockIcon class="h-4 w-4" aria-hidden="true" />
              há {{ item.espera }}
              <span v-if="item.atrasada" class="sr-only">(atrasada)</span>
            </span>
            <Button
              size="sm"
              :disabled="recepcao.aghuIndisponivel"
              :aria-label="`Iniciar recebimento da solicitação ${item.codigoSolicitacao}`"
              @click="lerDaLista(item.codigoSolicitacao)"
            >
              Iniciar recebimento
              <ArrowRightIcon class="ml-1 h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </li>
      </ul>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import { useToast } from 'vue-toastification';
import { ArrowRightIcon, CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import { Scan } from 'lucide-vue-next';
import Alert from '../../Alert.vue';
import Badge from '../../Badge.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import { HORAS_ALERTA_PENDENTE, ORIGENS } from '../../../constants/ap';
import { formatarDataHora, horasDesde, tempoDecorrido } from '../../../helpers/formato';
import { rotaDoCaso } from '../../../helpers/rotas';
import { mensagemDeErro } from '../../../services/ap';
import { useRecepcaoStore } from '../../../stores/recepcao';

const emit = defineEmits<{ (e: 'sem-etiqueta'): void }>();

const toast = useToast();
const recepcao = useRecepcaoStore();
const campo = ref<HTMLInputElement | null>(null);
const codigo = ref('');

/** Referência de "agora", atualizada a cada minuto para o tempo de espera. */
const agora = ref(new Date());
let relogio: ReturnType<typeof setInterval> | undefined;

/** Fila de tarefas: congelações primeiro, depois da mais antiga para a mais nova. */
const fila = computed(() =>
  [...recepcao.pendentes]
    .sort((a, b) => {
      const prioridade = (s: typeof a) => (s.tipoExameSugerido === 'CO' ? 0 : 1);
      return prioridade(a) - prioridade(b) || a.dataSolicitacao.localeCompare(b.dataSolicitacao);
    })
    .map((s) => ({
      codigoSolicitacao: s.codigoSolicitacao,
      tipo: s.tipoExameSugerido,
      congelacao: s.tipoExameSugerido === 'CO',
      exame: s.nomeExame,
      material: s.descricaoMaterial,
      origem: `${s.unidade} · ${ORIGENS[s.origem]}`,
      data: formatarDataHora(s.dataSolicitacao),
      espera: tempoDecorrido(s.dataSolicitacao, agora.value),
      atrasada: horasDesde(s.dataSolicitacao, agora.value) >= HORAS_ALERTA_PENDENTE,
    })),
);

/** Lê o número digitado/lido. */
const ler = async () => {
  try {
    await recepcao.lerCodigo(codigo.value);
    if (recepcao.passo === 1) codigo.value = '';
  } catch (erro) {
    toast.error(mensagemDeErro(erro));
  }
};

/** "Iniciar recebimento" na fila equivale a ler o número. */
const lerDaLista = async (numero: string) => {
  codigo.value = numero;
  await ler();
};

onMounted(async () => {
  relogio = setInterval(() => (agora.value = new Date()), 60_000);
  await nextTick();
  campo.value?.focus();
});

onUnmounted(() => clearInterval(relogio));

defineExpose({
  focar: () => campo.value?.focus(),
  /** Limpa o número digitado e coloca o foco no campo. */
  limparEFocar: () => {
    codigo.value = '';
    campo.value?.focus();
  },
});
</script>
