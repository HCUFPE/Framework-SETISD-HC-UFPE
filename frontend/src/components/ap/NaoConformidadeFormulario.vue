<template>
  <!--
    Formulário de não conformidade e devolução. Usado dentro do `NaoConformidadeModal`
    (título no cabeçalho e ações no rodapé do modal, ligadas a este formulário pelo `idFormulario`).
  -->
  <section class="text-left" :aria-label="'Não conformidade e devolução'">
    <p class="text-xs text-gray-600">
      {{ etapaRotulo }} · {{ responsavel.nome }} · toda não conformidade gera a devolução do material à unidade de origem.
    </p>

    <form :id="idFormulario" class="mt-3 space-y-3" novalidate @submit.prevent="registrar">
      <div v-if="semEtiqueta" class="form-group mb-0">
        <label :for="`${idBase}-unidade`" class="form-label">Unidade de origem <span class="text-paper-danger">*</span></label>
        <SelectBusca
          :id="`${idBase}-unidade`"
          v-model="unidadeOrigem"
          :opcoes="opcoesUnidade"
          rotulo="Unidade de origem"
          :invalid="!!errors.unidadeOrigem"
        />
        <p v-if="errors.unidadeOrigem" class="mt-1 text-sm text-paper-danger-strong">{{ errors.unidadeOrigem }}</p>
      </div>

      <!-- Conferência com mais de um tipo de exame: cada tipo é devolvido como uma unidade -->
      <fieldset v-if="examesDevolviveis.length > 1">
        <legend class="form-label">Exames devolvidos <span class="text-paper-danger">*</span></legend>
        <div class="space-y-1.5">
          <label
            v-for="exame in examesDevolviveis"
            :key="exame.id"
            :class="examesSelecionados.includes(exame.id) ? 'border-paper-danger bg-white' : 'border-gray-300 bg-white/60'"
            class="flex cursor-pointer items-start gap-2 rounded-md border px-3 py-2 text-sm transition hover:bg-white active:bg-gray-50"
          >
            <input v-model="examesSelecionados" type="checkbox" :value="exame.id" class="focus-ring mt-0.5 h-4 w-4 rounded" />
            <span>
              <strong>{{ exame.tipoExameSugerido }} · {{ TIPOS_EXAME[exame.tipoExameSugerido].nome }}</strong>
              <span class="block text-xs text-gray-600">{{ rotuloNumerosAmostras(exame.amostras) }} · {{ exame.siglaExame }}</span>
            </span>
          </label>
        </div>
        <p v-if="erroExames" class="mt-1 text-sm text-paper-danger-strong">{{ erroExames }}</p>
      </fieldset>

      <div class="form-group mb-0">
        <label :for="`${idBase}-tipo`" class="form-label">Não conformidade <span class="text-paper-danger">*</span></label>
        <SelectBusca
          :id="`${idBase}-tipo`"
          v-model="tipo"
          :opcoes="opcoesTipo"
          rotulo="Não conformidade"
          :invalid="!!errors.tipo"
        />
        <p v-if="errors.tipo" class="mt-1 text-sm text-paper-danger-strong">{{ errors.tipo }}</p>
        <p v-if="solucao" class="mt-2 text-sm text-gray-700">
          <strong>Solução:</strong> <em>{{ solucao }}</em>
        </p>
      </div>

      <div v-if="tipo === 'OUTROS'" class="form-group mb-0">
        <label :for="`${idBase}-outros`" class="form-label">Descreva a não conformidade <span class="text-paper-danger">*</span></label>
        <input
          :id="`${idBase}-outros`"
          v-model="descricao"
          v-bind="descricaoAttrs"
          type="text"
          class="form-control"
          :aria-invalid="!!errors.descricao"
        />
        <p v-if="errors.descricao" class="mt-1 text-sm text-paper-danger-strong">{{ errors.descricao }}</p>
      </div>

      <div class="form-group mb-0">
        <label :for="`${idBase}-observacao`" class="form-label">Observação</label>
        <textarea :id="`${idBase}-observacao`" v-model="observacao" rows="3" class="form-control resize-none"></textarea>
      </div>

      <fieldset>
        <legend class="form-label">Nova amostra solicitada? <span class="text-paper-danger">*</span></legend>
        <div class="flex gap-2" role="radiogroup">
          <label
            v-for="opcao in opcoesSimNao"
            :key="opcao.valor"
            :class="novaAmostra === opcao.valor ? 'border-paper-primary bg-paper-primary-soft text-paper-primary-strong' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'"
            class="relative inline-flex cursor-pointer items-center gap-2 rounded-md border px-4 py-2 text-sm font-semibold transition has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-paper-primary active:bg-gray-100"
          >
            <input v-model="novaAmostra" type="radio" :name="`${idBase}-nova-amostra`" :value="opcao.valor" class="sr-only" />
            {{ opcao.rotulo }}
          </label>
        </div>
        <p v-if="errors.novaAmostra" class="mt-1 text-sm text-paper-danger-strong">{{ errors.novaAmostra }}</p>
      </fieldset>
    </form>
  </section>
</template>

<script lang="ts">
/** Contador para ids únicos entre instâncias do formulário. */
let instancias = 0;
</script>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as z from 'zod';
import { useToast } from 'vue-toastification';
import SelectBusca from '../SelectBusca.vue';
import { rotuloNumerosAmostras } from '../../helpers/aghu';
import {
  ETAPAS,
  ORDEM_TIPOS_NAO_CONFORMIDADE,
  SOLUCOES_NAO_CONFORMIDADE,
  TIPOS_EXAME,
  TIPOS_NAO_CONFORMIDADE,
  UNIDADES_AGHU,
} from '../../constants/ap';
import { useResponsavel } from '../../composables/useResponsavel';
import { mensagemDeErro } from '../../services/ap';
import { useDevolucoesStore } from '../../stores/devolucoes';
import type {
  ContextoNaoConformidade,
  DevolucaoDetalhada,
  EtapaCodigo,
  SolicitacaoAghu,
  TipoNaoConformidadeCodigo,
} from '../../types/ap';

const props = withDefaults(
  defineProps<{
    contexto: ContextoNaoConformidade;
    /** Etapa atual do caso, quando o registro parte do detalhe. */
    etapaCaso?: EtapaCodigo | null;
    /** Conferência: tipos de exame pendentes que podem ser devolvidos (escolha quando há mais de um). */
    examesDevolviveis?: SolicitacaoAghu[];
    /** Id do <form>, para o botão de envio ficar fora dele (rodapé do modal). */
    idFormulario: string;
  }>(),
  { etapaCaso: null, examesDevolviveis: () => [] },
);

const emit = defineEmits<{
  (e: 'registrado', devolucao: DevolucaoDetalhada): void;
}>();

const toast = useToast();
const responsavel = useResponsavel();
const devolucoesStore = useDevolucoesStore();
const idBase = `nc-${++instancias}`;

const opcoesTipo = ORDEM_TIPOS_NAO_CONFORMIDADE.map((codigo) => ({ valor: codigo, rotulo: TIPOS_NAO_CONFORMIDADE[codigo] }));
const opcoesUnidade = UNIDADES_AGHU.map((unidade) => ({ valor: unidade, rotulo: unidade }));

/** Tipos de exame marcados para devolução (todos por padrão). */
const examesSelecionados = ref<string[]>(props.examesDevolviveis.map((e) => e.id));
const tentouRegistrar = ref(false);
const erroExames = computed(() =>
  tentouRegistrar.value && props.examesDevolviveis.length > 1 && examesSelecionados.value.length === 0
    ? 'Selecione ao menos um exame para devolver.'
    : '',
);
const salvando = ref(false);

const semEtiqueta = computed(() => props.contexto.tipo === 'SEM_ETIQUETA');

const etapaRotulo = computed(() => {
  if (props.contexto.tipo === 'SEM_ETIQUETA') return 'Recepção (leitura)';
  if (props.contexto.tipo === 'SOLICITACAO') return 'Recepção (conferência)';
  return props.etapaCaso ? ETAPAS[props.etapaCaso] : 'Caso';
});

const opcoesSimNao = [
  { valor: 'SIM', rotulo: 'Sim' },
  { valor: 'NAO', rotulo: 'Não' },
] as const;

const schema = computed(() =>
  toTypedSchema(
    z
      .object({
        unidadeOrigem: z.string().optional(),
        descricao: z.string().optional(),
        observacao: z.string().optional(),
        // Opcional no objeto e exigido no superRefine: assim todos os erros aparecem juntos
        // (o superRefine do zod só roda quando os campos do objeto passam).
        tipo: z.string().optional(),
        novaAmostra: z.enum(['SIM', 'NAO']).optional(),
      })
      .superRefine((v, ctx) => {
        if (!v.tipo) ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['tipo'], message: 'Selecione a não conformidade.' });
        if (!v.novaAmostra) ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['novaAmostra'], message: 'Escolha Sim ou Não.' });
        if (semEtiqueta.value && !v.unidadeOrigem) {
          ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['unidadeOrigem'], message: 'Selecione a unidade de origem.' });
        }
        if (v.tipo === 'OUTROS' && !v.descricao?.trim()) {
          ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['descricao'], message: 'Descreva a não conformidade.' });
        }
      }),
  ),
);

const { defineField, handleSubmit, errors } = useForm({
  validationSchema: schema,
  initialValues: {
    unidadeOrigem: '',
    tipo: props.contexto.tipo === 'SEM_ETIQUETA' ? 'SEM_SOLICITACAO_OU_ETIQUETA' : '',
    descricao: '',
    observacao: '',
    novaAmostra: undefined,
  },
});

const [unidadeOrigem] = defineField('unidadeOrigem');
const [tipo] = defineField('tipo');
const [descricao, descricaoAttrs] = defineField('descricao');
const [observacao] = defineField('observacao');
const [novaAmostra] = defineField('novaAmostra');

const solucao = computed(() => SOLUCOES_NAO_CONFORMIDADE[tipo.value as TipoNaoConformidadeCodigo]);

/** Contexto efetivo: na conferência, só os tipos de exame marcados são devolvidos. */
const contextoEfetivo = (): ContextoNaoConformidade =>
  props.contexto.tipo === 'SOLICITACAO' && props.examesDevolviveis.length > 1
    ? { tipo: 'SOLICITACAO', solicitacaoIds: [...examesSelecionados.value] }
    : props.contexto;

const enviar = handleSubmit(async (valores) => {
  if (erroExames.value) return;
  salvando.value = true;
  try {
    const tipoEscolhido = valores.tipo as TipoNaoConformidadeCodigo;
    const devolucao = await devolucoesStore.registrar({
      contexto: contextoEfetivo(),
      tipo: tipoEscolhido,
      descricao: tipoEscolhido === 'OUTROS' ? valores.descricao?.trim() : undefined,
      observacao: valores.observacao?.trim() || undefined,
      unidadeOrigem: valores.unidadeOrigem || undefined,
      novaAmostraSolicitada: valores.novaAmostra === 'SIM',
    });
    toast.success('Não conformidade e devolução registradas. O material saiu das filas ativas.');
    emit('registrado', devolucao);
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível registrar a não conformidade.'));
  } finally {
    salvando.value = false;
  }
});

const registrar = () => {
  tentouRegistrar.value = true;
  void enviar();
};

/** O modal mostra o carregamento no botão do rodapé. */
defineExpose({ salvando });

onMounted(async () => {
  await nextTick();
  document.getElementById(`${idBase}-tipo`)?.focus();
});
</script>
