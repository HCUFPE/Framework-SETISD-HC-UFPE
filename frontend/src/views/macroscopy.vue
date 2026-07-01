<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-lab-text flex items-center gap-2">
          <QrCodeIcon class="h-5 w-5 text-gray-400" />
          Identificar Frasco na Macroscopia
        </h2>
        <p class="text-sm text-gray-500">Bipe o QR Code do frasco ou digite o identificador local.</p>
      </template>

      <div class="flex items-end gap-3">
        <div class="flex-1 max-w-xs">
          <label class="form-label" for="codigoFrasco">Código do Frasco</label>
          <input
            id="codigoFrasco"
            v-model="codigoFrasco"
            type="text"
            class="form-control"
            placeholder="Digite aqui"
            @keyup.enter="buscarFrasco"
          >
        </div>
        <Button variant="primary" @click="buscarFrasco">Buscar</Button>
      </div>
    </Card>

    <Card v-if="buscou && !casoAtual">
      <div class="flex items-start gap-3 p-2">
        <ExclamationTriangleIcon class="h-6 w-6 shrink-0 text-amber-600" />
        <div>
          <p class="font-semibold text-amber-700">Frasco não encontrado</p>
          <p class="text-sm text-gray-600 mt-1">
            Esse identificador não corresponde a nenhum frasco registrado pela Recepção.
          </p>
        </div>
      </div>
    </Card>

    <Card v-else-if="buscou && casoAtual && casoAtual.etapaAtual !== 'Em Macroscopia'">
      <div class="flex items-start gap-3 p-2">
        <ExclamationTriangleIcon class="h-6 w-6 shrink-0 text-amber-600" />
        <div>
          <p class="font-semibold text-amber-700">Este caso já avançou de etapa</p>
          <p class="text-sm text-gray-600 mt-1">
            O caso {{ casoAtual.codigoLocal }} está atualmente em "{{ casoAtual.etapaAtual }}".
          </p>
        </div>
      </div>
    </Card>

    <div v-else-if="buscou && casoAtual" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Visão Unificada do Caso</h2>
            <p class="text-sm text-gray-500">Dados demográficos, clínicos e de recepção (somente leitura)</p>
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
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Prontuário</p>
                <p class="text-gray-700">{{ casoAtual.aghu.prontuario }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Solicitação AGHU</p>
                <p class="text-gray-700">{{ casoAtual.aghu.numeroSolicitacaoAghu }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Código local</p>
                <p class="text-gray-700 font-mono">{{ casoAtual.codigoLocal }}</p>
              </div>
              <div>
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Frasco atual</p>
                <p class="text-gray-700 font-mono">{{ codigoFrasco }}</p>
              </div>
            </div>

            <div>
              <p class="text-[10px] font-semibold text-gray-400 uppercase">Procedimento solicitado</p>
              <p class="text-gray-700">{{ casoAtual.aghu.procedimentoSus }}</p>
            </div>

            <div class="bg-gray-50 border border-gray-100 p-3 rounded-sm">
              <p class="text-[10px] font-semibold text-gray-500 uppercase">Descrição (médico solicitante)</p>
              <p class="text-gray-700 mt-1">{{ casoAtual.aghu.tipoMaterial || 'Não informado.' }}</p>
            </div>

            <div class="border-t border-gray-100 pt-4">
              <p class="text-xs font-bold text-gray-500 uppercase mb-2">Dados da Recepção</p>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-[10px] font-semibold text-gray-400 uppercase">Recebido em</p>
                  <p class="text-gray-700">{{ formatDateShort(casoAtual.recepcao!.dataEntrada) }}</p>
                </div>
                <div>
                  <p class="text-[10px] font-semibold text-gray-400 uppercase">Qtd. frascos</p>
                  <p class="text-gray-700">{{ casoAtual.recepcao!.quantidadeFrascos }}</p>
                </div>
              </div>
              <div class="mt-3">
                <p class="text-[10px] font-semibold text-gray-400 uppercase">Material confirmado na Recepção</p>
                <p class="text-gray-700">{{ casoAtual.recepcao!.descricaoFisica }}</p>
              </div>
            </div>
          </div>
        </Card>

        <Card v-if="!cassetesGerados.length">
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Clivagem e Descrição Macroscópica</h2>
            <p class="text-sm text-gray-500">Registro de fragmentação da peça cirúrgica</p>
          </template>

          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="form-label" for="responsavel">Responsável (Macro) *</label>
                <select id="responsavel" v-model="responsavel" class="form-control">
                  <option value="" disabled>Selecione...</option>
                  <option v-for="nome in RESPONSAVEIS_MACROSCOPIA" :key="nome" :value="nome">{{ nome }}</option>
                </select>
              </div>
              <div>
                <label class="form-label" for="dataMacro">Data da Macro *</label>
                <input id="dataMacro" v-model="dataMacro" type="date" class="form-control">
              </div>
            </div>

            <div>
              <label class="form-label" for="descricaoMacro">Descrição Macroscópica Completa *</label>
              <textarea
                id="descricaoMacro"
                v-model="descricaoMacroscopica"
                rows="4"
                class="form-control"
                placeholder="Ex: Recebido frasco com fixador contendo fragmento de tecido nodular, pardacento, medindo..."
              ></textarea>
            </div>

            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
              <input type="checkbox" v-model="sobraMaterial" class="h-4 w-4 text-lab-primary rounded border-gray-300">
              Houve sobra de material?
            </label>

            <div class="border-t border-gray-100 pt-4 space-y-3">
              <p class="text-xs font-bold text-gray-500 uppercase">Estruturas identificadas</p>

              <div v-for="(estrutura, i) in estruturas" :key="estrutura.letra" class="flex items-center gap-3">
                <span class="font-mono font-bold text-lab-primary bg-lab-primary/10 px-2.5 py-1.5 rounded text-sm w-9 text-center shrink-0">
                  {{ estrutura.letra }}
                </span>
                <input
                  v-model="estrutura.nome"
                  type="text"
                  class="form-control flex-1"
                  placeholder="Ex: Útero, Trompa direita..."
                >
                <div class="flex items-center gap-1.5 shrink-0">
                  <label class="text-xs text-gray-500">Cassetes</label>
                  <input v-model.number="estrutura.quantidadeCassetes" type="number" min="1" class="form-control w-16">
                </div>
                <button v-if="estruturas.length > 1" @click="removerEstrutura(i)" class="text-gray-400 hover:text-red-600 shrink-0">
                  <TrashIcon class="h-5 w-5" />
                </button>
              </div>

              <button @click="adicionarEstrutura" class="text-sm font-medium text-lab-primary hover:underline flex items-center gap-1">
                <PlusIcon class="h-4 w-4" /> Adicionar estrutura
              </button>
            </div>

            <Button variant="primary" :disabled="!podeMapear" class="w-full" @click="mapearFragmentos">
              Mapear Fragmentos (Cassetes)
            </Button>
          </div>
        </Card>

        <Card v-else>
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Configuração dos Cassetes</h2>
            <p class="text-sm text-gray-500">Confirme a coloração de cada cassete antes de emitir as etiquetas</p>
          </template>

          <div class="space-y-3">
            <div
              v-for="cassete in cassetesGerados"
              :key="cassete.id"
              class="grid grid-cols-[48px_1fr_256px_144px] items-center gap-3 border border-gray-200 rounded-lg p-3"
            >
              <span class="h-10 font-mono font-bold text-lab-primary bg-lab-primary/10 rounded text-sm inline-flex items-center justify-center">
                {{ cassete.id }}
              </span>
              <input
                v-model="cassete.observacao"
                type="text"
                class="form-control h-10 w-full min-w-0"
                placeholder="Observações"
              >
              <select v-model="cassete.coloracao" class="form-control h-10 w-full">
                <option v-for="opcao in STAINING_OPTIONS" :key="opcao" :value="opcao">{{ opcao }}</option>
              </select>
              <span class="h-10 text-xs font-mono text-gray-400 truncate flex items-center justify-start pl-6 loading-none">
                {{ casoAtual.codigoLocal }}-{{ cassete.id }}
              </span>
            </div>

            <div v-if="!finalizado" class="flex justify-end gap-3 pt-2">
              <Button variant="default" @click="cassetesGerados = []">Voltar</Button>
              <Button variant="primary" @click="confirmarClivagem">Confirmar Clivagem e Emitir Etiquetas</Button>
            </div>
          </div>
        </Card>
      </div>

      <Card v-if="finalizado" class="border-t-4 border-t-lab-success">
        <div class="space-y-4">
          <div class="flex items-start gap-3 p-3 rounded-lg bg-green-50 border border-green-200">
            <CheckCircleIcon class="h-6 w-6 shrink-0 text-green-600" />
            <div>
              <p class="font-semibold text-green-700">Clivagem finalizada com sucesso!</p>
              <p class="text-sm text-green-600 mt-0.5">
                {{ cassetesGerados.length }} cassete(s) gerados para o caso {{ casoAtual.codigoLocal }}.
              </p>
            </div>
          </div>

          <div class="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <QrcodeBatchPrint :items="etiquetasCassetes" />
          </div>

          <div class="flex justify-end">
            <Button variant="primary" class="w-full md:w-auto md:min-w-[240px]" @click="enviarProcessamento">
              <template #icon>
                <ArrowRightIcon class="h-5 w-5" />
              </template>
              Enviar para Processamento Técnico
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
  QrCodeIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import Button from '../components/button/button.vue';
import Badge from '../components/badge/badge.vue';
import QrcodeBatchPrint from '../components/qrcode/qrcodeBatchPrint.vue';
import { useExamCasesStore } from '../stores/examCases';
import { exameService } from '../services/exameService';
import { formatDateShort } from '../utils/date';
import { RESPONSAVEIS_MACROSCOPIA, STAINING_OPTIONS } from '../constants/staffMembers';
import { EXAM_TYPE_PREFIX, type ExamType } from '../constants/examTypes';
import type { ExamCaseDetail, CasseteInfo } from '../types/exam';

const toast = useToast();
const examCasesStore = useExamCasesStore();

const codigoFrasco = ref('');
const buscou = ref(false);
const casoAtual = ref<ExamCaseDetail | null>(null);
// Identidade real do frasco no backend (resolvida na busca).
const frascoIdReal = ref<string | null>(null);
const frascoStatusReal = ref('');

// Deriva o tipo de exame a partir do prefixo do nº de solicitação (ex: "HP-0009/26.2" → HP).
function tipoExameDoNumero(numero: string): ExamType {
  const prefixo = numero.split('-')[0];
  const entrada = (Object.entries(EXAM_TYPE_PREFIX) as [ExamType, string][]).find(([, p]) => p === prefixo);
  return entrada?.[0] ?? 'HP';
}

const responsavel = ref('');
const dataMacro = ref(new Date().toISOString().slice(0, 10));
const descricaoMacroscopica = ref('');
const sobraMaterial = ref(false);

interface EstruturaForm {
  letra: string;
  nome: string;
  quantidadeCassetes: number;
}

const estruturas = ref<EstruturaForm[]>([{ letra: 'A', nome: '', quantidadeCassetes: 1 }]);
const cassetesGerados = ref<CasseteInfo[]>([]);
const finalizado = ref(false);
const etiquetasCassetes = ref<{ identificador: string; tipo: 'cassete'; rotulo: string }[]>([]);

const podeMapear = computed(() => {
  return (
    responsavel.value !== '' &&
    dataMacro.value !== '' &&
    descricaoMacroscopica.value.trim().length > 0 &&
    estruturas.value.every(e => e.nome.trim().length > 0 && e.quantidadeCassetes >= 1)
  );
});

async function buscarFrasco() {
  buscou.value = true;
  finalizado.value = false;
  cassetesGerados.value = [];
  casoAtual.value = null;
  frascoIdReal.value = null;

  const code = codigoFrasco.value.trim();
  if (!code) return;

  // O código impresso na Recepção é o "codigo_interno" (nº solicitação + "-F1");
  // se o usuário digitar só o nº de solicitação, busca por ele.
  const params = /-F\d+$/i.test(code) ? { codigo_interno: code } : { numero_solicitacao: code };
  try {
    const [frasco] = await exameService.buscarFrasco(params);
    if (!frasco) return;

    frascoIdReal.value = frasco.id_frasco;
    frascoStatusReal.value = frasco.status;

    // 'Processamento Completo' = macroscopia já registrada → caso já avançou.
    const etapa: ExamCaseDetail['etapaAtual'] =
      frasco.status === 'Processamento Completo' ? 'Em Processamento' : 'Em Macroscopia';

    // Usa o contexto rico da mesma sessão (Recepção) ou sintetiza a partir do backend.
    const local = examCasesStore.getCase(frasco.numero_solicitacao);
    const base: ExamCaseDetail = local ?? {
      codigoLocal: frasco.numero_solicitacao,
      etapaAtual: etapa,
      urgente: false,
      aghu: {
        numeroSolicitacaoAghu: '—',
        nomePaciente: frasco.paciente_nome,
        prontuario: '—',
        idade: 0,
        sexo: 'M',
        origem: 'Internado',
        tipoMaterial: frasco.tipo_peca ?? '',
        tipoExame: tipoExameDoNumero(frasco.numero_solicitacao),
        procedimentoSus: '—',
        indicacaoClinica: '—',
      },
      recepcao: {
        dataEntrada: frasco.data_criacao ? new Date(frasco.data_criacao) : new Date(),
        quantidadeFrascos: 1,
        descricaoFisica: frasco.tipo_peca ?? '—',
        frascosIds: [frasco.codigo_interno],
        responsavel: '—',
      },
    };

    // Status do backend é a fonte de verdade da etapa exibida.
    casoAtual.value = { ...base, etapaAtual: etapa };
  } catch {
    // interceptor exibe erro; casoAtual permanece null → template mostra "não encontrado".
  }
}

function adicionarEstrutura() {
  const proximaLetra = String.fromCharCode(65 + estruturas.value.length);
  estruturas.value.push({ letra: proximaLetra, nome: '', quantidadeCassetes: 1 });
}

function removerEstrutura(index: number) {
  estruturas.value.splice(index, 1);
  estruturas.value.forEach((e, i) => {
    e.letra = String.fromCharCode(65 + i);
  });
}

function mapearFragmentos() {
  if (!podeMapear.value) return;

  const lista: CasseteInfo[] = [];
  for (const estrutura of estruturas.value) {
    if (estrutura.quantidadeCassetes === 1) {
      lista.push({ id: estrutura.letra, estrutura: estrutura.nome, coloracao: STAINING_OPTIONS[0] });
    } else {
      for (let i = 1; i <= estrutura.quantidadeCassetes; i++) {
        lista.push({ id: `${estrutura.letra}${i}`, estrutura: estrutura.nome, coloracao: STAINING_OPTIONS[0] });
      }
    }
  }
  cassetesGerados.value = lista;
}

async function confirmarClivagem() {
  if (!casoAtual.value || !frascoIdReal.value) return;

  const total = cassetesGerados.value.length;
  if (total === 0) return;

  try {
    // O backend exige o frasco 'Em Macroscopia' antes de registrar.
    if (frascoStatusReal.value === 'Aguardando Macroscopia') {
      await exameService.iniciarMacroscopia(frascoIdReal.value);
      frascoStatusReal.value = 'Em Macroscopia';
    }

    const result = await exameService.registrarMacroscopia({
      id_frasco: frascoIdReal.value,
      descricao: descricaoMacroscopica.value,
      numero_cassetes: total,
    });

    // O backend é a fonte de verdade da identidade dos cassetes (letras A, B, C...).
    // Preserva estrutura/coloração digitadas casando pela ordem de geração.
    const preview = cassetesGerados.value;
    cassetesGerados.value = result.cassetes.map((c, i): CasseteInfo => ({
      id: c.letra_fragmento,
      estrutura: preview[i]?.estrutura ?? '',
      coloracao: preview[i]?.coloracao ?? STAINING_OPTIONS[0],
      observacao: preview[i]?.observacao,
    }));

    examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
      etapaAtual: 'Em Processamento', // o backend já avançou o exame nesta etapa
      macroscopia: {
        dataMacro: new Date(dataMacro.value),
        responsavel: responsavel.value,
        descricaoMacroscopica: descricaoMacroscopica.value,
        sobraMaterial: sobraMaterial.value,
        cassetes: cassetesGerados.value,
      },
    });

    etiquetasCassetes.value = cassetesGerados.value.map(c => ({
      identificador: `${casoAtual.value!.codigoLocal}-${c.id}`,
      tipo: 'cassete' as const,
      rotulo: `Cassete ${c.id} — ${c.estrutura}`,
    }));

    finalizado.value = true;
    toast.success('Clivagem registrada e etiquetas emitidas.');
  } catch {
    // O interceptor do axios já exibe o toast de erro.
  }
}

function enviarProcessamento() {
  if (!casoAtual.value) return;

  examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
    etapaAtual: 'Em Processamento',
  });

  toast.success(`Caso ${casoAtual.value.codigoLocal} enviado para o Processamento Técnico.`);
  codigoFrasco.value = '';
  buscou.value = false;
  casoAtual.value = null;
}
</script>