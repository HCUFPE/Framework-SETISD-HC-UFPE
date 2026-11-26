<template>
  <div class="space-y-5">
    <div class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <strong>Ambiente de demonstração:</strong> os dados vêm do export AGHUX e incluem
      solicitações simuladas recentes. A referência usada para contar prazos e tempo na fila é
      {{ formatarDataHora(REFERENCIA_EM) }} — não é a data atual do computador.
    </div>

    <Card>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-xl font-bold text-paper-text">Fila de Marcação</h2>
            <p class="text-sm text-gray-500">
              Ordem automática pelos critérios de priorização vigentes ·
              {{ store.paginacao.total }} solicitação(ões) ·
              {{ formatarDataHora(REFERENCIA_EM) }} como referência
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="rounded-full bg-paper-primary/10 px-3 py-1 text-xs font-semibold text-paper-primary">RN-02: prioridade não editável pelo operador</span>
            <ColumnMenu
              :colunas="TODAS_COLUNAS"
              :model-value="colunasVisiveis"
              @update:model-value="colunasVisiveis = $event"
              @redefinir="restaurarColunas"
            />
          </div>
        </div>
      </template>

      <FilterBar
        v-model:busca="store.filtros.busca"
        v-model:status="store.filtros.status"
        v-model:tipoExame="store.filtros.tipoExame"
        v-model:unidadeSolicitante="store.filtros.unidadeSolicitante"
        v-model:periodo="store.filtros.periodo"
        :tipos-exame="tiposExame"
        :unidades-solicitantes="unidadesSolicitantes"
        @filtrar="store.aoFiltrar"
      />

      <p v-if="store.erro" class="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ store.erro }}</p>

      <div class="mt-5 overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th v-if="visivel('selecao') && podeEditar" class="px-3 py-2">
                <input
                  type="checkbox"
                  :checked="selecionadosTodas"
                  @change="alternarSelecaoTodas"
                  class="rounded border-gray-300 text-paper-primary focus:ring-paper-primary"
                />
              </th>
              <th v-if="visivel('ordem')" class="px-3 py-2">#</th>
              <th v-if="visivel('prioridade')" class="px-3 py-2">Prioridade</th>
              <th v-if="visivel('paciente')" class="px-3 py-2">Paciente / Prontuário</th>
              <th v-if="visivel('unidade')" class="px-3 py-2">Unidade solicitante</th>
              <th v-if="visivel('exames')" class="px-3 py-2">Exame(s)</th>
              <th v-if="visivel('status')" class="px-3 py-2">Status</th>
              <th v-if="visivel('tempo')" class="px-3 py-2">Tempo na fila</th>
              <th v-if="visivel('divergencias')" class="px-3 py-2">Divergências</th>
              <th v-if="visivel('acao')" class="px-3 py-2">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="(solicitacao, indice) in store.solicitacoes"
              :key="solicitacao.id"
              class="cursor-pointer bg-white transition hover:bg-gray-50"
              :class="{ 'bg-gray-50/50': selecionados.has(solicitacao.id) }"
              @click="store.abrir(solicitacao.id)"
            >
              <td v-if="visivel('selecao') && podeEditar" class="px-3 py-3">
                <input
                  type="checkbox"
                  :checked="selecionados.has(solicitacao.id)"
                  @change="alternarSelecao(solicitacao.id)"
                  class="rounded border-gray-300 text-paper-primary focus:ring-paper-primary"
                />
              </td>
              <td v-if="visivel('ordem')" class="px-3 py-3 font-medium text-gray-500">{{ (store.paginacao.pagina - 1) * store.paginacao.porPagina + indice + 1 }}</td>
              <td v-if="visivel('prioridade')" class="px-3 py-3">
                <PriorityBadge :prioridade="solicitacao.prioridade" />
                <span class="ml-2 text-xs text-gray-500">{{ solicitacao.pontuacao }}</span>
              </td>
              <td v-if="visivel('paciente')" class="px-3 py-3">
                <p class="font-medium text-gray-800">{{ solicitacao.pacienteNome }}</p>
                <p class="text-xs text-gray-500">{{ solicitacao.protocolo }} · pront. {{ solicitacao.prontuario }}</p>
              </td>
              <td v-if="visivel('unidade')" class="px-3 py-3">
                <p class="text-gray-700">{{ solicitacao.setorSolicitante }}</p>
                <p class="text-xs text-gray-500">{{ solicitacao.solicitanteNome }}</p>
              </td>
              <td v-if="visivel('exames')" class="px-3 py-3 text-gray-700">
                <p>{{ solicitacao.exame }}</p>
                <p v-if="solicitacao.itensExame.length > 1" class="text-xs text-paper-primary">+ {{ solicitacao.itensExame.length - 1 }} exame(s) na mesma solicitação</p>
              </td>
              <td v-if="visivel('status')" class="px-3 py-3"><StatusBadge :status="solicitacao.status" /></td>
              <td v-if="visivel('tempo')" class="px-3 py-3 text-gray-600">{{ formatarDuracao(horasDesde(solicitacao.recebidaEm)) }}</td>
              <td v-if="visivel('divergencias')" class="px-3 py-3"><DivergenciaBadge :quantidade="solicitacao.divergencias.filter((item) => !item.tratada).length" /></td>
              <td v-if="visivel('acao')" class="px-3 py-3">
                <div class="flex items-center gap-1">
                  <button
                    v-if="solicitacao.status === 'RECEBIDA' && podeEditar"
                    type="button"
                    @click.stop="agendarDaFila(solicitacao)"
                    class="text-xs bg-paper-success hover:bg-paper-success-hover text-white px-2 py-1 rounded"
                    title="Agendar solicitação"
                  >
                    Agendar
                  </button>
                  <button
                    v-if="podeEditar && (
                      solicitacao.status === 'AGUARDANDO_CONFIRMACAO' ||
                      solicitacao.status === 'NAO_CONFIRMADO' ||
                      solicitacao.status === 'AGUARDANDO_REAGENDAMENTO' ||
                      solicitacao.status === 'AGENDADA'
                    )"
                    type="button"
                    @click.stop="cancelarDaFila(solicitacao)"
                    class="text-xs bg-paper-danger hover:bg-paper-danger-hover text-white px-2 py-1 rounded"
                    title="Cancelar agendamento"
                  >
                    Cancelar
                  </button>
                  <button
                    v-if="solicitacao.status === 'AGENDADA' && podeEditar"
                    type="button"
                    @click.stop="reagendarDaFila(solicitacao)"
                    class="text-xs bg-paper-warning hover:bg-paper-warning-hover text-white px-2 py-1 rounded"
                    title="Reagendar"
                  >
                    Reagendar
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="store.solicitacoes.length === 0 && !store.carregando">
              <td :colspan="colunasVisiveis.length + (podeEditar && visivel('selecao') ? 1 : 0)" class="px-3 py-8 text-center text-gray-500">Nenhuma solicitação encontrada para os filtros selecionados.</td>
            </tr>
          </tbody>
        </table>
        <LoadingIndicator v-if="store.carregando" />
      </div>

      <!-- Barra de ação em lote -->
      <div
        v-if="podeEditar && selecionados.size > 0"
        class="mt-3 rounded border border-amber-200 bg-amber-50 p-3"
      >
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold text-amber-800">
            {{ selecionados.size }} item(ns) selecionado(s)
          </span>
          <select
            v-model="loteNovoStatus"
            class="campo-lote text-xs border border-amber-300 rounded px-2 py-1"
          >
            <option value="PROPOSTO">Proposta</option>
            <option value="ATIVO">Ativo</option>
            <option value="CANCELADO">Cancelado</option>
            <option value="CONCLUIDO">Concluído</option>
          </select>
          <input
            v-model="loteJustificativa"
            type="text"
            placeholder="Justificativa (obrigatória)"
            class="campo-lote text-xs border border-amber-300 rounded px-2 py-1 w-48"
          />
          <Button variant="warning" :loading="agendamentosStore.salvando" @click="abrirConfirmacaoLote">
            Aplicar em lote
          </Button>
          <button
            type="button"
            @click="limparSelecao"
            class="text-xs text-gray-600 hover:underline px-2 py-1"
          >
            Limpar seleção
          </button>
        </div>
        <p class="mt-1 text-xs text-amber-700">
          A justificativa será aplicada a todos os itens selecionados.
        </p>
      </div>

      <!-- Modal de confirmação da edição em lote -->
      <ModalLote
        v-if="modalLoteAberto"
        :selecionados="selecionadosArray"
        :novoStatus="loteNovoStatus"
        :justificativa="loteJustificativa"
        :ocupado="agendamentosStore.salvando"
        @confirmar="aplicarLote"
        @cancelar="modalLoteAberto = false"
      />

      <!-- Popup temporário de reverter após edição em lote -->
      <div
        v-if="reverterVisivel && reverterInfo"
        class="mt-3 rounded border border-emerald-200 bg-emerald-50 p-3 flex items-start gap-3"
      >
        <div class="rounded-full bg-emerald-100 p-1 text-emerald-600 flex-shrink-0">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.859-3.087Z" />
          </svg>
        </div>
        <div>
          <p class="text-sm text-emerald-800 font-semibold">
            Edição em lote aplicada: {{ reverterInfo.quantidade }} item(ns)
            para {{ reverterInfo.novoStatus }}.
          </p>
          <button
            type="button"
            class="mt-1 text-xs text-emerald-700 underline underline-offset-2 hover:text-emerald-900"
            @click="reverterLote"
          >
            Reverter alteração em lote
          </button>
          <span class="ml-2 text-xs text-emerald-600">
            (desaparece automaticamente em 8s)
          </span>
        </div>
      </div>

      <nav class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-gray-200 pt-4" aria-label="Paginação da fila">
        <p class="text-sm text-gray-600">
          Página <strong>{{ store.paginacao.pagina }}</strong> de {{ store.paginacao.totalPaginas }}
          · {{ store.paginacao.total }} solicitação(ões)
        </p>
        <div class="flex items-center gap-2">
          <Button variant="secondary" :disabled="store.paginacao.pagina <= 1 || store.carregando" @click="store.irParaPagina(store.paginacao.pagina - 1)">Anterior</Button>
          <span class="px-2 text-sm text-gray-600">20 por página</span>
          <Button variant="secondary" :disabled="store.paginacao.pagina >= store.paginacao.totalPaginas || store.carregando" @click="store.irParaPagina(store.paginacao.pagina + 1)">Próxima</Button>
        </div>
      </nav>
    </Card>

    <SolicitacaoDrawer
      :solicitacao="store.selecionada"
      :pode-editar="podeEditar"
      :erro="store.erro"
      :ocupado="store.carregando"
      @close="store.fechar()"
      @validar="validar"
      @contato="contatar"
      @efetuar-marcacao="efetuarMarcacao"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import ColumnMenu from '../components/ColumnMenu.vue';
import DivergenciaBadge from '../components/DivergenciaBadge.vue';
import FilterBar from '../components/FilterBar.vue';
import LoadingIndicator from '../components/LoadingIndicator.vue';
import ModalLote from '../components/agendamentos/ModalLote.vue';
import PriorityBadge from '../components/PriorityBadge.vue';
import SolicitacaoDrawer from '../components/SolicitacaoDrawer.vue';
import StatusBadge from '../components/StatusBadge.vue';
import { REFERENCIA_EM } from '../config/tempo';
import { listarUnidadesSolicitantes } from '../services/sae';
import { useAuthStore } from '../stores/auth';
import { useAgendamentosStore } from '../stores/agendamentos';
import { useSolicitacaoStore } from '../stores/solicitacao';
import type { OpcaoColuna, ResultadoContato, Solicitacao } from '../types/sae';
import { formatarDataHora, formatarDuracao, horasDesde } from '../utils/format';

const TODAS_COLUNAS: OpcaoColuna[] = [
  { chave: 'selecao', rotulo: '' },
  { chave: 'ordem', rotulo: '#' },
  { chave: 'prioridade', rotulo: 'Prioridade' },
  { chave: 'paciente', rotulo: 'Paciente / Prontuário' },
  { chave: 'unidade', rotulo: 'Unidade solicitante' },
  { chave: 'exames', rotulo: 'Exame(s)' },
  { chave: 'status', rotulo: 'Status' },
  { chave: 'tempo', rotulo: 'Tempo na fila' },
  { chave: 'divergencias', rotulo: 'Divergências' },
  { chave: 'acao', rotulo: 'Ação' },
];

const CHAVE_PREFERENCIA = 'sae.fila.colunas';

function colunasPadrao(): string[] {
  return TODAS_COLUNAS
    .map((coluna) => coluna.chave)
    .filter((chave) => chave !== 'divergencias' && chave !== 'acao');
}

function preferenciaInicial(): string[] {
  const padrao = colunasPadrao();
  try {
    const salvo = localStorage.getItem(CHAVE_PREFERENCIA);
    if (!salvo) return padrao;
    const interpretado: unknown = JSON.parse(salvo);
    if (!Array.isArray(interpretado)) return padrao;
    const validas = interpretado.filter((chave): chave is string =>
      typeof chave === 'string' && TODAS_COLUNAS.some((coluna) => coluna.chave === chave));
    return validas.length > 0 ? validas : padrao;
  } catch {
    return padrao;
  }
}

const store = useSolicitacaoStore();
const agendamentosStore = useAgendamentosStore();
const auth = useAuthStore();
const toast = useToast();
const router = useRouter();
const tiposExame = ['Imagem', 'Laboratório', 'Medicina Nuclear', 'Fonoaudiologia', 'Outro'];
const unidadesSolicitantes = ref<string[]>([]);
const colunasVisiveis = ref<string[]>(preferenciaInicial());

const podeEditar = computed(() => auth.temPerfil('OPERADOR', 'CHEFIA', 'AREA_GESTORA', 'ADMIN_TI'));

// Seleção múltipla para edição em lote
const selecionados = ref<Set<string>>(new Set());
const selecionadosArray = computed(() => Array.from(selecionados.value));
const selecionadosTodas = computed(() =>
  selecionados.value.size > 0 &&
  selecionados.value.size === store.solicitacoes.length,
);

function alternarSelecao(id: string): void {
  if (selecionados.value.has(id)) selecionados.value.delete(id);
  else selecionados.value.add(id);
}

function alternarSelecaoTodas(): void {
  if (selecionadosTodas.value) {
    selecionados.value.clear();
  } else {
    store.solicitacoes.forEach((s) => selecionados.value.add(s.id));
  }
}

function limparSelecao(): void {
  selecionados.value.clear();
}

// Estado da edição em lote
const modalLoteAberto = ref(false);
const loteNovoStatus = ref('ATIVO');
const loteJustificativa = ref('');

// Popup de reverter
const reverterVisivel = ref(false);
const reverterInfo = ref<{
  novoStatus: string;
  statusAnterior: string;
  quantidade: number;
} | null>(null);

watch(colunasVisiveis, (valor) => {
  try {
    localStorage.setItem(CHAVE_PREFERENCIA, JSON.stringify(valor));
  } catch {
    // Preferência não crítica: a tabela continua funcional sem persistência.
  }
});

function visivel(chave: string): boolean {
  return colunasVisiveis.value.includes(chave);
}

function restaurarColunas(): void {
  colunasVisiveis.value = colunasPadrao();
}

onMounted(() => {
  void store.carregar();
  void listarUnidadesSolicitantes()
    .then((unidades) => { unidadesSolicitantes.value = unidades; })
    .catch(() => { unidadesSolicitantes.value = []; });
});

async function validar(justificativa: string): Promise<void> {
  await store.validar(justificativa);
  if (!store.erro) toast.success('Dados validados e assinados eletronicamente.');
}

async function contatar(resultado: ResultadoContato, observacao: string): Promise<void> {
  await store.contatar(resultado, observacao);
  if (!store.erro) toast.info('Contato registrado no histórico.');
}

/** Leva o paciente já identificado para a fila de agendamento do calendário. */
function efetuarMarcacao(solicitacao: Solicitacao): void {
  store.fechar();
  void router.push({
    path: '/agendamentos',
    query: { solicitacao: solicitacao.id, busca: solicitacao.prontuario },
  });
}

function abrirConfirmacaoLote(): void {
  if (!loteJustificativa.value.trim()) return;
  modalLoteAberto.value = true;
}

async function aplicarLote(): Promise<void> {
  const ids = selecionadosArray.value;
  const resultado = await agendamentosStore.alterarStatusLote(
    ids,
    loteNovoStatus.value,
    loteJustificativa.value,
  );
  if (resultado) {
    toast.success(
      `${resultado.processados} agendamento(ns) alterado(s) para ${resultado.novoStatus}.`,
    );
    modalLoteAberto.value = false;
    limparSelecao();
    loteJustificativa.value = '';
    reverterInfo.value = {
      novoStatus: loteNovoStatus.value,
      statusAnterior: resultado.itens[0]?.statusAnterior ?? '',
      quantidade: resultado.processados,
    };
    reverterVisivel.value = true;
    setTimeout(() => {
      reverterVisivel.value = false;
      reverterInfo.value = null;
    }, 8000);
  } else {
    toast.error(agendamentosStore.erro || 'Não foi possível aplicar a edição em lote.');
  }
}

async function reverterLote(): Promise<void> {
  const ok = await agendamentosStore.reverterUltimoLote();
  if (ok) {
    toast.success('Edição em lote revertida.');
    reverterVisivel.value = false;
    reverterInfo.value = null;
  } else {
    toast.error(agendamentosStore.erro || 'Não foi possível reverter a edição em lote.');
  }
}

/**
 * Ações individuais da coluna "Ação" da fila.
 * Agendar leva ao calendário com a solicitação já selecionada, onde o operador
 * escolhe a vaga pelo dia; a marcação de uma solicitação recebida usa o fluxo da fila.
 */
function agendarDaFila(solicitacao: Solicitacao): void {
  efetuarMarcacao(solicitacao);
}

async function cancelarDaFila(solicitacao: Solicitacao): Promise<void> {
  store.selecionada = solicitacao;
  const justificativa = window.prompt('Informe a justificativa para o cancelamento:');
  if (!justificativa || !justificativa.trim()) return;
  await store.cancelarDaFila(justificativa.trim());
}

async function reagendarDaFila(solicitacao: Solicitacao): Promise<void> {
  store.selecionada = solicitacao;
  const slotId = window.prompt('Informe o ID da nova vaga (slot) para reagendar:');
  if (!slotId) return;
  const justificativa = window.prompt('Informe a justificativa para o reagendamento:');
  if (!justificativa || !justificativa.trim()) return;
  await store.reagendarDaFila(slotId, justificativa.trim());
}
</script>

<style scoped>
.campo-lote {
  width: 100%;
  border-radius: 0.25rem;
  border: 1px solid #d1d5db;
  padding: 0.45rem 0.6rem;
  font-size: 0.875rem;
  background: #fffbf0;
}
.campo-lote:focus {
  outline: none;
  border-color: #f59e0b;
}
</style>
