<template>
  <Card v-if="recepcao.solicitacao">
    <template #header>
      <div class="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 class="text-lg font-bold text-gray-800">Completar e confirmar entrada</h2>
          <p class="text-sm text-gray-600">
            Solicitação AGHU <strong>{{ recepcao.solicitacao.codigoSolicitacao }}</strong> ·
            {{ recepcao.solicitacao.nomePaciente }} · {{ recepcao.solicitacao.descricaoMaterial }}
          </p>
        </div>
        <p class="text-xs text-gray-500"><span class="text-paper-danger">*</span> Obrigatório</p>
      </div>
    </template>

    <form id="form-complemento" novalidate class="space-y-6" @submit.prevent="confirmar">
      <!-- Resumo de erros -->
      <div v-if="tentouConfirmar && listaErros.length" ref="resumo" tabindex="-1" class="focus:outline-none">
        <Alert variant="danger" :title="`Faltam ${listaErros.length} campo${listaErros.length > 1 ? 's' : ''} obrigatório${listaErros.length > 1 ? 's' : ''} para confirmar`">
          <ul class="list-disc pl-5">
            <li v-for="item in listaErros" :key="item.campo">
              <a :href="`#${ids[item.campo]}`" class="font-semibold underline hover:no-underline" @click.prevent="focarCampo(item.campo)">
                {{ item.rotulo }}
              </a>
              — {{ item.mensagem }}
            </li>
          </ul>
        </Alert>
      </div>

      <!-- Tipo de exame -->
      <fieldset :id="ids.tipo" tabindex="-1" class="focus:outline-none">
        <legend class="form-label">Tipo de exame <span class="text-paper-danger">*</span></legend>
        <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-5" role="radiogroup">
          <label
            v-for="sigla in ORDEM_TIPOS_EXAME"
            :key="sigla"
            :class="tipo === sigla ? 'border-paper-primary bg-paper-primary-soft ring-2 ring-paper-primary/40' : 'border-gray-200 bg-white hover:bg-gray-50'"
            class="relative has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-paper-primary flex cursor-pointer flex-col rounded-lg border p-3 transition active:bg-gray-100"
          >
            <input v-model="tipo" type="radio" name="tipo-exame" :value="sigla" class="sr-only" />
            <span class="text-lg font-extrabold text-gray-900">{{ sigla }}</span>
            <span class="text-xs text-gray-600">{{ TIPOS_EXAME[sigla].nome }}</span>
            <span v-if="!TIPOS_EXAME[sigla].principal" class="mt-1 text-[11px] font-semibold text-paper-info-strong">Vincula a um caso existente</span>
          </label>
        </div>
        <p class="mt-2 text-xs text-gray-500">
          Selecionado a partir do exame do AGHU: <strong>{{ recepcao.solicitacao.nomeExame }}</strong>. Altere se necessário.
        </p>
        <p v-if="mostrarErro('tipo')" class="mt-1 text-sm text-paper-danger-strong">{{ errors.tipo }}</p>
      </fieldset>

      <!-- Caso principal -->
      <template v-if="!ehIhq">
        <div class="grid gap-6 md:grid-cols-3">
          <div class="form-group mb-0">
            <label :for="ids.quantidade" class="form-label">Quantidade de peças/frascos <span class="text-paper-danger">*</span></label>
            <input
              :id="ids.quantidade"
              v-model.number="quantidade"
              type="number"
              min="1"
              step="1"
              class="form-control"
              :aria-invalid="mostrarErro('quantidade') ? 'true' : undefined"
            />
            <p v-if="mostrarErro('quantidade')" class="mt-1 text-sm text-paper-danger-strong">{{ errors.quantidade }}</p>
          </div>

          <fieldset :id="ids.urgente" tabindex="-1" class="focus:outline-none">
            <legend class="form-label">Urgente? <span class="text-paper-danger">*</span></legend>
            <div class="flex gap-2" role="radiogroup" :aria-describedby="urgenciaAutomatica ? 'nota-urgencia-automatica' : undefined">
              <label
                v-for="opcao in opcoesUrgencia"
                :key="opcao.valor"
                :class="[
                  urgente === opcao.valor ? opcao.ativo : 'border-gray-300 bg-white text-gray-700',
                  urgenciaAutomatica ? 'cursor-not-allowed' : 'cursor-pointer active:bg-gray-100',
                  urgenciaAutomatica && urgente !== opcao.valor ? 'opacity-50' : '',
                  !urgenciaAutomatica && urgente !== opcao.valor ? 'hover:bg-gray-50' : '',
                ]"
                class="relative has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-paper-primary flex-1 rounded-md border px-4 py-2 text-center text-sm font-bold transition"
              >
                <input v-model="urgente" type="radio" name="urgente" :value="opcao.valor" :disabled="urgenciaAutomatica" class="sr-only" />
                {{ opcao.rotulo }}
              </label>
            </div>
            <p v-if="urgenciaAutomatica" id="nota-urgencia-automatica" class="mt-1 text-xs font-semibold text-gray-500">
              Automático para Congelação.
            </p>
            <p v-if="mostrarErro('urgente')" class="mt-1 text-sm text-paper-danger-strong">{{ errors.urgente }}</p>
          </fieldset>

          <div class="form-group mb-0">
            <label :for="ids.procedimento" class="form-label">Procedimento <span class="text-paper-danger">*</span></label>
            <select
              :id="ids.procedimento"
              v-model="procedimento"
              class="form-control"
              :aria-invalid="mostrarErro('procedimento') ? 'true' : undefined"
            >
              <option value="">Selecione</option>
              <option v-for="p in PROCEDIMENTOS" :key="p" :value="p">{{ p }}</option>
            </select>
            <p v-if="mostrarErro('procedimento')" class="mt-1 text-sm text-paper-danger-strong">{{ errors.procedimento }}</p>
          </div>
        </div>

        <div v-if="urgente === 'SIM'" class="form-group mb-0">
          <label :for="ids.motivoUrgencia" class="form-label">Motivo da urgência <span class="text-paper-danger">*</span></label>
          <input
            :id="ids.motivoUrgencia"
            v-model="motivoUrgencia"
            type="text"
            class="form-control"
            placeholder="Ex.: cirurgia oncológica programada"
            :aria-invalid="mostrarErro('motivoUrgencia') ? 'true' : undefined"
          />
          <p v-if="mostrarErro('motivoUrgencia')" class="mt-1 text-sm text-paper-danger-strong">{{ errors.motivoUrgencia }}</p>
        </div>
      </template>

      <!-- IHQ -->
      <template v-else>
        <CasoOrigemIhq :id="ids.casoOrigem" v-model="casoOrigem" :erro="mostrarErro('casoOrigem') ? errors.casoOrigem : undefined" />
        <div v-if="divergente && casoOrigem">
          <Alert variant="warning" title="Prontuário divergente">
            A solicitação é do prontuário <strong>{{ recepcao.solicitacao.prontuario }}</strong> e o caso
            {{ casoOrigem.numeroInterno }} é do prontuário <strong>{{ casoOrigem.prontuario }}</strong>. Confira a requisição
            antes de vincular.
          </Alert>
          <label :for="ids.divergenciaConfirmada" class="mt-3 flex cursor-pointer items-start gap-3 text-sm font-semibold text-gray-800">
            <input :id="ids.divergenciaConfirmada" v-model="divergenciaConfirmada" type="checkbox" class="focus-ring mt-0.5 h-5 w-5 rounded" />
            Confirmo o vínculo da IHQ ao caso {{ casoOrigem.numeroInterno }} apesar do prontuário divergente.
          </label>
          <p v-if="mostrarErro('divergenciaConfirmada')" class="mt-1 text-sm text-paper-danger-strong">{{ errors.divergenciaConfirmada }}</p>
        </div>
      </template>

      <div class="form-group mb-0">
        <label for="campo-observacoes" class="form-label">Observações</label>
        <textarea id="campo-observacoes" v-model="observacoes" rows="3" class="form-control"></textarea>
      </div>

      <p class="flex flex-wrap gap-x-6 gap-y-1 rounded-md bg-gray-50 px-4 py-2 text-sm text-gray-600">
        <span><strong>Entrada:</strong> registrada automaticamente na confirmação</span>
        <span><strong>Responsável:</strong> {{ responsavel.nome }} (automático)</span>
      </p>

      <div class="flex flex-wrap justify-end gap-2">
        <Button variant="secondary" :disabled="salvando" @click="recepcao.voltarParaConferencia()">Voltar à conferência</Button>
        <Button type="submit" :loading="salvando" title="Atalho: Ctrl+Enter">
          <CheckCircleIcon class="h-5 w-5 mr-2" aria-hidden="true" />
          {{ ehIhq ? 'Confirmar e vincular IHQ' : 'Confirmar entrada' }}
        </Button>
      </div>
    </form>
  </Card>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as z from 'zod';
import { useToast } from 'vue-toastification';
import { CheckCircleIcon } from '@heroicons/vue/24/outline';
import Alert from '../../Alert.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import CasoOrigemIhq from './CasoOrigemIhq.vue';
import { MOTIVO_URGENCIA_CONGELACAO, ORDEM_TIPOS_EXAME, PROCEDIMENTOS, TIPOS_EXAME } from '../../../constants/ap';
import { useResponsavel } from '../../../composables/useResponsavel';
import { mensagemDeErro } from '../../../services/ap';
import { useRecepcaoStore } from '../../../stores/recepcao';
import type { CasoElegivelIhq, TipoCasoPrincipal, TipoExame } from '../../../types/ap';

type Campo = 'tipo' | 'quantidade' | 'urgente' | 'motivoUrgencia' | 'procedimento' | 'casoOrigem' | 'divergenciaConfirmada';

const toast = useToast();
const recepcao = useRecepcaoStore();
const responsavel = useResponsavel();

const salvando = ref(false);
const tentouConfirmar = ref(false);
const resumo = ref<HTMLElement | null>(null);

const ids: Record<Campo, string> = {
  tipo: 'campo-tipo',
  quantidade: 'campo-quantidade',
  urgente: 'campo-urgente',
  motivoUrgencia: 'campo-motivo-urgencia',
  procedimento: 'campo-procedimento',
  casoOrigem: 'campo-caso-origem',
  divergenciaConfirmada: 'campo-divergencia',
};

const rotulos: Record<Campo, string> = {
  tipo: 'Tipo de exame',
  quantidade: 'Quantidade de peças/frascos',
  urgente: 'Urgente?',
  motivoUrgencia: 'Motivo da urgência',
  procedimento: 'Procedimento',
  casoOrigem: 'Caso de origem da IHQ',
  divergenciaConfirmada: 'Confirmação do prontuário divergente',
};

const opcoesUrgencia = [
  { valor: 'SIM', rotulo: 'Sim', ativo: 'border-paper-danger bg-paper-danger-soft text-paper-danger-strong' },
  { valor: 'NAO', rotulo: 'Não', ativo: 'border-paper-success bg-paper-success-soft text-paper-success-strong' },
] as const;

const schema = toTypedSchema(
  z
    .object({
      tipo: z.enum(['HP', 'CG', 'CCV', 'CO', 'IHQ'], { required_error: 'Selecione o tipo de exame.', invalid_type_error: 'Selecione o tipo de exame.' }),
      quantidade: z.any(),
      urgente: z.enum(['SIM', 'NAO']).optional(),
      motivoUrgencia: z.string().optional(),
      procedimento: z.string().optional(),
      observacoes: z.string().optional(),
      casoOrigem: z.any(),
      divergente: z.boolean().optional(),
      divergenciaConfirmada: z.boolean().optional(),
    })
    .superRefine((v, ctx) => {
      const falta = (campo: Campo, message: string) => ctx.addIssue({ code: z.ZodIssueCode.custom, path: [campo], message });
      if (v.tipo === 'IHQ') {
        if (!v.casoOrigem) falta('casoOrigem', 'Selecione o caso de origem.');
        else if (v.divergente && !v.divergenciaConfirmada) falta('divergenciaConfirmada', 'Confirme o vínculo apesar do prontuário divergente.');
        return;
      }
      const qtd = Number(v.quantidade);
      if (v.quantidade === '' || v.quantidade === undefined || !Number.isInteger(qtd) || qtd < 1) falta('quantidade', 'Informe 1 ou mais.');
      if (!v.urgente) falta('urgente', 'Escolha Sim ou Não.');
      if (v.urgente === 'SIM' && !v.motivoUrgencia?.trim()) falta('motivoUrgencia', 'Descreva o motivo da urgência.');
      if (!v.procedimento) falta('procedimento', 'Selecione o procedimento.');
    }),
);

const sugerido = recepcao.solicitacao?.tipoExameSugerido;

const { defineField, errors, handleSubmit, setFieldValue } = useForm({
  validationSchema: schema,
  initialValues: {
    tipo: sugerido as TipoExame | undefined,
    quantidade: 1,
    urgente: undefined,
    motivoUrgencia: '',
    procedimento: '',
    observacoes: '',
    casoOrigem: null as CasoElegivelIhq | null,
    divergente: false,
    divergenciaConfirmada: false,
  },
});

const [tipo] = defineField('tipo');
const [quantidade] = defineField('quantidade');
const [urgente] = defineField('urgente');
const [motivoUrgencia] = defineField('motivoUrgencia');
const [procedimento] = defineField('procedimento');
const [observacoes] = defineField('observacoes');
const [casoOrigemCampo] = defineField('casoOrigem');
const [divergenciaConfirmada] = defineField('divergenciaConfirmada');

const ehIhq = computed(() => tipo.value === 'IHQ');

/** Congelação é sempre urgente: "Urgente?" fica em Sim e não pode ser alterado. */
const urgenciaAutomatica = computed(() => tipo.value === 'CO');

/**
 * Ao entrar em Congelação, marca Sim e sugere o motivo (editável, ainda obrigatório).
 * Ao sair, volta "Urgente?" sem valor e limpa o motivo se ainda for a sugestão.
 */
watch(
  tipo,
  (novo, anterior) => {
    if (novo === 'CO') {
      setFieldValue('urgente', 'SIM');
      if (!motivoUrgencia.value?.trim()) setFieldValue('motivoUrgencia', MOTIVO_URGENCIA_CONGELACAO);
    } else if (anterior === 'CO') {
      setFieldValue('urgente', undefined);
      if (motivoUrgencia.value === MOTIVO_URGENCIA_CONGELACAO) setFieldValue('motivoUrgencia', '');
    }
  },
  { immediate: true },
);

/** Caso de origem escolhido; atualiza também o indicador de divergência de prontuário. */
const casoOrigem = computed<CasoElegivelIhq | null>({
  get: () => (casoOrigemCampo.value as CasoElegivelIhq | null) ?? null,
  set: (caso) => {
    casoOrigemCampo.value = caso;
    setFieldValue('divergente', !!caso && caso.prontuario !== recepcao.solicitacao?.prontuario);
    divergenciaConfirmada.value = false;
  },
});

const divergente = computed(() => !!casoOrigem.value && casoOrigem.value.prontuario !== recepcao.solicitacao?.prontuario);

/** Erros só aparecem depois da primeira tentativa de confirmar. */
const mostrarErro = (campo: Campo) => tentouConfirmar.value && !!(errors.value as Record<string, string | undefined>)[campo];

const ordemCampos: Campo[] = ['tipo', 'quantidade', 'urgente', 'motivoUrgencia', 'procedimento', 'casoOrigem', 'divergenciaConfirmada'];
const listaErros = computed(() =>
  ordemCampos
    .filter((campo) => (errors.value as Record<string, string | undefined>)[campo])
    .map((campo) => ({ campo, rotulo: rotulos[campo], mensagem: (errors.value as Record<string, string>)[campo] })),
);

/** Leva o foco ao campo indicado no resumo de erros. */
const focarCampo = (campo: Campo) => {
  const el = document.getElementById(ids[campo]);
  el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  const alvo = el?.matches('input, select, textarea') ? el : el?.querySelector<HTMLElement>('input, select, textarea, button') ?? el;
  alvo?.focus({ preventScroll: true });
};

const confirmar = handleSubmit(
  async (valores) => {
    salvando.value = true;
    try {
      if (valores.tipo === 'IHQ') {
        const caso = valores.casoOrigem as CasoElegivelIhq;
        await recepcao.vincularIhq({
          casoOrigemNumero: caso.numeroInterno,
          divergenciaConfirmada: !!valores.divergenciaConfirmada,
          observacoes: valores.observacoes,
        });
        toast.success(`IHQ vinculada ao caso ${caso.numeroInterno}.`);
      } else {
        await recepcao.confirmarEntrada({
          tipoExame: valores.tipo as TipoCasoPrincipal,
          quantidade: Number(valores.quantidade),
          urgente: valores.urgente === 'SIM',
          motivoUrgencia: valores.urgente === 'SIM' ? valores.motivoUrgencia : undefined,
          procedimento: valores.procedimento ?? '',
          observacoes: valores.observacoes,
        });
        const resultado = recepcao.resultado;
        if (resultado?.tipo === 'CASO') toast.success(`Entrada confirmada. Caso ${resultado.caso.numeroInterno} criado.`);
      }
    } catch (erro) {
      toast.error(mensagemDeErro(erro, 'Não foi possível confirmar a entrada.'));
    } finally {
      salvando.value = false;
    }
  },
  async () => {
    tentouConfirmar.value = true;
    toast.warning(`Faltam ${listaErros.value.length} campo(s) obrigatório(s) para confirmar a entrada.`);
    await nextTick();
    resumo.value?.focus();
  },
);

const enviar = () => {
  tentouConfirmar.value = true;
  confirmar();
};

/** Ctrl+Enter (ou Cmd+Enter) confirma a entrada. */
const aoTeclar = (evento: KeyboardEvent) => {
  if (evento.key === 'Enter' && (evento.ctrlKey || evento.metaKey)) {
    evento.preventDefault();
    if (!salvando.value) enviar();
  }
};
onMounted(() => document.addEventListener('keydown', aoTeclar));
onUnmounted(() => document.removeEventListener('keydown', aoTeclar));
</script>
