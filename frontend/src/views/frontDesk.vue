<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-lab-text flex items-center gap-2">
          <MagnifyingGlassIcon class="h-5 w-5 text-gray-400" />
          Buscar Solicitação AGHU
        </h2>
        <p class="text-sm text-gray-500">Escaneie o código de barras da requisição ou digite o número da solicitação.</p>
      </template>

      <div class="flex items-end gap-3">
        <div class="flex-1 max-w-xs">
          <label class="form-label" for="codigo">Nº Solicitação / Registro</label>
          <input
            id="codigo"
            v-model="codigoBusca"
            type="text"
            class="form-control"
            placeholder="Digite aqui"
            @keyup.enter="buscar"
          >
        </div>
        <Button variant="primary" @click="buscar">Buscar</Button>
      </div>
    </Card>

    <Card v-if="buscou && !registroAghu">
      <div class="flex items-start gap-3 p-2">
        <ExclamationTriangleIcon class="h-6 w-6 shrink-0 text-amber-600" />
        <div>
          <p class="font-semibold text-amber-700">Solicitação não cadastrada no AGHU</p>
          <p class="text-sm text-gray-600 mt-1">
            Cadastre a solicitação do exame no AGHU antes de prosseguir. Essa etapa é feita diretamente
            no AGHU e não envolve este sistema.
          </p>
        </div>
      </div>
    </Card>

    <Card v-else-if="buscou && registroAghu && !exameValido">
      <div class="flex items-start gap-3 p-2">
        <XCircleIcon class="h-6 w-6 shrink-0 text-red-600" />
        <div>
          <p class="font-semibold text-red-700">Este exame não pertence à Anatomia Patológica</p>
          <p class="text-sm text-gray-600 mt-1">
            A solicitação <strong>{{ registroAghu.numeroSolicitacaoAghu }}</strong> está classificada no AGHU
            como <strong>{{ registroAghu.tipoExameRaw }}</strong>. Não receba esta amostra nesta bancada.
          </p>
        </div>
      </div>
    </Card>

    <div v-else-if="buscou && registroAghu && exameValido" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Dados do Paciente (AGHU)</h2>
            <p class="text-sm text-gray-500">Visualização unificada (somente leitura)</p>
          </template>

          <div class="space-y-4 text-sm">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Nome do paciente</p>
                <p class="font-bold text-lab-text text-base">{{ registroAghu.nomePaciente }}</p>
              </div>
              <Badge v-if="urgente" color="red">Urgente</Badge>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Registro (prontuário)</p>
                <p class="text-gray-700">{{ registroAghu.prontuario }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Solicitação</p>
                <p class="text-gray-700">{{ registroAghu.numeroSolicitacaoAghu }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Idade / Sexo</p>
                <p class="text-gray-700">{{ registroAghu.idade }} anos / {{ registroAghu.sexo }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Origem</p>
                <p class="text-gray-700">
                  {{ registroAghu.origem }}{{ registroAghu.clinica ? ` · ${registroAghu.clinica}` : '' }}
                </p>
              </div>
            </div>

            <div>
              <p class="text-[10px] font-semibold text-gray-400 uppercase">Procedimento (SUS)</p>
              <p class="text-gray-700">{{ registroAghu.procedimentoSus }}</p>
            </div>

            <div>
              <p class="text-[10px] font-semibold text-gray-400 uppercase">Indicação clínica</p>
              <p class="text-gray-700">{{ registroAghu.indicacaoClinica }}</p>
            </div>

            <div class="bg-gray-50 border border-gray-100 p-3 rounded-sm">
              <p class="text-[10px] font-semibold text-gray-500 uppercase">Descrição do material (médico solicitante)</p>
              <p class="text-gray-700 mt-1">
                {{ registroAghu.tipoMaterial || 'Não informado pelo médico solicitante.' }}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Registro de Peça (UACAP)</h2>
            <p class="text-sm text-gray-500">Preencha os dados físicos recebidos na bancada</p>
          </template>

          <div class="space-y-4">
            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                v-model="urgente"
                :disabled="registrado"
                class="h-4 w-4 text-red-600 rounded border-gray-300 focus:ring-red-500 disabled:opacity-60"
              >
              Exame de urgência
            </label>

            <div>
              <label class="form-label" for="qtdFrascos">Qtd. de frascos físicos *</label>
              <input
                id="qtdFrascos"
                v-model.number="quantidadeFrascos"
                type="number"
                min="1"
                :disabled="registrado"
                class="form-control max-w-[120px] disabled:bg-gray-50 disabled:text-gray-500"
              >
            </div>

            <div>
              <label class="form-label" for="descricaoFisica">Descrição do material físico (o que chegou?) *</label>
              <textarea
                id="descricaoFisica"
                v-model="descricaoFisica"
                rows="3"
                :disabled="registrado"
                class="form-control disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="Confirme ou complete a descrição do material recebido"
              ></textarea>
              <p v-if="!registroAghu.tipoMaterial" class="text-xs text-amber-600 mt-1">
                O médico não descreveu o material no AGHU — preencha manualmente antes de registrar.
              </p>
            </div>

            <Button v-if="!registrado" variant="primary" :disabled="!podeRegistrar" class="w-full" @click="registrarPeca">
              Registrar e Gerar Etiquetas
            </Button>
          </div>
        </Card>
      </div>

      <Card v-if="registrado" class="border-t-4 border-t-lab-success">
        <div class="space-y-4">
          <div class="flex items-start gap-3 p-3 rounded-lg bg-green-50 border border-green-200">
            <CheckCircleIcon class="h-6 w-6 shrink-0 text-green-600" />
            <div>
              <p class="font-semibold text-green-700">Recebimento registrado com sucesso!</p>
              <p class="text-sm text-green-600 mt-0.5">
                Caso {{ codigoGerado }}. Imprima as etiquetas e cole nos frascos correspondentes.
              </p>
            </div>
          </div>

          <div class="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <QrcodeBatchPrint :items="etiquetasFrascos" />
          </div>

          <div class="flex justify-end">
            <Button variant="primary" class="w-full md:w-auto md:min-w-[200px]" @click="enviarParaMacroscopia">
              <template #icon>
                <ArrowRightIcon class="h-5 w-5" />
              </template>
              Enviar para Macroscopia
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useToast } from 'vue-toastification';
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  CheckCircleIcon,
  ArrowRightIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import Button from '../components/button/button.vue';
import Badge from '../components/badge/badge.vue';
import QrcodeBatchPrint from '../components/qrcode/qrcodeBatchPrint.vue';
import { useExamSequenceStore } from '../stores/examSequence';
import { useExamCasesStore } from '../stores/examCases';
import { useAuthStore } from '../stores/auth';
import { formatExamCode } from '../utils/examCode';
import { EXAM_TYPE_PREFIX, type ExamType } from '../constants/examTypes';

interface AghuRawRecord {
  numeroSolicitacaoAghu: string;
  nomePaciente: string;
  prontuario: string;
  idade: number;
  sexo: 'M' | 'F';
  origem: 'Internado' | 'Ambulatorial';
  clinica?: string;
  tipoMaterial: string;
  tipoExameRaw: string;
  procedimentoSus: string;
  indicacaoClinica: string;
}

const AGHU_MOCK_DB: Record<string, AghuRawRecord> = {
  '442806': {
    numeroSolicitacaoAghu: '442806',
    nomePaciente: 'Claudiano de Farias Santos',
    prontuario: '21692793',
    idade: 44,
    sexo: 'M',
    origem: 'Internado',
    clinica: 'Cirurgia Geral',
    tipoMaterial: '1-COLON A DIREITA; 2-LINFONODO DA ARTERIA CÓLICA MÉDIA',
    tipoExameRaw: 'HP',
    procedimentoSus: 'Anatomopatológico Geral',
    indicacaoClinica: 'Investigação de neoplasia colônica.',
  },
  '379950': {
    numeroSolicitacaoAghu: '379950',
    nomePaciente: 'Maria Aparecida Silva',
    prontuario: '445210',
    idade: 58,
    sexo: 'F',
    origem: 'Internado',
    clinica: 'Hepatologia',
    tipoMaterial: '',
    tipoExameRaw: 'HP',
    procedimentoSus: 'Anatomopatológico Geral',
    indicacaoClinica: 'Nódulo hepático em investigação.',
  },
  '550010': {
    numeroSolicitacaoAghu: '550010',
    nomePaciente: 'Joana Pereira Lima',
    prontuario: '309981',
    idade: 36,
    sexo: 'F',
    origem: 'Ambulatorial',
    tipoMaterial: 'Esfregaço cervical',
    tipoExameRaw: 'CG',
    procedimentoSus: 'Citologia Geral',
    indicacaoClinica: 'Rotina de prevenção, colpocitologia.',
  },
  '991122': {
    numeroSolicitacaoAghu: '991122',
    nomePaciente: 'Roberto Alves',
    prontuario: '120044',
    idade: 70,
    sexo: 'M',
    origem: 'Internado',
    clinica: 'Clínica Médica',
    tipoMaterial: '',
    tipoExameRaw: 'Bioquímica',
    procedimentoSus: '-',
    indicacaoClinica: '-',
  },
};

const toast = useToast();
const sequenceStore = useExamSequenceStore();
const examCasesStore = useExamCasesStore();
const authStore = useAuthStore();

const codigoBusca = ref('');
const buscou = ref(false);
const registroAghu = ref<AghuRawRecord | null>(null);

const urgente = ref(false);
const quantidadeFrascos = ref(1);
const descricaoFisica = ref('');
const registrado = ref(false);
const codigoGerado = ref('');
const etiquetasFrascos = ref<{ identificador: string; tipo: 'frasco'; rotulo: string }[]>([]);

const exameValido = computed(() => {
  return !!registroAghu.value && registroAghu.value.tipoExameRaw in EXAM_TYPE_PREFIX;
});

const podeRegistrar = computed(() => {
  return quantidadeFrascos.value >= 1 && descricaoFisica.value.trim().length > 0;
});

function buscar() {
  buscou.value = true;
  registrado.value = false;
  const encontrado = AGHU_MOCK_DB[codigoBusca.value.trim()] ?? null;
  registroAghu.value = encontrado;
  descricaoFisica.value = encontrado?.tipoMaterial ?? '';
  quantidadeFrascos.value = 1;
  urgente.value = false;
}

function registrarPeca() {
  if (!podeRegistrar.value || !registroAghu.value) return;

  const tipoExame = registroAghu.value.tipoExameRaw as ExamType;
  const caso = sequenceStore.nextSequencial();
  codigoGerado.value = formatExamCode(tipoExame, caso.sequencial, caso.ano, caso.semestre);

  // Cada frasco recebe um ID FÍSICO próprio (F-{AGHU}-{NN}) — diferente do código
  // local do caso, que é compartilhado por todos os frascos da mesma peça.
  const total = quantidadeFrascos.value;
  const aghuNumero = registroAghu.value.numeroSolicitacaoAghu;
  etiquetasFrascos.value = Array.from({ length: total }, (_, i) => ({
    identificador: `F-${aghuNumero}-${String(i + 1).padStart(2, '0')}`,
    tipo: 'frasco' as const,
    rotulo: `Frasco ${String(i + 1).padStart(2, '0')}/${String(total).padStart(2, '0')}`,
  }));

  registrado.value = true;
  toast.success(
    urgente.value
      ? `Recebimento registrado com prioridade de urgência — caso ${codigoGerado.value}.`
      : 'Recebimento registrado com sucesso.'
  );
}

function enviarParaMacroscopia() {
  if (!registroAghu.value) return;

  examCasesStore.upsertCase(codigoGerado.value, {
    etapaAtual: 'Em Macroscopia',
    urgente: urgente.value,
    aghu: {
      numeroSolicitacaoAghu: registroAghu.value.numeroSolicitacaoAghu,
      nomePaciente: registroAghu.value.nomePaciente,
      prontuario: registroAghu.value.prontuario,
      idade: registroAghu.value.idade,
      sexo: registroAghu.value.sexo,
      origem: registroAghu.value.origem,
      clinica: registroAghu.value.clinica,
      tipoMaterial: registroAghu.value.tipoMaterial,
      tipoExame: registroAghu.value.tipoExameRaw as ExamType,
      procedimentoSus: registroAghu.value.procedimentoSus,
      indicacaoClinica: registroAghu.value.indicacaoClinica,
    },
    recepcao: {
      dataEntrada: new Date(),
      quantidadeFrascos: quantidadeFrascos.value,
      descricaoFisica: descricaoFisica.value,
      frascosIds: etiquetasFrascos.value.map(e => e.identificador),
      responsavel: authStore.user?.givenName?.[0] || authStore.user?.username || 'Recepção',
    },
  });

  toast.success(`Caso ${codigoGerado.value} enviado para a Macroscopia.`);
  codigoBusca.value = '';
  buscou.value = false;
  registroAghu.value = null;
  registrado.value = false;
}
</script>