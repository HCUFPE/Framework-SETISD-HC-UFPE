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
          <Alert v-if="recepcao.mensagemLeitura" :variant="recepcao.mensagemLeitura.variante ?? 'danger'" class="mt-3">
            <p class="font-semibold">{{ recepcao.mensagemLeitura.texto }}</p>
            <p v-if="recepcao.mensagemLeitura.dica" class="mt-1">{{ recepcao.mensagemLeitura.dica }}</p>
            <ul v-if="recepcao.mensagemLeitura.recebimentos?.length" class="mt-2 space-y-1">
              <li v-for="r in recepcao.mensagemLeitura.recebimentos" :key="`${r.siglaExame}-${r.casoNumero}`">
                {{ r.nomeExame }} ({{ r.siglaExame }}) →
                <template v-if="r.ihqCodigo">{{ r.ihqCodigo }} no caso</template>
                <router-link
                  :to="rotaDoCaso(r.casoNumero, { aba: r.ihqCodigo ? 'ihq' : undefined })"
                  class="focus-ring rounded font-bold underline hover:no-underline active:opacity-70"
                >
                  {{ r.casoNumero }}
                </router-link>
              </li>
            </ul>
            <ul v-if="recepcao.mensagemLeitura.cancelamentos?.length" class="mt-2 space-y-2">
              <li v-for="(item, index) in recepcao.mensagemLeitura.cancelamentos" :key="`${item.canceladoEm}-${index}`">
                {{ item.motivo }} — {{ item.canceladoPor.nome }} — {{ formatarData(item.canceladoEm) }}
              </li>
            </ul>
          </Alert>
        </div>

        <div class="mt-6 border-t border-gray-100 pt-5">
          <Button variant="danger" aria-haspopup="dialog" @click="ncSemEtiquetaAberta = true">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2" aria-hidden="true" />
            Registrar não conformidade de material sem etiqueta do AGHU
          </Button>
          <NaoConformidadeModal
            :show="ncSemEtiquetaAberta"
            :contexto="{ tipo: 'SEM_ETIQUETA' }"
            @close="ncSemEtiquetaAberta = false"
            @registrado="aposRegistroSemEtiqueta"
          />
        </div>
      </div>
    </Card>

    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-gray-800">
          <span
            v-if="fila.length > 0"
            class="inline-flex items-center rounded-full bg-paper-warning-soft px-3 py-1 text-base font-bold text-paper-warning-strong"
          >
            {{ rotuloQuantidadeSolicitacoes(fila.length) }} para receber
          </span>
          <template v-else>Para receber</template>
        </h2>
        <p class="mt-1 text-sm text-gray-500">
          Solicitações de exames do AGHU aguardando recebimento. Congelações primeiro, depois as mais antigas.
        </p>
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
          v-for="item in filaDaPagina"
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
              <span class="font-bold tabular-nums text-gray-900">Solicitação {{ item.codigoSolicitacao }}</span>
              <Badge
                v-for="tipo in item.tipos"
                :key="tipo"
                :variant="tipo === 'CO' ? 'danger' : 'primary'"
                size="sm"
                :title="TIPOS_EXAME[tipo].nome"
              >
                {{ tipo }}
              </Badge>
              <span class="text-sm text-gray-500">· {{ item.amostras }} · {{ item.paciente }}</span>
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
              {{ item.data }} · {{ item.espera }}
              <span v-if="item.atrasada" class="sr-only">(atrasada)</span>
            </span>
            <Button
              size="sm"
              :disabled="recepcao.aghuIndisponivel"
              :aria-label="`Iniciar recebimento da solicitação ${item.codigoSolicitacao}`"
              @click="iniciarDaLista(item.codigoSolicitacao)"
            >
              Iniciar recebimento
              <ArrowRightIcon class="ml-1 h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </li>
      </ul>

      <!-- Paginação da fila (mesmo padrão da tabela da Consulta de casos) -->
      <div
        v-if="!recepcao.carregandoPendentes && !recepcao.aghuIndisponivel && fila.length > ITENS_POR_PAGINA"
        class="mt-2 flex flex-col items-center justify-between gap-2 border-t border-gray-100 pt-3 text-sm text-gray-600 sm:flex-row"
      >
        <span aria-live="polite">Exibindo {{ inicioPagina }}–{{ fimPagina }} de {{ fila.length }}</span>
        <div class="flex items-center gap-2">
          <Button variant="secondary" size="sm" :disabled="pagina <= 1" aria-label="Página anterior" @click="irParaPagina(pagina - 1)">
            <ChevronLeftIcon class="h-4 w-4 mr-1" aria-hidden="true" /> Anterior
          </Button>
          <span class="px-1 text-xs text-gray-500">Página {{ pagina }} de {{ totalPaginas }}</span>
          <Button variant="secondary" size="sm" :disabled="pagina >= totalPaginas" aria-label="Próxima página" @click="irParaPagina(pagina + 1)">
            Próxima <ChevronRightIcon class="h-4 w-4 ml-1" aria-hidden="true" />
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useToast } from 'vue-toastification';
import {
  ArrowRightIcon,
  CheckCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline';
import { Scan } from 'lucide-vue-next';
import Alert from '../../Alert.vue';
import Badge from '../../Badge.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import NaoConformidadeModal from '../NaoConformidadeModal.vue';
import { DIAS_ALERTA_PENDENTE, NAO_INFORMADO, TIPOS_EXAME, rotuloOrigem } from '../../../constants/ap';
import { agruparPorSolicitacao, resumoMaterial, rotuloQuantidadeAmostras, rotuloQuantidadeSolicitacoes } from '../../../helpers/aghu';
import { diasDesde, formatarData, rotuloEsperaDias } from '../../../helpers/formato';
import { rotaDoCaso } from '../../../helpers/rotas';
import { mensagemDeErro } from '../../../services/ap';
import { useRecepcaoStore } from '../../../stores/recepcao';

/** `devolvido`: não conformidade de material sem etiqueta registrada. */
const emit = defineEmits<{ (e: 'devolvido'): void }>();

const toast = useToast();
const recepcao = useRecepcaoStore();
const campo = ref<HTMLInputElement | null>(null);
const codigo = ref('');
const ncSemEtiquetaAberta = ref(false);

/** Referência de "agora", atualizada a cada minuto para o tempo de espera. */
const agora = ref(new Date());
let relogio: ReturnType<typeof setInterval> | undefined;

/**
 * Fila de tarefas, um item por solicitação do AGHU com tipos de exame pendentes:
 * com Congelação primeiro, depois da mais antiga para a mais nova.
 */
const fila = computed(() =>
  agruparPorSolicitacao(recepcao.pendentes)
    .map(({ codigoSolicitacao, exames }) => {
      const s = exames[0];
      const amostras = exames.reduce((total, e) => total + e.amostras.length, 0);
      return {
        codigoSolicitacao,
        tipos: exames.map((e) => e.tipoExameSugerido),
        amostras: rotuloQuantidadeAmostras(amostras),
        paciente: s.nomePaciente || NAO_INFORMADO,
        congelacao: exames.some((e) => e.tipoExameSugerido === 'CO'),
        dataIso: s.dataSolicitacao,
        material: exames.map(resumoMaterial).join(' · '),
        origem: `${s.unidade || NAO_INFORMADO} · ${rotuloOrigem(s.origem)}`,
        data: formatarData(s.dataSolicitacao),
        espera: rotuloEsperaDias(s.dataSolicitacao, agora.value),
        atrasada: diasDesde(s.dataSolicitacao, agora.value) >= DIAS_ALERTA_PENDENTE,
      };
    })
    .sort((a, b) => Number(b.congelacao) - Number(a.congelacao) || a.dataIso.localeCompare(b.dataIso)),
);

/** Paginação da fila: 10 solicitações por página, como nas demais listas do sistema. */
const ITENS_POR_PAGINA = 10;
const pagina = ref(1);
const totalPaginas = computed(() => Math.max(1, Math.ceil(fila.value.length / ITENS_POR_PAGINA)));
const filaDaPagina = computed(() => fila.value.slice((pagina.value - 1) * ITENS_POR_PAGINA, pagina.value * ITENS_POR_PAGINA));
const inicioPagina = computed(() => (fila.value.length === 0 ? 0 : (pagina.value - 1) * ITENS_POR_PAGINA + 1));
const fimPagina = computed(() => Math.min(pagina.value * ITENS_POR_PAGINA, fila.value.length));

/** Muda de página e leva a lista de volta ao topo. */
const irParaPagina = async (nova: number) => {
  pagina.value = Math.min(Math.max(1, nova), totalPaginas.value);
  await nextTick();
  document.querySelector('[aria-label="Solicitações aguardando recebimento"]')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

/** Se a fila diminuir (recebimento ou devolução), mantém a página dentro do total. */
watch(totalPaginas, (total) => {
  if (pagina.value > total) pagina.value = total;
});

/** Lê o número digitado/lido. */
const ler = async () => {
  try {
    await recepcao.lerCodigo(codigo.value);
    if (recepcao.passo === 1) codigo.value = '';
  } catch (erro) {
    toast.error(mensagemDeErro(erro));
  }
};

/** "Iniciar recebimento" na fila abre a conferência da solicitação. */
const iniciarDaLista = async (codigoSolicitacao: string) => {
  codigo.value = '';
  try {
    await recepcao.lerCodigo(codigoSolicitacao);
  } catch (erro) {
    toast.error(mensagemDeErro(erro));
  }
};

/** Após registrar a devolução de material sem etiqueta, fecha o formulário e volta ao início. */
const aposRegistroSemEtiqueta = () => {
  ncSemEtiquetaAberta.value = false;
  emit('devolvido');
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
