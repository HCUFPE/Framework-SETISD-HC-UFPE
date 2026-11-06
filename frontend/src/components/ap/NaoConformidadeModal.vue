<template>
  <Modal :show="show" size="xl" :close-on-backdrop="false" @close="fechar">
    <template #header>
      <span class="flex items-center gap-2">
        <ExclamationTriangleIcon class="h-6 w-6 text-paper-danger" aria-hidden="true" />
        Não conformidade e devolução
        <span class="ml-2 text-sm font-semibold text-gray-500">Passo {{ passo }} de 2</span>
      </span>
    </template>

    <!-- Contexto automático -->
    <dl class="mb-5 grid grid-cols-2 gap-x-4 gap-y-2 rounded-lg bg-gray-50 p-4 text-sm sm:grid-cols-5">
      <div>
        <dt class="text-xs font-bold uppercase text-gray-500">Setor</dt>
        <dd class="font-semibold text-gray-800">{{ SETOR_RECEPCAO }}</dd>
      </div>
      <div>
        <dt class="text-xs font-bold uppercase text-gray-500">Etapa</dt>
        <dd class="font-semibold text-gray-800">{{ etapaRotulo }}</dd>
      </div>
      <div>
        <dt class="text-xs font-bold uppercase text-gray-500">Caso</dt>
        <dd class="font-semibold text-gray-800">{{ caso?.numeroInterno ?? '—' }}</dd>
      </div>
      <div>
        <dt class="text-xs font-bold uppercase text-gray-500">Data/hora</dt>
        <dd class="font-semibold text-gray-800">{{ formatarDataHora(abertoEm) }}</dd>
      </div>
      <div>
        <dt class="text-xs font-bold uppercase text-gray-500">Profissional</dt>
        <dd class="font-semibold text-gray-800">{{ responsavel.nome }}</dd>
      </div>
    </dl>

    <!-- Dados da solicitação (somente leitura) -->
    <div v-if="dadosSolicitacao" class="mb-5 grid gap-3 sm:grid-cols-2">
      <div v-for="campo in cartoesSolicitacao" :key="campo.rotulo" class="rounded-md border border-paper-info/30 bg-paper-info-soft px-3 py-2">
        <p class="text-[11px] font-bold uppercase text-paper-info-strong">{{ campo.rotulo }}</p>
        <p class="text-sm font-semibold text-gray-800">{{ campo.valor }}</p>
      </div>
    </div>

    <!-- Passo 1: dados da não conformidade -->
    <form v-if="passo === 1" id="nc-passo-1" class="space-y-4" novalidate @submit.prevent="avancar">
      <div v-if="semEtiqueta" class="form-group mb-0">
        <label for="nc-unidade" class="form-label">Unidade de origem <span class="text-paper-danger">*</span></label>
        <select id="nc-unidade" v-model="unidadeOrigem" v-bind="unidadeAttrs" class="form-control" :aria-invalid="!!erros1.unidadeOrigem">
          <option value="">Selecione</option>
          <option v-for="unidade in UNIDADES_ORIGEM" :key="unidade" :value="unidade">{{ unidade }}</option>
        </select>
        <p v-if="erros1.unidadeOrigem" class="mt-1 text-sm text-paper-danger-strong">{{ erros1.unidadeOrigem }}</p>
      </div>

      <div class="form-group mb-0">
        <label for="nc-tipo" class="form-label">Tipo de inconformidade <span class="text-paper-danger">*</span></label>
        <select id="nc-tipo" v-model="tipo" v-bind="tipoAttrs" class="form-control" :aria-invalid="!!erros1.tipo">
          <option value="">Selecione</option>
          <option v-for="(rotulo, codigo) in TIPOS_NAO_CONFORMIDADE" :key="codigo" :value="codigo">{{ rotulo }}</option>
        </select>
        <p v-if="erros1.tipo" class="mt-1 text-sm text-paper-danger-strong">{{ erros1.tipo }}</p>
      </div>

      <div class="form-group mb-0">
        <label for="nc-descricao" class="form-label">Detalhamento <span class="text-paper-danger">*</span></label>
        <textarea
          id="nc-descricao"
          v-model="descricao"
          v-bind="descricaoAttrs"
          rows="3"
          class="form-control"
          placeholder="O que foi encontrado na amostra?"
          :aria-invalid="!!erros1.descricao"
        ></textarea>
        <p v-if="erros1.descricao" class="mt-1 text-sm text-paper-danger-strong">{{ erros1.descricao }}</p>
      </div>
    </form>

    <!-- Passo 2: devolução -->
    <form v-else id="nc-passo-2" class="space-y-4" novalidate @submit.prevent="registrar">
      <Alert variant="danger" :title="TIPOS_NAO_CONFORMIDADE[valores1.tipo as TipoNaoConformidadeCodigo] ?? ''">
        {{ valores1.descricao }}
      </Alert>
      <p class="text-sm text-gray-600">
        Toda não conformidade gera a devolução do material à unidade de origem
        <strong>{{ unidadeExibida }}</strong>.
      </p>

      <div class="grid gap-4 sm:grid-cols-2">
        <div class="form-group mb-0">
          <label for="nc-devolvido-por" class="form-label">Quem devolveu</label>
          <input id="nc-devolvido-por" :value="responsavel.nome" type="text" class="form-control bg-gray-100" readonly />
        </div>

        <fieldset>
          <legend class="form-label">Nova amostra solicitada? <span class="text-paper-danger">*</span></legend>
          <div class="flex gap-2" role="radiogroup">
            <label
              v-for="opcao in opcoesSimNao"
              :key="opcao.valor"
              :class="novaAmostra === opcao.valor ? 'border-paper-primary bg-paper-primary-soft text-paper-primary-strong' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'"
              class="relative has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-paper-primary inline-flex cursor-pointer items-center gap-2 rounded-md border px-4 py-2 text-sm font-semibold transition active:bg-gray-100"
            >
              <input v-model="novaAmostra" type="radio" name="nova-amostra" :value="opcao.valor" class="sr-only" />
              {{ opcao.rotulo }}
            </label>
          </div>
          <p v-if="erros2.novaAmostra" class="mt-1 text-sm text-paper-danger-strong">{{ erros2.novaAmostra }}</p>
        </fieldset>
      </div>
    </form>

    <template #footer>
      <template v-if="passo === 1">
        <Button variant="secondary" @click="fechar">Cancelar</Button>
        <Button type="submit" form="nc-passo-1" variant="danger">Avançar para a devolução</Button>
      </template>
      <template v-else>
        <Button variant="secondary" :disabled="salvando" @click="passo = 1">Voltar</Button>
        <Button type="submit" form="nc-passo-2" variant="danger" :loading="salvando">
          <ArrowUturnLeftIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Registrar devolução
        </Button>
      </template>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as z from 'zod';
import { useToast } from 'vue-toastification';
import { ArrowUturnLeftIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import Modal from '../Modal.vue';
import Button from '../Button.vue';
import Alert from '../Alert.vue';
import { ETAPAS, ORIGENS, SETOR_RECEPCAO, TIPOS_NAO_CONFORMIDADE, UNIDADES_ORIGEM } from '../../constants/ap';
import { formatarDataHora } from '../../helpers/formato';
import { useResponsavel } from '../../composables/useResponsavel';
import { mensagemDeErro } from '../../services/ap';
import { useDevolucoesStore } from '../../stores/devolucoes';
import type {
  CasoAp,
  ContextoNaoConformidade,
  DevolucaoDetalhada,
  SolicitacaoAghu,
  TipoNaoConformidadeCodigo,
} from '../../types/ap';

const props = defineProps<{
  show: boolean;
  contexto: ContextoNaoConformidade | null;
  /** Solicitação exibida quando o registro parte da conferência. */
  solicitacao?: SolicitacaoAghu | null;
  /** Caso exibido quando o registro parte do detalhe. */
  caso?: CasoAp | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'registrado', devolucao: DevolucaoDetalhada): void;
}>();

const toast = useToast();
const responsavel = useResponsavel();
const devolucoesStore = useDevolucoesStore();

const passo = ref<1 | 2>(1);
const salvando = ref(false);
const abertoEm = ref(new Date().toISOString());

const semEtiqueta = computed(() => props.contexto?.tipo === 'SEM_ETIQUETA');
const dadosSolicitacao = computed(() => props.caso?.solicitacao ?? props.solicitacao ?? null);

const etapaRotulo = computed(() => {
  if (!props.contexto) return '—';
  if (props.contexto.tipo === 'SEM_ETIQUETA') return 'Recepção (leitura)';
  if (props.contexto.tipo === 'SOLICITACAO') return 'Recepção (conferência)';
  return props.caso?.etapaAtual ? ETAPAS[props.caso.etapaAtual] : '—';
});

const cartoesSolicitacao = computed(() => {
  const s = dadosSolicitacao.value;
  if (!s) return [];
  return [
    { rotulo: 'Solicitação AGHU', valor: s.codigoSolicitacao },
    { rotulo: 'Exame', valor: s.nomeExame },
    { rotulo: 'Origem', valor: `${s.unidade} · ${ORIGENS[s.origem]}` },
    { rotulo: 'Médico / especialidade', valor: `${s.nomeSolicitante} · ${s.especialidade}` },
  ];
});

const opcoesSimNao = [
  { valor: 'SIM', rotulo: 'Sim' },
  { valor: 'NAO', rotulo: 'Não' },
] as const;

// Passo 1 ---------------------------------------------------------------
const schema1 = computed(() =>
  toTypedSchema(
    z.object({
      unidadeOrigem: semEtiqueta.value
        ? z.string({ required_error: 'Selecione a unidade de origem.' }).min(1, 'Selecione a unidade de origem.')
        : z.string().optional(),
      tipo: z.string({ required_error: 'Selecione o tipo de inconformidade.' }).min(1, 'Selecione o tipo de inconformidade.'),
      descricao: z
        .string({ required_error: 'Descreva o que foi encontrado.' })
        .trim()
        .min(1, 'Descreva o que foi encontrado.'),
    }),
  ),
);

const {
  defineField: defineField1,
  handleSubmit: handleSubmit1,
  errors: erros1,
  values: valores1,
  resetForm: resetForm1,
} = useForm({ validationSchema: schema1 });

const [unidadeOrigem, unidadeAttrs] = defineField1('unidadeOrigem');
const [tipo, tipoAttrs] = defineField1('tipo');
const [descricao, descricaoAttrs] = defineField1('descricao');

const unidadeExibida = computed(() => valores1.unidadeOrigem || dadosSolicitacao.value?.unidade || '—');

const avancar = handleSubmit1(() => {
  passo.value = 2;
});

// Passo 2 ---------------------------------------------------------------
const schema2 = toTypedSchema(
  z.object({
    novaAmostra: z.enum(['SIM', 'NAO'], { required_error: 'Escolha Sim ou Não.', invalid_type_error: 'Escolha Sim ou Não.' }),
  }),
);

const {
  defineField: defineField2,
  handleSubmit: handleSubmit2,
  errors: erros2,
  resetForm: resetForm2,
} = useForm({ validationSchema: schema2 });

const [novaAmostra] = defineField2('novaAmostra');

const registrar = handleSubmit2(async (valores2) => {
  if (!props.contexto) return;
  salvando.value = true;
  try {
    const devolucao = await devolucoesStore.registrar({
      contexto: props.contexto,
      tipo: valores1.tipo as TipoNaoConformidadeCodigo,
      descricao: valores1.descricao ?? '',
      unidadeOrigem: valores1.unidadeOrigem,
      novaAmostraSolicitada: valores2.novaAmostra === 'SIM',
    });
    toast.success('Não conformidade e devolução registradas. O material saiu das filas ativas.');
    emit('registrado', devolucao);
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível registrar a não conformidade.'));
  } finally {
    salvando.value = false;
  }
});

const fechar = () => {
  if (!salvando.value) emit('close');
};

/** Reinicia o formulário a cada abertura. */
watch(
  () => props.show,
  (aberto) => {
    if (!aberto) return;
    passo.value = 1;
    abertoEm.value = new Date().toISOString();
    resetForm1({
      values: {
        unidadeOrigem: '',
        tipo: props.contexto?.tipo === 'SEM_ETIQUETA' ? 'SEM_ETIQUETA_AGHU' : '',
        descricao: '',
      },
    });
    resetForm2({ values: { novaAmostra: undefined } });
  },
  { immediate: true },
);
</script>
