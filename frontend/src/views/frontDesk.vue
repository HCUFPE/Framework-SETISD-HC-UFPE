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
import { useExamCasesStore } from '../stores/examCases';
import { useAuthStore } from '../stores/auth';
import { exameService, type FrascoDetalhe } from '../services/exameService';
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
// ID (UUID) real do frasco criado/encontrado no backend — usado no encaminhamento.
const frascoIdReal = ref<string | null>(null);
// true quando a busca encontrou um caso JÁ existente no banco (não é recebimento novo).
const casoExistente = ref(false);

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

async function registrarPeca() {
  if (!podeRegistrar.value || !registroAghu.value) return;

  const aghu = registroAghu.value;
  try {
    // Persiste a triagem no backend (cria exame + frasco + gera o nº de solicitação real).
    const resp = await exameService.criar({
      paciente: {
        nome: aghu.nomePaciente,
        cns: aghu.prontuario, // usa o prontuário como documento do paciente (dev/demo)
        // origem do backend é o sistema de saúde (SUS/HC), eixo diferente do
        // Internado/Ambulatorial da tela → deixa o default "SUS".
      },
      tipo_exame: aghu.tipoExameRaw,
      tipo_peca: descricaoFisica.value,
      numero_exame_aghu: aghu.numeroSolicitacaoAghu,
    });

    codigoGerado.value = resp.exame.numero_solicitacao;
    frascoIdReal.value = resp.frasco.id;

    // O backend cria 1 frasco por exame; a etiqueta usa o código interno real dele.
    etiquetasFrascos.value = [{
      identificador: resp.frasco.codigo_interno,
      tipo: 'frasco' as const,
      rotulo: 'Frasco 01/01',
    }];

    registrado.value = true;
    toast.success(
      urgente.value
        ? `Recebimento registrado com prioridade de urgência — caso ${codigoGerado.value}.`
        : `Recebimento registrado com sucesso — caso ${codigoGerado.value}.`
    );
  } catch {
    // O interceptor do axios já exibe o toast de erro.
  }
}

async function enviarParaMacroscopia() {
  if (!registroAghu.value || !frascoIdReal.value) return;

  try {
    // Muda o status do frasco no backend: Na Recepção → Aguardando Macroscopia.
    await exameService.encaminharMacroscopia(frascoIdReal.value);

    const aghu = registroAghu.value;
    // Guarda o contexto rico (AGHU + recepção) no store, chaveado pelo nº de
    // solicitação real, para a Macroscopia exibir a visão unificada na mesma sessão.
    examCasesStore.upsertCase(codigoGerado.value, {
      etapaAtual: 'Em Macroscopia',
      urgente: urgente.value,
      aghu: {
        numeroSolicitacaoAghu: aghu.numeroSolicitacaoAghu,
        nomePaciente: aghu.nomePaciente,
        prontuario: aghu.prontuario,
        idade: aghu.idade,
        sexo: aghu.sexo,
        origem: aghu.origem,
        clinica: aghu.clinica,
        tipoMaterial: aghu.tipoMaterial,
        tipoExame: aghu.tipoExameRaw as ExamType,
        procedimentoSus: aghu.procedimentoSus,
        indicacaoClinica: aghu.indicacaoClinica,
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
    frascoIdReal.value = null;
  } catch {
    // O interceptor do axios já exibe o toast de erro.
  }
}
</script>