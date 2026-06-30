<template>
  <div class="space-y-6">
    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-lab-text flex items-center gap-2">
          <QrCodeIcon class="h-5 w-5 text-gray-400" />
          Identificar Cassete
        </h2>
        <p class="text-sm text-gray-500">Bipe o QR Code do cassete ou digite o código para iniciar a inclusão.</p>
      </template>

      <div class="flex items-end gap-3">
        <div class="flex-1 max-w-xs">
          <label class="form-label" for="codigoCassete">Código do Cassete</label>
          <input
            id="codigoCassete"
            v-model="codigoCassete"
            type="text"
            class="form-control"
            placeholder="Digite aqui"
            @keyup.enter="buscarCassete"
          >
        </div>
        <Button variant="primary" @click="buscarCassete">Buscar</Button>
      </div>
    </Card>

    <Card v-if="buscou && !casoAtual">
      <div class="flex items-start gap-3 p-2">
        <ExclamationTriangleIcon class="h-6 w-6 shrink-0 text-amber-600" />
        <div>
          <p class="font-semibold text-amber-700">Cassete não encontrado</p>
          <p class="text-sm text-gray-600 mt-1">
            Esse código não corresponde a nenhum cassete gerado pela Macroscopia.
          </p>
        </div>
      </div>
    </Card>

    <Card v-else-if="buscou && casoAtual && !['Em Processamento', 'Em Macroscopia'].includes(casoAtual.etapaAtual)">
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
        <!-- Contexto da amostra: visão unificada + progresso dos cassetes -->
        <Card>
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Contexto da Amostra</h2>
            <p class="text-sm text-gray-500">Garantia de rastreabilidade — todos os cassetes do caso</p>
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
            </div>

            <div class="border-t border-gray-100 pt-4">
              <p class="text-xs font-bold text-gray-500 uppercase mb-3">
                Cassetes do caso ({{ cassetesProcessados.length }} de {{ casoAtual.macroscopia!.cassetes.length }} incluídos)
              </p>
              <div class="space-y-2">
                <div
                  v-for="cassete in casoAtual.macroscopia!.cassetes"
                  :key="cassete.id"
                  class="flex items-center justify-between gap-3 p-2 rounded-lg"
                  :class="cassete.id === casseteAtivo?.id ? 'bg-lab-primary/10 ring-1 ring-lab-primary/30' : 'bg-gray-50'"
                >
                  <div class="flex items-center gap-2">
                    <span class="font-mono font-bold text-xs bg-white border border-gray-200 px-2 py-1 rounded">{{ cassete.id }}</span>
                    <span class="text-gray-600 text-xs">{{ cassete.estrutura }}</span>
                  </div>
                  <Badge :color="cassetesProcessados.includes(cassete.id) ? 'green' : 'gray'">
                    {{ cassetesProcessados.includes(cassete.id) ? 'Incluído' : 'Pendente' }}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <!-- Inclusão e microtomia do cassete ativo -->
        <Card v-if="casseteAtivo && !cassetesProcessados.includes(casseteAtivo.id)">
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Inclusão e Microtomia</h2>
            <p class="text-sm text-gray-500">Cassete {{ casseteAtivo.id }} — gera 1 bloco de parafina</p>
          </template>

          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="form-label" for="responsavelProc">Técnico Responsável *</label>
                <select id="responsavelProc" v-model="responsavelProcessamento" class="form-control">
                  <option value="" disabled>Selecione...</option>
                  <option v-for="nome in RESPONSAVEIS_PROCESSAMENTO" :key="nome" :value="nome">{{ nome }}</option>
                </select>
              </div>
              <div>
                <label class="form-label" for="dataProc">Data do Processamento *</label>
                <input id="dataProc" v-model="dataProcessamento" type="date" class="form-control">
              </div>
            </div>

            <div class="border-t border-gray-100 pt-4">
              <p class="text-xs font-bold text-gray-500 uppercase mb-2">Lâminas a gerar (conforme coloração solicitada na Macroscopia)</p>
              <div class="space-y-2">
                <label class="flex items-center gap-2 text-sm text-gray-500">
                  <input type="checkbox" checked disabled class="h-4 w-4 rounded border-gray-300">
                  HE (Hematoxilina-Eosina) - Rotina <span class="text-xs text-gray-400">(sempre gerada)</span>
                </label>
                <label
                  v-for="opcao in coloracaoesEspeciaisDisponiveis"
                  :key="opcao"
                  class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer"
                >
                  <input type="checkbox" v-model="coloracoesSelecionadas" :value="opcao" class="h-4 w-4 text-lab-primary rounded border-gray-300">
                  {{ opcao }}
                </label>
              </div>
              <p class="text-xs text-gray-400 mt-2">
                Total: {{ coloracoesSelecionadas.length + 1 }} lâmina(s) para este bloco.
              </p>
            </div>

            <Button variant="primary" :disabled="!podeRegistrarInclusao" class="w-full" @click="registrarInclusao">
              Registrar Inclusão e Emitir Etiquetas
            </Button>
          </div>
        </Card>

        <!-- Cassete já processado: mostra resumo -->
        <Card v-else-if="casseteAtivo">
          <template #header>
            <h2 class="text-lg font-bold text-lab-text">Cassete já incluído</h2>
          </template>
          <div class="flex items-center gap-3 p-2">
            <CheckCircleIcon class="h-6 w-6 text-green-600 shrink-0" />
            <p class="text-sm text-gray-600">
              O cassete {{ casseteAtivo.id }} já foi processado. Selecione outro cassete pendente para continuar.
            </p>
          </div>
        </Card>
      </div>

      <!-- Etiquetas geradas até agora (blocos + lâminas) -->
      <Card v-if="casoAtual.processamentoTecnico?.blocos.length">
        <template #header>
          <h2 class="text-lg font-bold text-lab-text">Blocos de Parafina Gerados</h2>
        </template>
        <QrcodeBatchPrint :items="etiquetasBlocos" />
      </Card>

      <Card v-if="casoAtual.processamentoTecnico?.laminas.length">
        <template #header>
          <h2 class="text-lg font-bold text-lab-text">Lâminas de Microscopia Geradas</h2>
          <p class="text-sm text-gray-500">Prontas para montagem e coloração.</p>
        </template>
        <QrcodeBatchPrint :items="etiquetasLaminas" />
      </Card>

      <!-- Liberação final: só quando TODOS os cassetes estiverem incluídos -->
      <Card v-if="todosProcessados" class="border-t-4 border-t-lab-success">
        <div class="space-y-4">
          <div class="flex items-start gap-3 p-3 rounded-lg bg-green-50 border border-green-200">
            <CheckCircleIcon class="h-6 w-6 shrink-0 text-green-600" />
            <div>
              <p class="font-semibold text-green-700">Todos os cassetes do caso foram processados!</p>
              <p class="text-sm text-green-600 mt-0.5">
                Os blocos serão encaminhados ao arquivo e as lâminas seguem para a Microscopia.
              </p>
            </div>
          </div>
          <div class="flex justify-end">
            <Button variant="primary" class="w-full md:w-auto md:min-w-[240px]" @click="enviarParaMicroscopia">
              <template #icon>
                <ArrowRightIcon class="h-5 w-5" />
              </template>
              Enviar Lâminas para Microscopia
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useToast } from 'vue-toastification';
import {
  QrCodeIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowRightIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/card/card.vue';
import Button from '../components/button/button.vue';
import Badge from '../components/badge/badge.vue';
import QrcodeBatchPrint from '../components/qrcode/qrcodeBatchPrint.vue';
import { useExamCasesStore } from '../stores/examCases';
import { useAuthStore } from '../stores/auth';
import { RESPONSAVEIS_PROCESSAMENTO } from '../constants/staffMembers';
import type { ExamCaseDetail, BlocoInfo, LaminaInfo } from '../types/exam';

const toast = useToast();
const examCasesStore = useExamCasesStore();
const authStore = useAuthStore();

const codigoCassete = ref('');
const buscou = ref(false);
const casoAtual = ref<ExamCaseDetail | null>(null);

const responsavelProcessamento = ref('');
const dataProcessamento = ref(new Date().toISOString().slice(0, 10));
const coloracoesSelecionadas = ref<string[]>([]);

const casseteAtivo = computed(() => {
  if (!casoAtual.value) return null;
  const idDoCassete = codigoCassete.value.trim().replace(`${casoAtual.value.codigoLocal}-`, '');
  return casoAtual.value.macroscopia?.cassetes.find(c => c.id === idDoCassete) ?? null;
});

// Coloração já pedida pelo macroscopista naquele cassete específico, exceto a rotina HE
// (que é sempre gerada e não precisa ser oferecida como opção extra).
const coloracaoesEspeciaisDisponiveis = computed(() => {
  if (!casseteAtivo.value) return [];
  const coloracao = casseteAtivo.value.coloracao;
  if (!coloracao || coloracao === 'HE (Hematoxilina-Eosina) - Rotina') return [];
  return [coloracao];
});

const cassetesProcessados = computed(() => {
  return casoAtual.value?.processamentoTecnico?.blocos.map(b => b.casseteId) ?? [];
});

const todosProcessados = computed(() => {
  if (!casoAtual.value?.macroscopia) return false;
  const total = casoAtual.value.macroscopia.cassetes.length;
  return total > 0 && cassetesProcessados.value.length === total;
});

const podeRegistrarInclusao = computed(() => {
  return responsavelProcessamento.value !== '' && dataProcessamento.value !== '';
});

const etiquetasBlocos = computed(() => {
  return (casoAtual.value?.processamentoTecnico?.blocos ?? []).map(b => ({
    identificador: `${casoAtual.value!.codigoLocal}-${b.id}-bloco`,
    tipo: 'bloco' as const,
    rotulo: `Bloco ${b.id}`,
  }));
});

const etiquetasLaminas = computed(() => {
  return (casoAtual.value?.processamentoTecnico?.laminas ?? []).map(l => ({
    identificador: `${casoAtual.value!.codigoLocal}-${l.id}`,
    tipo: 'lamina' as const,
    rotulo: `Lâmina ${l.id} (${l.coloracao.includes('HE') ? 'HE' : l.coloracao})`,
  }));
});

// Pré-marca a coloração especial do cassete (se houver) ao trocar de cassete ativo.
watch(casseteAtivo, () => {
  coloracoesSelecionadas.value = [...coloracaoesEspeciaisDisponiveis.value];
});

function buscarCassete() {
  buscou.value = true;
  casoAtual.value = examCasesStore.findByCassete(codigoCassete.value.trim());
}

function registrarInclusao() {
  if (!podeRegistrarInclusao.value || !casoAtual.value || !casseteAtivo.value) return;

  const blocoId = casseteAtivo.value.id;
  const novoBloco: BlocoInfo = {
    id: blocoId,
    casseteId: casseteAtivo.value.id,
    responsavel: responsavelProcessamento.value,
    dataInclusao: new Date(dataProcessamento.value),
  };

  const coloracoes = ['HE (Hematoxilina-Eosina) - Rotina', ...coloracoesSelecionadas.value];
  const novasLaminas: LaminaInfo[] = coloracoes.map((coloracao, i) => ({
    id: `${blocoId}-${String(i + 1).padStart(2, '0')}`,
    blocoId,
    coloracao,
  }));

  const atual = casoAtual.value.processamentoTecnico ?? { blocos: [], laminas: [] };

  examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
    etapaAtual: 'Em Processamento',
    processamentoTecnico: {
      ...atual,
      blocos: [...atual.blocos, novoBloco],
      laminas: [...atual.laminas, ...novasLaminas],
    },
  });

  casoAtual.value = examCasesStore.getCase(casoAtual.value.codigoLocal);
  toast.success(`Cassete ${blocoId} incluído. ${novasLaminas.length} lâmina(s) geradas.`);
}

function enviarParaMicroscopia() {
  if (!casoAtual.value) return;

  examCasesStore.upsertCase(casoAtual.value.codigoLocal, {
    etapaAtual: 'Em Microscopia',
    processamentoTecnico: {
      ...casoAtual.value.processamentoTecnico!,
      dataLiberacao: new Date(),
      responsavelLiberacao: authStore.user?.givenName?.[0] || authStore.user?.username || 'Processamento Técnico',
    },
  });

  toast.success(`Caso ${casoAtual.value.codigoLocal}: lâminas enviadas para a Microscopia, blocos encaminhados ao arquivo.`);
  codigoCassete.value = '';
  buscou.value = false;
  casoAtual.value = null;
  responsavelProcessamento.value = '';
  coloracoesSelecionadas.value = [];
}
</script>