<template>
  <div class="space-y-5">
    <div v-if="USAR_MOCKS" class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <strong>Ambiente de demonstração:</strong> a agenda começa em
      {{ formatarDataHora(REFERENCIA_EM) }} e as vagas são simuladas. Nenhum dado de endereço do paciente é utilizado.
    </div>

    <Card>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold text-paper-text">Calendário de Agendamentos</h2>
            <p class="text-sm text-gray-500">
              Vagas por unidade/exame, ocupação em tempo real e sugestões automáticas para a solicitação selecionada.
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button variant="info" :disabled="!store.podeEditar" @click="store.abrirSugestoes">Ver sugestões</Button>
            <Button
              v-if="store.podeGerirVagas"
              variant="secondary"
              @click="gestorVagasAberto = true"
            >Gestão de vagas</Button>
            <span v-if="!store.podeEditar" class="self-center rounded-full bg-gray-200 px-3 py-1 text-xs font-semibold text-gray-600">
              Modo somente leitura (Coordenação)
            </span>
          </div>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <label class="text-sm">
          <span class="mb-1 block font-semibold text-gray-700">Unidade</span>
          <select v-model="store.filtros.unidade" class="campo" @change="store.aoFiltrar">
            <option value="">Todas as unidades</option>
            <option v-for="unidade in store.unidades" :key="unidade" :value="unidade">{{ unidade }}</option>
          </select>
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-semibold text-gray-700">Tipo de exame</span>
          <select v-model="store.filtros.codigoExame" class="campo" @change="store.aoFiltrar">
            <option value="">Todos os exames</option>
            <option v-for="exame in store.exames" :key="exame.codigo" :value="exame.codigo">
              {{ exame.nome }} ({{ exame.codigo }})
            </option>
          </select>
        </label>
        <div class="text-sm">
          <span class="mb-1 block font-semibold text-gray-700">Paciente no filtro</span>
          <div class="flex h-[38px] items-center justify-between rounded border border-gray-300 px-3">
            <span class="truncate text-gray-600">
              {{ store.pacienteChave ? (pacienteSelecionado?.pacienteNome ?? store.pacienteChave) : 'Todos os pacientes' }}
            </span>
            <button
              v-if="store.pacienteChave"
              type="button"
              class="ml-2 text-xs font-bold text-paper-primary hover:underline"
              @click="limparPaciente"
            >limpar</button>
          </div>
        </div>
      </div>

      <div class="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <div class="flex flex-wrap items-center gap-2">
          <input
            v-model="termoSolicitacao"
            type="search"
            class="campo max-w-xs"
            placeholder="Buscar solicitação (nome, prontuário, protocolo)"
            @keyup.enter="buscarSolicitacoes()"
          />
          <Button variant="secondary" @click="buscarSolicitacoes()">Buscar solicitação</Button>
          <span v-if="store.solicitacao" class="text-sm text-gray-700">
            Selecionada: <strong>{{ store.solicitacao.protocolo }}</strong> · {{ store.solicitacao.pacienteNome }}
          </span>
          <span v-else class="text-sm text-gray-500">Nenhuma solicitação selecionada</span>
        </div>
        <p v-if="!buscaFeita" class="mt-2 text-xs text-gray-500">
          A lista de solicitações aparece somente após a busca.
        </p>
        <p v-else-if="store.solicitacoes.length === 0 && !store.carregando" class="mt-2 text-xs text-gray-500">
          Nenhuma solicitação encontrada para o termo informado.
        </p>
        <div v-if="buscaFeita && store.solicitacoes.length > 0" class="mt-2 flex max-h-32 flex-wrap gap-2 overflow-y-auto">
          <button
            v-for="item in store.solicitacoes"
            :key="item.id"
            type="button"
            class="rounded border border-gray-300 bg-white px-2 py-1 text-left text-xs text-gray-700 hover:border-paper-primary hover:text-paper-primary"
            @click="selecionarSolicitacao(item.id)"
          >
            {{ item.protocolo }} · {{ item.pacienteNome }}
          </button>
        </div>
      </div>

      <p v-if="store.erro" class="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {{ store.erro }}
      </p>

      <div class="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
        <div class="xl:col-span-2">
          <div class="relative">
            <div v-if="store.carregando" class="absolute inset-0 z-10 flex items-center justify-center bg-white/60">
              <span class="rounded bg-white px-3 py-2 text-sm text-gray-600 shadow">Carregando agenda…</span>
            </div>
            <CalendarioAgendamentos
              ref="calendarioRef"
              :slots="store.slots"
              :agendamentos="store.agendamentos"
              :propostas="store.propostas"
              :readonly="!store.podeEditar"
              @periodo-alterado="store.definirPeriodo"
              @dia-selecionado="abrirDia"
              @slot-selecionado="store.selecionarSlot"
              @agendamento-selecionado="store.abrirAgendamento"
              @remarcar="aoRemarcar"
              @proposta-movida="moverProposta"
              @erro-slot="toast.error"
            />
          </div>
        </div>

        <div class="space-y-5">
          <PainelPropostas
            :propostas="store.propostas"
            :pode-editar="store.podeEditar"
            :ocupado="store.salvando"
            @gerar="gerarPropostas"
            @confirmar="confirmarProposta"
            @remarcar="remarcarProposta"
            @nao-confirmado="naoConfirmarProposta"
            @cancelar="cancelarProposta"
          />

          <Card>
            <template #header>
              <div>
                <h2 class="text-lg font-bold text-paper-text">Vagas do dia</h2>
                <p class="text-xs text-gray-500">
                  {{ store.diaSelecionado ? formatarData(store.diaSelecionado) : 'Clique em um dia no calendário' }}
                </p>
              </div>
            </template>
            <p v-if="!store.diaSelecionado" class="text-sm text-gray-500">
              Selecione uma data ou um horário no calendário para ver as vagas disponíveis.
            </p>
            <ul v-else class="max-h-80 space-y-2 overflow-y-auto">
              <li
                v-for="slot in store.slotsDoDia"
                :key="slot.id"
                class="rounded border p-2 text-sm"
                :class="slot.id === store.slotSelecionado?.id ? 'border-paper-primary bg-paper-primary/5' : 'border-gray-200'"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="font-semibold text-gray-800">{{ formatarHora(slot.inicio) }}–{{ formatarHora(slot.fim) }}</span>
                  <span class="rounded-full px-2 py-0.5 text-[11px] font-bold" :class="classeOcupacao(slot)">
                    {{ slot.livres }}/{{ slot.capacidade }} vagas
                  </span>
                </div>
                <p class="truncate text-xs text-gray-600">{{ slot.unidade }}</p>
                <p class="truncate text-xs text-gray-500">{{ slot.nomeExame }} · {{ slot.status }}</p>
                <div class="mt-1 flex gap-2">
                  <button type="button" class="text-xs font-semibold text-paper-primary hover:underline" @click="store.selecionarSlot(slot)">
                    Selecionar
                  </button>
                  <button
                    v-if="store.podeEditar && store.solicitacao && slot.livres > 0 && slot.status !== 'ENCERRADO'"
                    type="button"
                    class="text-xs font-semibold text-paper-success hover:underline"
                    @click="store.iniciarAgendamento(slot)"
                  >
                    Agendar aqui
                  </button>
                </div>
              </li>
              <li v-if="store.slotsDoDia.length === 0" class="text-sm text-gray-500">Nenhuma vaga cadastrada nesta data.</li>
            </ul>
            <div class="mt-3 border-t border-gray-200 pt-3">
              <Button variant="info" :disabled="!store.solicitacao" @click="store.abrirSugestoes">
                Ver sugestões para {{ store.solicitacao?.protocolo ?? 'a solicitação selecionada' }}
              </Button>
            </div>
          </Card>

          <PainelPaciente
            :pacientes="store.pacientes"
            :agendamentos="store.agendamentosPaciente"
            :paciente-chave="store.pacienteChave"
            :carregando="store.carregando"
            :pode-editar="store.podeEditar"
            @buscar="store.buscarPacientes"
            @selecionar="store.selecionarPaciente"
            @remarcar="store.iniciarRemarcacao"
            @cancelar="store.iniciarCancelamento"
            @sugestoes="sugerirParaAgendamento"
          />
        </div>
      </div>
    </Card>

    <ModalVagasDia
      :show="store.modalDia"
      :data="store.diaSelecionado"
      :slots="store.slotsDoDia"
      :solicitacao="store.solicitacao"
      :solicitacoes="store.solicitacoes"
      :selecionado-id="store.slotSelecionado?.id"
      :modo="store.modoPopup"
      :pode-editar="store.podeEditar"
      :ocupado="store.salvando"
      :erro="store.erro"
      @close="store.fecharDia"
      @buscar="buscarSolicitacoes"
      @selecionar="selecionarSolicitacao"
      @limpar="store.limparSolicitacao"
      @selecionar-slot="store.selecionarSlot"
      @marcar="store.marcarNoSlot"
    />

    <ModalSugestoes
      :show="store.modalSugestoes"
      :sugestoes="store.sugestoes"
      @close="store.modalSugestoes = false"
      @usar="store.usarSugestao"
    />

    <ModalRemarcacao
      :show="store.modalAcao"
      :modo="store.modoAcao"
      :slot="store.slotSelecionado"
      :agendamento="store.agendamentoSelecionado"
      :solicitacao="store.solicitacao"
      :salvando="store.salvando"
      @close="store.modalAcao = false"
      @confirmar="confirmarAcao"
    />

    <GestorVagas
      v-if="store.podeGerirVagas"
      :show="gestorVagasAberto"
      @close="gestorVagasAberto = false"
      @alterado="aoAlterarVagas"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import CalendarioAgendamentos from '../components/agendamentos/CalendarioAgendamentos.vue';
import GestorVagas from '../components/agendamentos/GestorVagas.vue';
import ModalRemarcacao from '../components/agendamentos/ModalRemarcacao.vue';
import ModalSugestoes from '../components/agendamentos/ModalSugestoes.vue';
import ModalVagasDia from '../components/agendamentos/ModalVagasDia.vue';
import PainelPaciente from '../components/agendamentos/PainelPaciente.vue';
import PainelPropostas from '../components/agendamentos/PainelPropostas.vue';
import { USAR_MOCKS } from '../config/mocks';
import { REFERENCIA_EM } from '../config/tempo';
import { useAgendamentosStore } from '../stores/agendamentos';
import type { AgendaSlot, Agendamento, PropostaAgendamentoFila } from '../types/sae';
import { formatarDataHora } from '../utils/format';

const store = useAgendamentosStore();
const route = useRoute();
const toast = useToast();
const termoSolicitacao = ref('');
const gestorVagasAberto = ref(false);
const buscaFeita = ref(false);
const calendarioRef = ref<{ irParaData: (dataIso: string) => void } | null>(null);

const pacienteSelecionado = computed(() =>
  store.pacientes.find((item) => item.pacienteChave === store.pacienteChave));

onMounted(() => {
  void store.carregar();
  const solicitacaoId = typeof route.query.solicitacao === 'string' ? route.query.solicitacao : '';
  const termo = typeof route.query.busca === 'string' ? route.query.busca : '';
  if (solicitacaoId) {
    termoSolicitacao.value = termo;
    buscaFeita.value = true;
    void store.buscarSolicitacoes(termo).then(() => selecionarSolicitacao(solicitacaoId));
  }
});

function formatarData(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
    .format(new Date(`${iso.slice(0, 10)}T12:00:00`));
}

function formatarHora(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
    .format(new Date(iso));
}

function classeOcupacao(slot: AgendaSlot): string {
  if (slot.status === 'ENCERRADO' || slot.livres === 0) return 'bg-red-100 text-red-800';
  if (slot.capacidade > 0 && slot.livres / slot.capacidade <= 0.4) return 'bg-amber-100 text-amber-800';
  return 'bg-emerald-100 text-emerald-800';
}

function buscarSolicitacoes(termo = termoSolicitacao.value.trim()): void {
  if (termo) termoSolicitacao.value = termo;
  buscaFeita.value = true;
  void store.buscarSolicitacoes(termo);
}

function abrirDia(data: string): void {
  store.abrirDia(data);
}

async function gerarPropostas(): Promise<void> {
  const resultado = await store.gerarPropostas(30);
  if (resultado) {
    toast.success(`${resultado.geradas} proposta(s) gerada(s) para ${resultado.dias} dias.`);
    if (resultado.deFora > 0) {
      toast.warning(`${resultado.deFora} solicitação(ões) não couberam nas vagas disponíveis.`);
    }
  } else {
    toast.error(store.erro || 'Não foi possível simular a agenda.');
  }
}

async function confirmarProposta(proposta: PropostaAgendamentoFila): Promise<void> {
  if (await store.confirmarProposta(proposta)) {
    calendarioRef.value?.irParaData(proposta.dataHora);
    toast.success('Proposta confirmada e agendamento efetivado.');
  } else {
    toast.error(store.erro || 'Não foi possível confirmar a proposta.');
  }
}

async function naoConfirmarProposta(proposta: PropostaAgendamentoFila): Promise<void> {
  const justificativa = window.prompt(
    'Motivo da não confirmação pelo paciente:',
    'Paciente não confirmou o horário proposto',
  );
  if (justificativa === null || !justificativa.trim()) return;
  if (await store.registrarNaoConfirmacao(proposta, justificativa)) {
    toast.info('Solicitação encaminhada para reagendamento.');
  } else {
    toast.error(store.erro || 'Não foi possível registrar a não confirmação.');
  }
}

async function remarcarProposta(proposta: PropostaAgendamentoFila): Promise<void> {
  await store.selecionarSolicitacao(proposta.solicitacaoId);
  store.abrirDia(proposta.dataHora, 'remarcar', store.agendamentoDaProposta(proposta));
}

function cancelarProposta(proposta: PropostaAgendamentoFila): void {
  store.iniciarCancelamento(store.agendamentoDaProposta(proposta));
}

function selecionarSolicitacao(id: string): void {
  void store.selecionarSolicitacao(id).then(() => {
    if (!store.erro) toast.info('Solicitação selecionada. Escolha uma vaga ou veja as sugestões.');
  });
}

async function moverProposta(proposta: PropostaAgendamentoFila, slot: AgendaSlot): Promise<void> {
  if (await store.moverProposta(proposta, slot)) {
    calendarioRef.value?.irParaData(slot.inicio);
    toast.success('Proposta movida para o novo horário.');
  } else {
    toast.error(store.erro || 'Não foi possível mover a proposta.');
  }
}

function aoRemarcar(agendamento: Agendamento, slot: AgendaSlot): void {
  store.iniciarRemarcacao(agendamento, slot);
}

function sugerirParaAgendamento(agendamento: Agendamento): void {
  void store.selecionarSolicitacao(agendamento.solicitacaoId).then(() => {
    void store.abrirSugestoes();
  });
}

async function confirmarAcao(justificativa: string): Promise<void> {
  const modo = store.modoAcao;
  const dataFoco = store.slotSelecionado?.inicio ?? '';
  const concluido = await store.confirmarAcao(justificativa);
  if (concluido) {
    if (modo !== 'cancelar') calendarioRef.value?.irParaData(dataFoco);
    if (modo === 'remarcar') toast.success('Agendamento remarcado com sucesso.');
    else if (modo === 'cancelar') toast.success('Agendamento cancelado com sucesso.');
    else toast.success('Agendamento efetivado com sucesso.');
    return;
  }
  const prefixo = store.erroStatus === 409
    ? 'Conflito de agenda: '
    : store.erroStatus === 422 ? 'Pré-condição não atendida: ' : '';
  toast.error(`${prefixo}${store.erro || 'Não foi possível concluir a operação.'}`);
}

function limparPaciente(): void {
  store.filtros.pacienteChave = '';
  store.pacienteChave = '';
  store.agendamentosPaciente = [];
  store.aoFiltrar();
}

function aoAlterarVagas(): void {
  toast.success('Agenda atualizada.');
  void store.carregar();
}
</script>

<style scoped>
.campo {
  width: 100%;
  border-radius: 0.25rem;
  border: 1px solid #d1d5db;
  padding: 0.45rem 0.6rem;
  font-size: 0.875rem;
}
</style>
