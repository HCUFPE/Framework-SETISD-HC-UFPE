<template>
  <div v-if="recepcao.solicitacao" class="space-y-4">
    <Alert
      v-if="recepcao.amostraBipadaSituacao"
      variant="warning"
      :title="`Amostra ${recepcao.amostraBipada} já ${recepcao.amostraBipadaSituacao.situacaoRecepcao === 'DEVOLVIDA' ? 'devolvida' : recepcao.amostraBipadaSituacao.situacaoRecepcao === 'CANCELADA' ? 'cancelada' : 'recebida'}`"
    >
      <template v-if="recepcao.amostraBipadaSituacao.situacaoRecepcao === 'RECEBIDA'">
        O grupo <strong>{{ recepcao.amostraBipadaSituacao.tipoExame }}</strong> desta amostra já foi recebido
        <template v-if="recepcao.amostraBipadaSituacao.casoNumero">
          (caso <strong>{{ recepcao.amostraBipadaSituacao.casoNumero }}</strong>)
        </template>
        <template v-else-if="recepcao.amostraBipadaSituacao.ihqCodigo">
          (<strong>{{ recepcao.amostraBipadaSituacao.ihqCodigo }}</strong>)
        </template>.
      </template>
      <template v-else-if="recepcao.amostraBipadaSituacao.situacaoRecepcao === 'DEVOLVIDA'">
        O grupo <strong>{{ recepcao.amostraBipadaSituacao.tipoExame }}</strong> desta amostra já foi devolvido por não conformidade.
      </template>
      <template v-else>
        O grupo <strong>{{ recepcao.amostraBipadaSituacao.tipoExame }}</strong> desta amostra foi cancelado
        <template v-if="recepcao.amostraBipadaSituacao.cancelamento?.motivo"> pelo motivo: {{ recepcao.amostraBipadaSituacao.cancelamento.motivo }}</template>.
      </template>
      Os demais exames pendentes desta solicitação seguem disponíveis para recebimento abaixo.
    </Alert>

    <div class="grid gap-6 lg:grid-cols-3">
    <Card class="lg:col-span-2">
      <template #header>
        <h2 class="text-lg font-bold text-gray-800">Dados da solicitação</h2>
      </template>
      <DadosSolicitacao
        class="-mt-4"
        :solicitacao="recepcao.solicitacao"
        :exames="recepcao.exames"
        :amostra-bipada="recepcao.amostraBipada"
        titulo="Amostras aguardando recebimento"
      />
      <p v-if="jaTratados.length" class="mt-3 text-xs text-gray-600">
        Outros exames desta solicitação:
        <template v-for="(e, i) in jaTratados" :key="e.id">
          <span v-if="i > 0"> · </span>
          <strong>{{ e.tipoExameSugerido }}</strong>
          {{ e.situacaoRecepcao === 'DEVOLVIDA' ? 'devolvido' : `já recebido (${e.casoNumero ?? e.ihqCodigo ?? '—'})` }}
        </template>
      </p>
    </Card>

    <div class="lg:sticky lg:top-28 self-start">
      <Card>
        <template #header>
          <div class="flex items-start justify-between gap-2">
            <div>
              <h2 class="text-lg font-bold text-gray-800">Conferência</h2>
              <p class="text-sm text-gray-500">Compare cada amostra e a requisição em papel com os dados do AGHU.</p>
            </div>
            <p class="shrink-0 text-xs text-gray-500"><span class="text-paper-danger">*</span> Obrigatório</p>
          </div>
        </template>

        <form id="form-conferencia" novalidate class="-mt-4 space-y-4" @submit.prevent="enviar">
          <!-- Resumo de erros -->
          <div v-if="tentouConfirmar && listaErros.length" ref="resumo" tabindex="-1" class="focus:outline-none">
            <Alert
              variant="danger"
              :title="`Faltam ${listaErros.length} campo${listaErros.length > 1 ? 's' : ''} obrigatório${listaErros.length > 1 ? 's' : ''} para confirmar`"
            >
              <ul class="list-disc pl-5">
                <li v-for="item in listaErros" :key="item.id">
                  <a :href="`#${item.id}`" class="font-semibold underline hover:no-underline" @click.prevent="focarCampo(item.id)">
                    {{ item.rotulo }}
                  </a>
                  — {{ item.mensagem }}
                </li>
              </ul>
            </Alert>
          </div>

          <!-- Urgência: vale para a solicitação (todos os casos gerados nesta conferência) -->
          <fieldset v-if="principaisSelecionados.length" id="campo-urgente" tabindex="-1" class="focus:outline-none">
            <legend class="form-label">Caso urgente? <span class="text-paper-danger">*</span></legend>
            <div class="flex gap-2" role="radiogroup">
              <label
                v-for="opcao in opcoesUrgencia"
                :key="opcao.valor"
                :class="[
                  urgente === opcao.valor ? opcao.ativo : 'border-gray-300 bg-white text-gray-700',
                  congelacaoSelecionada ? 'cursor-not-allowed' : 'cursor-pointer active:bg-gray-100',
                  congelacaoSelecionada && urgente !== opcao.valor ? 'opacity-50' : '',
                  !congelacaoSelecionada && urgente !== opcao.valor ? 'hover:bg-gray-50' : '',
                ]"
                class="relative flex-1 rounded-md border px-4 py-2 text-center text-sm font-bold transition has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-paper-primary"
              >
                <input v-model="urgente" type="radio" name="urgente" :value="opcao.valor" :disabled="congelacaoSelecionada" class="sr-only" />
                {{ opcao.rotulo }}
              </label>
            </div>
            <p v-if="tentouConfirmar && erroUrgente" class="mt-1 text-sm text-paper-danger-strong">{{ erroUrgente }}</p>
          </fieldset>

          <!-- Um bloco por tipo de exame: cada tipo é recebido como uma unidade -->
          <section
            v-for="grupo in recepcao.exames"
            :key="grupo.id"
            :class="[
              estado[grupo.id].receber ? 'bg-white' : 'border-dashed border-gray-300 bg-gray-50',
              grupo.id === recepcao.grupoSelecionadoId
                ? 'border-paper-primary ring-2 ring-paper-primary/25'
                : estado[grupo.id].receber
                  ? 'border-gray-200'
                  : '',
            ]"
            class="rounded-lg border p-3"
            :aria-label="`Tipo de exame ${grupo.tipoExameSugerido}`"
          >
            <header class="flex items-start gap-2">
              <label v-if="multiplos" class="flex cursor-pointer items-start gap-2" :for="`receber-${grupo.tipoExameSugerido}`">
                <input
                  :id="`receber-${grupo.tipoExameSugerido}`"
                  v-model="estado[grupo.id].receber"
                  type="checkbox"
                  class="focus-ring mt-0.5 h-5 w-5 rounded"
                  :aria-label="`Receber agora ${TIPOS_EXAME[grupo.tipoExameSugerido].nome}`"
                />
              </label>
              <div class="min-w-0">
                <p class="flex flex-wrap items-center gap-1.5">
                  <Badge :variant="grupo.tipoExameSugerido === 'CO' ? 'danger' : 'primary'" size="sm">{{ grupo.tipoExameSugerido }}</Badge>
                  <span class="font-bold text-gray-900">{{ TIPOS_EXAME[grupo.tipoExameSugerido].nome }}</span>
                  <Badge v-if="grupo.id === recepcao.grupoSelecionadoId" variant="info" size="sm">
                    Amostra bipada
                  </Badge>
                </p>
                <p class="mt-0.5 text-xs text-gray-600">
                  {{ rotuloAmostrasCapitalizado(grupo.amostras) }} · {{ grupo.siglaExame }}
                </p>
              </div>
              <Button
                v-if="authStore.hasPermission('casos:cancelar')"
                type="button"
                variant="danger"
                class="ml-auto shrink-0"
                :disabled="salvando || cancelandoId !== null"
                @click="abrirCancelamento(grupo.id)"
              >Cancelar exame</Button>
            </header>

            <div v-if="cancelandoId === grupo.id" class="mt-3 rounded-md border border-paper-danger/30 bg-paper-danger-soft p-3" role="dialog" aria-modal="true" :aria-label="`Cancelar exame ${grupo.tipoExameSugerido}`">
              <label :for="`motivo-cancelamento-${grupo.id}`" class="form-label">Motivo do cancelamento <span class="text-paper-danger">*</span></label>
              <textarea :id="`motivo-cancelamento-${grupo.id}`" v-model="motivoCancelamento" rows="3" class="form-control" required maxlength="1000" />
              <div class="mt-2 flex justify-end gap-2">
                <Button type="button" variant="secondary" :disabled="cancelando" @click="fecharCancelamento">Voltar</Button>
                <Button type="button" variant="danger" :loading="cancelando" :disabled="!motivoCancelamento.trim()" @click="confirmarCancelamento(grupo.id)">Confirmar cancelamento</Button>
              </div>
            </div>

            <div v-if="estado[grupo.id].receber" class="mt-3 space-y-3">
              <!-- Caso principal -->
              <template v-if="grupo.tipoExameSugerido !== 'IHQ'">
                <div class="form-group mb-0">
                  <label :for="idCampo(grupo, 'procedimento')" class="form-label">Procedimento <span class="text-paper-danger">*</span></label>
                  <SelectBusca
                    :id="idCampo(grupo, 'procedimento')"
                    v-model="estado[grupo.id].procedimento"
                    :opcoes="opcoesProcedimento"
                    rotulo="Procedimento"
                    :invalid="!!erro(grupo, 'procedimento')"
                  />
                  <p v-if="erro(grupo, 'procedimento')" class="mt-1 text-sm text-paper-danger-strong">{{ erro(grupo, 'procedimento') }}</p>
                </div>
              </template>

              <!-- IHQ: caso de origem -->
              <template v-else>
                <fieldset v-if="principalSelecionado" class="space-y-1.5">
                  <legend class="form-label">Caso de origem da IHQ <span class="text-paper-danger">*</span></legend>
                  <label class="flex cursor-pointer items-start gap-2 text-sm">
                    <input v-model="estado[grupo.id].origemModo" type="radio" :name="`origem-${grupo.id}`" value="CONFERENCIA" class="mt-0.5" />
                    <span>Caso {{ principalSelecionado.tipoExameSugerido }} gerado nesta conferência</span>
                  </label>
                  <label class="flex cursor-pointer items-start gap-2 text-sm">
                    <input v-model="estado[grupo.id].origemModo" type="radio" :name="`origem-${grupo.id}`" value="EXISTENTE" class="mt-0.5" />
                    <span>Caso já existente</span>
                  </label>
                </fieldset>
                <template v-if="!principalSelecionado || estado[grupo.id].origemModo === 'EXISTENTE'">
                  <CasoOrigemIhq
                    :id="idCampo(grupo, 'casoOrigem')"
                    v-model="estado[grupo.id].casoOrigem"
                    :erro="erro(grupo, 'casoOrigem') || undefined"
                  />
                  <p
                    v-if="casoSugerido && estado[grupo.id].casoOrigem?.numeroInterno === casoSugerido"
                    class="-mt-1 text-xs font-semibold text-paper-info-strong"
                  >
                    Sugerido: caso {{ casoSugerido }}, recebido a partir da mesma solicitação AGHU. Use "Trocar caso" se não for o correto.
                  </p>
                  <div v-if="divergente(grupo)">
                    <Alert variant="warning" title="Prontuário divergente">
                      A solicitação é do prontuário <strong>{{ grupo.prontuario || NAO_INFORMADO }}</strong> e o caso
                      {{ estado[grupo.id].casoOrigem?.numeroInterno }} é do prontuário
                      <strong>{{ estado[grupo.id].casoOrigem?.prontuario }}</strong>. Confira a requisição antes de vincular.
                    </Alert>
                    <label :for="idCampo(grupo, 'divergencia')" class="mt-3 flex cursor-pointer items-start gap-3 text-sm font-semibold text-gray-800">
                      <input
                        :id="idCampo(grupo, 'divergencia')"
                        v-model="estado[grupo.id].divergenciaConfirmada"
                        type="checkbox"
                        class="focus-ring mt-0.5 h-5 w-5 rounded"
                      />
                      Confirmo o vínculo da IHQ apesar do prontuário divergente.
                    </label>
                    <p v-if="erro(grupo, 'divergencia')" class="mt-1 text-sm text-paper-danger-strong">{{ erro(grupo, 'divergencia') }}</p>
                  </div>
                </template>
              </template>
            </div>
          </section>
          <p v-if="tentouConfirmar && nenhumSelecionado" class="text-sm text-paper-danger-strong">
            Marque ao menos um tipo de exame para receber agora.
          </p>

          <div class="form-group mb-0">
            <label for="campo-observacoes" class="form-label">Observações</label>
            <textarea id="campo-observacoes" v-model="observacoes" rows="2" class="form-control resize-none"></textarea>
          </div>

          <div class="flex flex-col gap-2 pt-2">
            <Button type="submit" :loading="salvando" :disabled="ncAberta" title="Atalho: Ctrl+Enter">
              <CheckCircleIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Confirmar conferência
            </Button>
            <Button variant="danger" :disabled="salvando" aria-haspopup="dialog" @click="ncAberta = true">
              <ExclamationTriangleIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Registrar não conformidade
            </Button>
          </div>
        </form>

        <NaoConformidadeModal
          :show="ncAberta"
          :contexto="{ tipo: 'SOLICITACAO', solicitacaoIds: recepcao.exames.map((e) => e.id) }"
          :exames-devolviveis="recepcao.exames"
          @close="ncAberta = false"
          @registrado="aposDevolucao"
        />

        <div class="mt-4 flex justify-center">
          <button
            type="button"
            class="focus-ring rounded px-2 py-1 text-sm font-semibold text-paper-primary-strong underline-offset-2 transition hover:underline active:opacity-70"
            @click="recepcao.reiniciar()"
          >
            Ler outra etiqueta
          </button>
        </div>
      </Card>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useToast } from 'vue-toastification';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import Alert from '../../Alert.vue';
import Badge from '../../Badge.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import SelectBusca from '../../SelectBusca.vue';
import DadosSolicitacao from '../DadosSolicitacao.vue';
import NaoConformidadeModal from '../NaoConformidadeModal.vue';
import CasoOrigemIhq from './CasoOrigemIhq.vue';
import { NAO_INFORMADO, PROCEDIMENTOS, TIPOS_EXAME } from '../../../constants/ap';
import { rotuloNumerosAmostras } from '../../../helpers/aghu';
import { mensagemDeErro } from '../../../services/ap';
import { useCasosStore } from '../../../stores/casos';
import { useRecepcaoStore, type EntradaConferencia } from '../../../stores/recepcao';
import { useAuthStore } from '../../../stores/auth';
import type { CasoElegivelIhq, SolicitacaoAghu, TipoCasoPrincipal } from '../../../types/ap';

/** `devolvido`: a não conformidade foi registrada e a recepção deve voltar ao passo 1. */
const emit = defineEmits<{ (e: 'devolvido'): void }>();

type CampoGrupo = 'procedimento' | 'casoOrigem' | 'divergencia';

/** Estado dos campos de um tipo de exame na conferência. */
interface EstadoGrupo {
  receber: boolean;
  procedimento: string;
  origemModo: 'CONFERENCIA' | 'EXISTENTE';
  casoOrigem: CasoElegivelIhq | null;
  divergenciaConfirmada: boolean;
}

const toast = useToast();
const recepcao = useRecepcaoStore();
const casosStore = useCasosStore();
const authStore = useAuthStore();

/** Modal de não conformidade e devolução aberto. */
const ncAberta = ref(false);

/** Devolução registrada: fecha o modal e a recepção volta ao passo 1. */
const aposDevolucao = () => {
  ncAberta.value = false;
  emit('devolvido');
};
const salvando = ref(false);
const tentouConfirmar = ref(false);
const resumo = ref<HTMLElement | null>(null);
const observacoes = ref('');
const cancelandoId = ref<string | null>(null);
const motivoCancelamento = ref('');
const cancelando = ref(false);

const abrirCancelamento = (id: string) => {
  cancelandoId.value = id;
  motivoCancelamento.value = '';
};
const fecharCancelamento = () => {
  cancelandoId.value = null;
  motivoCancelamento.value = '';
};
const confirmarCancelamento = async (id: string) => {
  const motivo = motivoCancelamento.value.trim();
  if (!motivo || cancelando.value) return;
  cancelando.value = true;
  try {
    const todosCancelados = await recepcao.cancelarExame(id, motivo);
    fecharCancelamento();
    if (todosCancelados) {
      toast.success('Todos os exames pendentes da solicitação foram cancelados.');
      emit('devolvido');
    } else {
      toast.success('Exame cancelado. Os demais exames continuam disponíveis para recebimento.');
    }
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível cancelar o exame.'));
  } finally {
    cancelando.value = false;
  }
};

const opcoesProcedimento = PROCEDIMENTOS.map((p) => ({ valor: p, rotulo: p }));
const opcoesUrgencia = [
  { valor: 'SIM', rotulo: 'Sim', ativo: 'border-paper-danger bg-paper-danger-soft text-paper-danger-strong' },
  { valor: 'NAO', rotulo: 'Não', ativo: 'border-paper-success bg-paper-success-soft text-paper-success-strong' },
] as const;
const rotulosCampo: Record<CampoGrupo, string> = {
  procedimento: 'Procedimento',
  casoOrigem: 'Caso de origem da IHQ',
  divergencia: 'Confirmação do prontuário divergente',
};

const ehCongelacao = (grupo: SolicitacaoAghu) => grupo.tipoExameSugerido === 'CO';
const rotuloAmostrasCapitalizado = (amostras: SolicitacaoAghu['amostras']) =>
  rotuloNumerosAmostras(amostras).replace(/^a/, 'A');

/** Quando a bipagem identificou uma amostra específica em solicitação mista, pré-marca apenas seu grupo. */
const temFiltroAmostra = computed(
  () =>
    !!recepcao.grupoSelecionadoId &&
    recepcao.exames.length > 1 &&
    recepcao.exames.some((g) => g.id === recepcao.grupoSelecionadoId),
);
const multiplos = computed(() => recepcao.exames.length > 1);

/** Estado inicial por tipo: se houver amostra bipada em solicitação mista, pré-marca só o grupo correspondente. */
const estado = reactive<Record<string, EstadoGrupo>>(
  Object.fromEntries(
    recepcao.exames.map((g) => [
      g.id,
      {
        receber: !temFiltroAmostra.value || g.id === recepcao.grupoSelecionadoId,
        procedimento: '',
        origemModo: 'CONFERENCIA',
        casoOrigem: null,
        divergenciaConfirmada: false,
      } satisfies EstadoGrupo,
    ]),
  ),
);

const selecionados = computed(() => recepcao.exames.filter((g) => estado[g.id].receber));
const nenhumSelecionado = computed(() => selecionados.value.length === 0);

/** Tipos principais (que geram caso) marcados: a urgência só se aplica a eles. */
const principaisSelecionados = computed(() => selecionados.value.filter((g) => g.tipoExameSugerido !== 'IHQ'));

/**
 * Urgência da solicitação: uma só para todos os casos gerados nesta conferência.
 * Com Congelação marcada para receber, fica em Sim e não pode ser alterada.
 */
const urgente = ref<'SIM' | 'NAO' | undefined>(undefined);
const congelacaoSelecionada = computed(() => principaisSelecionados.value.some(ehCongelacao));
watch(
  congelacaoSelecionada,
  (comCongelacao, antes) => {
    if (comCongelacao) urgente.value = 'SIM';
    else if (antes) urgente.value = undefined;
  },
  { immediate: true },
);
const erroUrgente = computed(() => (principaisSelecionados.value.length && !urgente.value ? 'Escolha Sim ou Não.' : ''));

/** Tipo principal (não IHQ) recebido nesta conferência, que pode ser o caso de origem da IHQ. */
const principalSelecionado = computed(
  () => selecionados.value.find((g) => g.tipoExameSugerido === 'HP') ?? selecionados.value.find((g) => g.tipoExameSugerido !== 'IHQ' && g.tipoExameSugerido !== 'CO') ?? selecionados.value.find((g) => g.tipoExameSugerido !== 'IHQ'),
);

/** Grupos da solicitação já recebidos ou devolvidos antes (informativo). */
const jaTratados = computed(() => recepcao.outrosExames.filter((e) => e.situacaoRecepcao !== 'AGUARDANDO_RECEBIMENTO'));

/** Caso principal já recebido a partir de outro tipo da mesma solicitação: sugerido para a IHQ. */
const casoSugerido = computed(
  () => recepcao.outrosExames.find((e) => e.situacaoRecepcao === 'RECEBIDA' && e.casoNumero)?.casoNumero ?? null,
);

watch(
  casoSugerido,
  async (numero) => {
    if (!numero) return;
    const ihqs = recepcao.exames.filter((g) => g.tipoExameSugerido === 'IHQ' && !estado[g.id].casoOrigem);
    if (ihqs.length === 0) return;
    try {
      const caso = (await casosStore.buscarElegiveisIhq(numero)).find((c) => c.numeroInterno === numero && c.elegivel);
      if (!caso) return;
      for (const g of ihqs) {
        if (!estado[g.id].casoOrigem) estado[g.id].casoOrigem = caso;
        if (!principalSelecionado.value) estado[g.id].origemModo = 'EXISTENTE';
      }
    } catch (e) {
      console.error('Falha ao sugerir o caso de origem da IHQ.', e);
    }
  },
  { immediate: true },
);

/** Troca do caso de origem desfaz a confirmação de divergência. */
watch(
  () => recepcao.exames.map((g) => estado[g.id].casoOrigem?.numeroInterno),
  () => recepcao.exames.forEach((g) => (estado[g.id].divergenciaConfirmada = false)),
);

const idCampo = (grupo: SolicitacaoAghu, campo: CampoGrupo) => `campo-${grupo.tipoExameSugerido.toLowerCase()}-${campo}`;

const usaCasoExistente = (grupo: SolicitacaoAghu) => !principalSelecionado.value || estado[grupo.id].origemModo === 'EXISTENTE';

const divergente = (grupo: SolicitacaoAghu) => {
  const caso = estado[grupo.id].casoOrigem;
  return usaCasoExistente(grupo) && !!caso && caso.prontuario !== grupo.prontuario;
};

/** Erros de validação por campo de cada tipo selecionado. */
const errosPorCampo = computed(() => {
  const erros: { grupo: SolicitacaoAghu; campo: CampoGrupo; mensagem: string }[] = [];
  for (const grupo of selecionados.value) {
    const e = estado[grupo.id];
    if (grupo.tipoExameSugerido === 'IHQ') {
      if (usaCasoExistente(grupo)) {
        if (!e.casoOrigem) erros.push({ grupo, campo: 'casoOrigem', mensagem: 'Selecione o caso de origem.' });
        else if (divergente(grupo) && !e.divergenciaConfirmada)
          erros.push({ grupo, campo: 'divergencia', mensagem: 'Confirme o vínculo apesar do prontuário divergente.' });
      }
      continue;
    }
    if (!e.procedimento) erros.push({ grupo, campo: 'procedimento', mensagem: 'Selecione o procedimento.' });
  }
  return erros;
});

const erro = (grupo: SolicitacaoAghu, campo: CampoGrupo): string =>
  tentouConfirmar.value ? (errosPorCampo.value.find((x) => x.grupo.id === grupo.id && x.campo === campo)?.mensagem ?? '') : '';

const listaErros = computed(() => [
  ...(erroUrgente.value ? [{ id: 'campo-urgente', rotulo: 'Urgente?', mensagem: erroUrgente.value }] : []),
  ...errosPorCampo.value.map((x) => ({
    id: idCampo(x.grupo, x.campo),
    rotulo: multiplos.value ? `${x.grupo.tipoExameSugerido} · ${rotulosCampo[x.campo]}` : rotulosCampo[x.campo],
    mensagem: x.mensagem,
  })),
]);

/** Leva o foco ao campo indicado no resumo de erros. */
const focarCampo = (id: string) => {
  const el = document.getElementById(id);
  el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  const alvo = el?.matches('input, select, textarea, button') ? el : el?.querySelector<HTMLElement>('input, select, textarea, button') ?? el;
  alvo?.focus({ preventScroll: true });
};

/** Monta as entradas dos tipos marcados para a confirmação. */
const montarEntradas = (): EntradaConferencia[] => {
  const obs = observacoes.value.trim() || undefined;
  return selecionados.value.map((grupo): EntradaConferencia => {
    const e = estado[grupo.id];
    if (grupo.tipoExameSugerido === 'IHQ') {
      const existente = usaCasoExistente(grupo);
      return {
        tipo: 'IHQ',
        usarCasoDaConferencia: !existente,
        dados: {
          solicitacaoId: grupo.id,
          casoOrigemNumero: existente ? e.casoOrigem?.numeroInterno : undefined,
          divergenciaConfirmada: e.divergenciaConfirmada,
          observacoes: obs,
        },
      };
    }
    return {
      tipo: 'CASO',
      dados: {
        solicitacaoId: grupo.id,
        tipoExame: grupo.tipoExameSugerido as TipoCasoPrincipal,
        urgente: urgente.value === 'SIM',
        procedimento: e.procedimento,
        observacoes: obs,
      },
    };
  });
};

const enviar = async () => {
  if (ncAberta.value || salvando.value) return;
  tentouConfirmar.value = true;
  if (nenhumSelecionado.value || listaErros.value.length > 0) {
    if (listaErros.value.length > 0) {
      toast.warning(`Faltam ${listaErros.value.length} campo(s) obrigatório(s) para confirmar a conferência.`);
      await nextTick();
      resumo.value?.focus();
    }
    return;
  }
  salvando.value = true;
  try {
    await recepcao.confirmarConferencia(montarEntradas());
    const n = recepcao.resultados.length;
    toast.success(n === 1 ? 'Conferência confirmada.' : `Conferência confirmada: ${n} registros gerados.`);
  } catch (e) {
    toast.error(mensagemDeErro(e, 'Não foi possível confirmar a conferência.'));
  } finally {
    salvando.value = false;
  }
};

/** Ctrl+Enter (ou Cmd+Enter) confirma a conferência. */
const aoTeclar = (evento: KeyboardEvent) => {
  if (evento.key === 'Enter' && (evento.ctrlKey || evento.metaKey)) {
    evento.preventDefault();
    void enviar();
  }
};
onMounted(() => document.addEventListener('keydown', aoTeclar));
onUnmounted(() => document.removeEventListener('keydown', aoTeclar));
</script>
