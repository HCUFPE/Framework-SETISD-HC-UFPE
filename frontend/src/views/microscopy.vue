<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-lab-text flex items-center gap-2">
          <QrCodeIcon class="h-5 w-5 text-gray-400" />
          Identificar Lâmina
        </h2>
        <p class="text-sm text-gray-500">Bipe o QR Code da lâmina ou digite o código de identificação para iniciar a análise.</p>
      </template>

      <div class="flex items-end gap-3">
        <div class="flex-1 max-w-xs">
          <label class="form-label" for="codigoLamina">Código da Lâmina</label>
          <input
            id="codigoLamina"
            v-model="codigoLamina"
            type="text"
            class="form-control"
            placeholder="Digite aqui"
            @keyup.enter="buscarLamina"
          >
        </div>
        <Button variant="primary" @click="buscarLamina">Buscar</Button>
      </div>
    </Card>

    <Card v-if="buscou && !casoAtual">
      <div class="flex items-start gap-3 p-2">
        <ExclamationTriangleIcon class="h-6 w-6 shrink-0 text-amber-600" />
        <div>
          <p class="font-semibold text-amber-700">Lâmina não encontrada</p>
          <p class="text-sm text-gray-600 mt-1">Esse código não corresponde a nenhuma lâmina registrada pelo Processamento Técnico.</p>
        </div>
      </div>
    </Card>

    <div v-else-if="buscou && casoAtual" class="space-y-6">

      <!-- Toggle de papel (só enquanto não temos AD/LDAP real) -->
      <div class="flex items-center gap-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <p class="text-sm font-medium text-gray-600 shrink-0">Atuando como:</p>
        <div class="flex gap-2">
          <button
            @click="papel = 'residente'"
            class="px-4 py-1.5 text-sm font-medium rounded-full transition-colors"
            :class="papel === 'residente' ? 'bg-lab-primary text-white' : 'bg-white text-gray-600 border border-gray-300'"
          >
            Residente
          </button>
          <button
            @click="papel = 'patologista'"
            class="px-4 py-1.5 text-sm font-medium rounded-full transition-colors"
            :class="papel === 'patologista' ? 'bg-lab-primary text-white' : 'bg-white text-gray-600 border border-gray-300'"
          >
            Médico Patologista
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Visão Unificada -->
        <Card>
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Visão Unificada do Caso</h2>
            <p class="text-sm text-gray-500">Somente leitura — toda a cadeia do caso</p>
          </template>

          <div class="space-y-4 text-sm">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Paciente</p>
                <p class="font-bold text-lab-text text-base">{{ casoAtual.aghu.nomePaciente }}</p>
              </div>
              <Badge v-if="casoAtual.urgente" color="red">Urgente</Badge>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Solicitação AGHU</p>
                <p class="text-gray-700">{{ casoAtual.aghu.numeroSolicitacaoAghu }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Código local</p>
                <p class="text-gray-700 font-mono">{{ casoAtual.codigoLocal }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Procedimento (SUS)</p>
                <p class="text-gray-700">{{ casoAtual.aghu.procedimentoSus }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Origem</p>
                <p class="text-gray-700">{{ casoAtual.aghu.origem }}{{ casoAtual.aghu.clinica ? ` · ${casoAtual.aghu.clinica}` : '' }}</p>
              </div>
            </div>

            <div class="bg-gray-50 border border-gray-100 p-3 rounded-sm">
              <p class="text-[10px] font-semibold text-gray-500 uppercase">Indicação clínica</p>
              <p class="text-gray-700 mt-1">{{ casoAtual.aghu.indicacaoClinica }}</p>
            </div>

            <div v-if="casoAtual.macroscopia" class="border-t border-gray-100 pt-4">
              <p class="text-xs font-bold text-gray-500 uppercase mb-2">Macroscopia</p>
              <p class="text-gray-600 text-xs leading-relaxed">{{ casoAtual.macroscopia.descricaoMacroscopica }}</p>
              <div class="flex flex-wrap gap-1.5 mt-2">
                <span
                  v-for="c in casoAtual.macroscopia.cassetes"
                  :key="c.id"
                  class="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                  :title="c.estrutura"
                >
                  {{ c.id }}
                </span>
              </div>
            </div>

            <div v-if="casoAtual.processamentoTecnico" class="border-t border-gray-100 pt-4">
              <p class="text-xs font-bold text-gray-500 uppercase mb-2">Processamento Técnico</p>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <p class="text-[10px] font-semibold text-gray-400 uppercase">Blocos gerados</p>
                  <p class="text-gray-700">{{ casoAtual.processamentoTecnico.blocos.length }}</p>
                </div>
                <div>
                  <p class="text-[10px] font-semibold text-gray-400 uppercase">Lâminas geradas</p>
                  <p class="text-gray-700">{{ casoAtual.processamentoTecnico.laminas.length }}</p>
                </div>
              </div>
            </div>

            <!-- Lâmina atual em análise -->
            <div class="border-t border-gray-100 pt-4">
              <p class="text-xs font-bold text-gray-500 uppercase mb-2">Lâmina em análise</p>
              <div class="bg-lab-primary/5 border border-lab-primary/20 rounded p-3">
                <p class="font-mono font-bold text-lab-primary text-sm">{{ codigoLamina }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ laminaAtiva?.coloracao ?? '-' }}</p>
              </div>
            </div>
          </div>
        </Card>

        <!-- Painel do Residente -->
        <Card v-if="papel === 'residente'">
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Laudo Prévio</h2>
            <p class="text-sm text-gray-500">Elaborado pelo residente antes da revisão do patologista</p>
          </template>

          <div v-if="!laudoEnviado" class="space-y-4">
            <div>
              <label class="form-label" for="responsavelRes">Residente Responsável *</label>
              <select id="responsavelRes" v-model="responsavelMicroscopia" class="form-control">
                <option value="" disabled>Selecione...</option>
                <option v-for="nome in RESPONSAVEIS_MICROSCOPIA" :key="nome" :value="nome">{{ nome }}</option>
              </select>
            </div>

            <div>
              <label class="form-label" for="laudoPrevio">Laudo Prévio / Impressões *</label>
              <textarea
                id="laudoPrevio"
                v-model="laudoPrevio"
                rows="6"
                class="form-control"
                placeholder="Descreva as impressões microscópicas, achados e hipótese diagnóstica..."
              ></textarea>
            </div>

            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                v-model="precisaComplementoPreLaudo"
                class="h-4 w-4 text-lab-primary rounded border-gray-300"
              >
              Precisa de material complementar antes de elaborar o laudo
            </label>

            <div v-if="precisaComplementoPreLaudo" class="space-y-2 pl-6">
              <label class="form-label" for="marcadoresPreLaudo">Marcadores / Complemento solicitado *</label>
              <input
                id="marcadoresPreLaudo"
                v-model="marcadoresPreLaudo"
                type="text"
                class="form-control"
                placeholder="Ex: HER2, p53, Ki-67"
              >
            </div>

            <Button
              variant="primary"
              :disabled="!podeEnviarLaudo"
              class="w-full"
              @click="enviarLaudoResidente"
            >
              Encaminhar para Revisão do Patologista
            </Button>
          </div>

          <div v-else class="flex items-start gap-3 p-3 rounded-lg bg-green-50 border border-green-200">
            <CheckCircleIcon class="h-6 w-6 shrink-0 text-green-600" />
            <div>
              <p class="font-semibold text-green-700">Laudo prévio encaminhado!</p>
              <p class="text-sm text-green-600 mt-0.5">Aguardando revisão do médico patologista.</p>
            </div>
          </div>
        </Card>

        <!-- Painel do Patologista -->
        <Card v-else-if="papel === 'patologista'">
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Revisão e Diagnóstico Final</h2>
            <p class="text-sm text-gray-500">Análise do patologista responsável</p>
          </template>

          <div class="space-y-4">
            <div>
              <label class="form-label" for="responsavelPat">Patologista Responsável *</label>
              <select id="responsavelPat" v-model="responsavelMicroscopia" class="form-control">
                <option value="" disabled>Selecione...</option>
                <option v-for="nome in RESPONSAVEIS_MICROSCOPIA" :key="nome" :value="nome">{{ nome }}</option>
              </select>
            </div>

            <!-- Laudo prévio do residente, se existir -->
            <div v-if="casoAtual.microscopia?.laudo" class="bg-amber-50 border border-amber-100 p-3 rounded-sm">
              <p class="text-[10px] font-bold text-amber-700 uppercase">Laudo prévio do residente</p>
              <p class="text-xs text-gray-800 mt-2 font-mono leading-relaxed whitespace-pre-wrap">
                {{ casoAtual.microscopia.laudo }}
              </p>
            </div>

            <div v-else class="bg-gray-50 border border-gray-200 p-3 rounded-sm text-sm text-gray-500 italic">
              Laudo prévio ainda não elaborado pelo residente.
            </div>

            <div>
              <label class="form-label" for="obsPatologista">Complemento / Observações (opcional)</label>
              <textarea
                id="obsPatologista"
                v-model="obsPatologista"
                rows="3"
                class="form-control"
                placeholder="Observações adicionais do patologista..."
              ></textarea>
            </div>

            <!-- Solicitação de IHQ -->
            <div v-if="acaoPatologista === 'ihq'" class="bg-gray-50 border border-gray-200 p-4 rounded-lg space-y-3">
              <p class="text-sm font-semibold text-gray-700">Solicitar IHQ / Complemento</p>
              <div>
                <label class="form-label" for="marcadores">Marcadores / Complemento *</label>
                <input
                  id="marcadores"
                  v-model="marcadoresIhq"
                  type="text"
                  class="form-control"
                  placeholder="Ex: HER2, p53, Ki-67, CD20"
                >
              </div>
              <div class="flex gap-3">
                <Button variant="danger" @click="solicitarIhq" :disabled="!marcadoresIhq.trim()">
                  Confirmar Solicitação
                </Button>
                <Button variant="default" @click="acaoPatologista = null">Cancelar</Button>
              </div>
            </div>

            <!-- Solicitação de Revisão Interna -->
            <div v-else-if="acaoPatologista === 'revisao'" class="bg-gray-50 border border-gray-200 p-4 rounded-lg space-y-3">
              <p class="text-sm font-semibold text-gray-700">Encaminhar para Revisão Interna</p>
              <div>
                <label class="form-label" for="obsRevisao">Motivo / Observação *</label>
                <textarea
                  id="obsRevisao"
                  v-model="obsRevisao"
                  rows="2"
                  class="form-control"
                  placeholder="Descreva o motivo da revisão interna..."
                ></textarea>
              </div>
              <div class="flex gap-3">
                <Button variant="warning" @click="solicitarRevisao" :disabled="!obsRevisao.trim()">
                  Confirmar Revisão
                </Button>
                <Button variant="default" @click="acaoPatologista = null">Cancelar</Button>
              </div>
            </div>

            <!-- Botões de ação (estado padrão) -->
            <div v-else class="flex flex-col gap-2 pt-2">
              <Button
                variant="primary"
                :disabled="!responsavelMicroscopia"
                class="w-full"
                @click="aprovarLaudo"
              >
                <template #icon><CheckCircleIcon class="h-5 w-5" /></template>
                Aprovar e Liberar
              </Button>
              <div class="grid grid-cols-2 gap-2">
                <Button
                  variant="warning"
                  :disabled="!responsavelMicroscopia"
                  class="w-full"
                  @click="acaoPatologista = 'ihq'"
                >
                  Solicitar IHQ / Complemento
                </Button>
                <Button
                  variant="default"
                  :disabled="!responsavelMicroscopia"
                  class="w-full"
                  @click="acaoPatologista = 'revisao'"
                >
                  Revisão Interna
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Card de caso encerrado -->
      <Card v-if="casoEncerrado" class="border-t-4 border-t-lab-success">
        <div class="flex items-start gap-3 p-3 rounded-lg bg-green-50 border border-green-200">
          <CheckCircleIcon class="h-6 w-6 shrink-0 text-green-600" />
          <div>
            <p class="font-semibold text-green-700">Caso {{ casoAtual.codigoLocal }} liberado!</p>
            <p class="text-sm text-green-600 mt-0.5">
              Laudo deve ser registrado e liberado no AGHU. Este sistema marca o caso como concluído.
            </p>
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
  QrCodeIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import Button from '../components/button/button.vue';
import Badge from '../components/badge/badge.vue';
import { useExamCasesStore } from '../stores/examCases';
import { RESPONSAVEIS_MICROSCOPIA } from '../constants/staffMembers';
import type { ExamCaseDetail } from '../types/exam';

const toast = useToast();
const examCasesStore = useExamCasesStore();

const codigoLamina = ref('');
const buscou = ref(false);
const casoAtual = ref<ExamCaseDetail | null>(null);
const papel = ref<'residente' | 'patologista'>('residente');

const responsavelMicroscopia = ref('');
const laudoPrevio = ref('');
const precisaComplementoPreLaudo = ref(false);
const marcadoresPreLaudo = ref('');
const laudoEnviado = ref(false);

const obsPatologista = ref('');
const acaoPatologista = ref<'ihq' | 'revisao' | null>(null);
const marcadoresIhq = ref('');
const obsRevisao = ref('');
const casoEncerrado = ref(false);

// A lâmina ativa é a que foi buscada — procura no processamento do caso.
const laminaAtiva = computed(() => {
  if (!casoAtual.value?.processamentoTecnico) return null;
  return casoAtual.value.processamentoTecnico.laminas.find(l =>
    `${casoAtual.value!.codigoLocal}-${l.id}` === codigoLamina.value.trim()
  ) ?? null;
});

const podeEnviarLaudo = computed(() => {
  if (!responsavelMicroscopia.value) return false;
  if (precisaComplementoPreLaudo.value) return marcadoresPreLaudo.value.trim().length > 0;
  return laudoPrevio.value.trim().length > 0;
});

function buscarLamina() {
  buscou.value = true;
  laudoEnviado.value = false;
  casoEncerrado.value = false;
  acaoPatologista.value = null;
  responsavelMicroscopia.value = '';

  // Busca o caso que contém a lâmina pelo código completo.
  casoAtual.value = Object.values(examCasesStore.cases).find(c =>
    c.processamentoTecnico?.laminas.some(l =>
      `${c.codigoLocal}-${l.id}` === codigoLamina.value.trim()
    )
  ) ?? null;
}

function enviarLaudoResidente() {
  if (!podeEnviarLaudo.value || !casoAtual.value) return;

  if (precisaComplementoPreLaudo.value) {
    examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
      etapaAtual: 'Em Processamento',
      microscopia: {
        dataRecebimento: new Date(),
        laudo: laudoPrevio.value,
        solicitouComplemento: true,
      },
    });
    toast.warning(`Complemento solicitado (${marcadoresPreLaudo.value}). Caso voltou para Processamento Técnico.`);
  } else {
    examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
      etapaAtual: 'Revisão Pendente',
      microscopia: {
        dataRecebimento: new Date(),
        laudo: laudoPrevio.value,
        solicitouComplemento: false,
      },
    });
    toast.success('Laudo prévio encaminhado para revisão do patologista.');
  }

  casoAtual.value = examCasesStore.getCase(casoAtual.value.codigoLocal);
  laudoEnviado.value = true;
}

function aprovarLaudo() {
  if (!casoAtual.value) return;

  const laudoFinal = [
    casoAtual.value.microscopia?.laudo,
    obsPatologista.value.trim() || null,
  ].filter(Boolean).join('\n\n');

  examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
    etapaAtual: 'Liberado',
    microscopia: {
      ...(casoAtual.value.microscopia ?? { dataRecebimento: new Date(), solicitouComplemento: false }),
      laudo: laudoFinal,
      dataLiberacaoLaudo: new Date(),
      responsavelLiberacao: responsavelMicroscopia.value,
    },
  });

  casoAtual.value = examCasesStore.getCase(casoAtual.value.codigoLocal);
  casoEncerrado.value = true;
  toast.success(`Caso ${casoAtual.value?.codigoLocal} liberado. Registre e libere o laudo no AGHU.`);
}

function solicitarIhq() {
  if (!casoAtual.value || !marcadoresIhq.value.trim()) return;

  examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
    etapaAtual: 'Em Processamento',
    microscopia: {
      ...(casoAtual.value.microscopia ?? { dataRecebimento: new Date(), solicitouComplemento: false, laudo: '' }),
      solicitouComplemento: true,
    },
  });

  casoAtual.value = examCasesStore.getCase(casoAtual.value.codigoLocal);
  toast.warning(`IHQ solicitada (${marcadoresIhq.value}). Caso retornou para Processamento Técnico.`);
  acaoPatologista.value = null;
  marcadoresIhq.value = '';
}

function solicitarRevisao() {
  if (!casoAtual.value || !obsRevisao.value.trim()) return;

  examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
    etapaAtual: 'Revisão Pendente',
  });

  casoAtual.value = examCasesStore.getCase(casoAtual.value.codigoLocal);
  toast.info('Caso encaminhado para revisão interna.');
  acaoPatologista.value = null;
  obsRevisao.value = '';
}
</script>