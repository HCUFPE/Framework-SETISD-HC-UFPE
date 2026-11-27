<template>
  <Modal :show="show" largura="2xl" @close="emit('close')">
    <template #header>Disponibilidade de exames — gestão de vagas</template>

    <LoadingIndicator v-if="carregando" />
    <p v-if="erroLocal" class="mb-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ erroLocal }}</p>
    <p v-if="resultadoCopia" class="mb-3 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{{ resultadoCopia }}</p>

    <div class="mb-4">
      <span class="mb-1 block text-xs font-bold uppercase tracking-wide text-gray-500">Exame</span>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="opcao in opcoesExame"
          :key="opcao.codigo"
          type="button"
          class="rounded-full border px-3 py-1.5 text-left text-xs font-semibold transition-colors"
          :class="opcao.codigo === codigoSelecionado
            ? 'border-paper-primary bg-paper-primary text-white'
            : 'border-gray-300 bg-white text-gray-700 hover:border-paper-primary hover:text-paper-primary'"
          @click="selecionarExame(opcao.codigo)"
        >
          {{ opcao.nome }}
          <span v-if="opcao.codigo !== 'TODOS'" class="ml-1 opacity-70">({{ opcao.codigo }})</span>
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div>
        <CalendarioVagas
          :slots="slotsDoExame"
          :data-selecionada="diaSelecionado"
          @dia-selecionado="selecionarDia"
        />

        <div class="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
          <h3 class="text-sm font-bold text-gray-700">Copiar configurações de uma semana</h3>
          <div class="mt-2 flex flex-wrap items-end gap-2">
            <label class="text-xs font-semibold text-gray-600">
              Semana de origem
              <input v-model="copiarOrigem" type="date" class="campo mt-1 w-auto" aria-label="Semana de origem" />
            </label>
            <label class="text-xs font-semibold text-gray-600">
              Semana de destino
              <input v-model="copiarDestino" type="date" class="campo mt-1 w-auto" aria-label="Semana de destino" />
            </label>
            <Button variant="secondary" :loading="copiando" @click="copiarSemana">Copiar semana</Button>
          </div>
          <p class="mt-2 text-xs text-gray-500">
            Copia as vagas do exame selecionado (ou de todos) mantendo dia da semana, horário,
            unidade, capacidade e situação. Vagas que já existem no destino são ignoradas.
          </p>
        </div>
      </div>

      <div class="space-y-4">
        <div class="rounded-lg border border-gray-200 p-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-sm font-bold text-gray-700">Vagas de {{ formatarData(diaSelecionado) }}</h3>
            <span class="text-xs text-gray-500">{{ slotsDoDia.length }} vaga(s)</span>
          </div>

          <p v-if="!diaSelecionado" class="mt-2 text-sm text-gray-500">
            Selecione um dia no calendário para ver e acrescentar vagas.
          </p>
          <ul v-else class="mt-2 max-h-64 space-y-2 overflow-y-auto">
            <li
              v-for="slot in slotsDoDia"
              :key="slot.id"
              class="rounded border border-gray-200 p-2 text-xs"
            >
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="font-bold text-gray-800">
                  {{ formatarHora(slot.inicio) }}–{{ formatarHora(slot.fim) }}
                </span>
                <span class="rounded-full bg-gray-100 px-2 py-0.5 font-semibold text-gray-600">
                  {{ slot.livres }}/{{ slot.capacidade }} · {{ slot.status }}
                </span>
              </div>
              <p class="mt-1 text-gray-600">{{ slot.unidade }} · {{ slot.nomeExame }} ({{ slot.codigoExame }})</p>
              <div class="mt-2 flex flex-wrap gap-2">
                <button type="button" class="font-bold text-paper-primary hover:underline" @click="editar(slot)">Editar</button>
                <button type="button" class="font-bold text-red-600 hover:underline" @click="remover(slot)">Remover</button>
              </div>

              <div v-if="selecionadoId === slot.id" class="mt-2 rounded bg-gray-50 p-2">
                <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  <label class="text-xs font-semibold text-gray-600">Unidade
                    <input v-model="edicao.unidade" class="campo mt-1" />
                  </label>
                  <label class="text-xs font-semibold text-gray-600">Código do exame
                    <input v-model="edicao.codigoExame" class="campo mt-1" />
                  </label>
                  <label class="text-xs font-semibold text-gray-600 sm:col-span-2">Nome do exame
                    <input v-model="edicao.nomeExame" class="campo mt-1" />
                  </label>
                  <label class="text-xs font-semibold text-gray-600">Início
                    <input v-model="edicao.inicio" type="datetime-local" class="campo mt-1" />
                  </label>
                  <label class="text-xs font-semibold text-gray-600">Fim
                    <input v-model="edicao.fim" type="datetime-local" class="campo mt-1" />
                  </label>
                  <label class="text-xs font-semibold text-gray-600">Capacidade
                    <input v-model.number="edicao.capacidade" type="number" min="1" class="campo mt-1" />
                  </label>
                  <label class="text-xs font-semibold text-gray-600">Situação
                    <select v-model="edicao.status" class="campo mt-1">
                      <option value="DISPONIVEL">Disponível</option>
                      <option value="LOTADO">Lotada</option>
                      <option value="ENCERRADO">Encerrada</option>
                    </select>
                  </label>
                </div>
                <div class="mt-2 flex justify-end gap-2">
                  <Button variant="secondary" @click="selecionadoId = ''">Cancelar</Button>
                  <Button variant="primary" :loading="salvandoItem === slot.id" @click="salvar(String(slot.id))">Salvar alterações</Button>
                </div>
              </div>
            </li>
            <li v-if="!slotsDoDia.length" class="rounded border border-dashed border-gray-300 p-3 text-gray-500">
              Nenhuma vaga cadastrada nesta data para o exame selecionado.
            </li>
          </ul>
        </div>

        <div class="rounded-lg border border-gray-200 bg-paper-primary/5 p-3">
          <h3 class="text-sm font-bold text-gray-700">Acrescentar vaga em {{ formatarData(diaSelecionado) }}</h3>
          <div class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <label class="text-xs font-semibold text-gray-600">Unidade
              <input v-model="novo.unidade" class="campo mt-1" list="unidades-vaga" />
            </label>
            <datalist id="unidades-vaga">
              <option v-for="unidade in unidades" :key="unidade" :value="unidade" />
            </datalist>
            <template v-if="codigoSelecionado === 'TODOS'">
              <label class="text-xs font-semibold text-gray-600">Código do exame
                <input v-model="novo.codigoExame" class="campo mt-1" />
              </label>
              <label class="text-xs font-semibold text-gray-600">Nome do exame
                <input v-model="novo.nomeExame" class="campo mt-1" />
              </label>
            </template>
            <p v-else class="text-xs text-gray-600 sm:col-span-2">
              Exame: <strong>{{ nomeExameSelecionado }}</strong> ({{ codigoSelecionado }})
            </p>
            <label class="text-xs font-semibold text-gray-600">Início
              <input v-model="novo.inicio" type="datetime-local" class="campo mt-1" />
            </label>
            <label class="text-xs font-semibold text-gray-600">Fim
              <input v-model="novo.fim" type="datetime-local" class="campo mt-1" />
            </label>
            <label class="text-xs font-semibold text-gray-600">Capacidade
              <input v-model.number="novo.capacidade" type="number" min="1" class="campo mt-1" />
            </label>
            <label class="text-xs font-semibold text-gray-600">Situação
              <select v-model="novo.situacao" class="campo mt-1">
                <option value="DISPONIVEL">Disponível</option>
                <option value="LOTADO">Lotada</option>
                <option value="ENCERRADO">Encerrada</option>
              </select>
            </label>
          </div>
          <div class="mt-3 flex justify-end">
            <Button variant="primary" :disabled="!diaSelecionado" :loading="salvando" @click="criar">Acrescentar vaga</Button>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import Button from '../Button.vue';
import CalendarioVagas from './CalendarioVagas.vue';
import LoadingIndicator from '../LoadingIndicator.vue';
import Modal from '../Modal.vue';
import { agoraIso } from '../../config/tempo';
import {
  atualizarSlotAdmin,
  copiarSemanaAdmin,
  criarSlotAdmin,
  listarSlotsAdmin,
  removerSlotAdmin,
  type DadosNovoSlot,
} from '../../services/sae';
import { diaLocal, paraApiIso, paraInputLocal } from '../../utils/datetime';
import { useAuthStore } from '../../stores/auth';
import type { AgendaSlot } from '../../types/sae';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{ close: []; alterado: [] }>();

const auth = useAuthStore();
const slots = ref<AgendaSlot[]>([]);
const carregando = ref(false);
const salvando = ref(false);
const salvandoItem = ref('');
const copiando = ref(false);
const erroLocal = ref('');
const resultadoCopia = ref('');
const codigoSelecionado = ref('TODOS');
const diaSelecionado = ref(agoraIso().slice(0, 10));
const copiarOrigem = ref('');
const copiarDestino = ref('');
const selecionadoId = ref('');

const novo = ref<DadosNovoSlot>({
  unidade: '', codigoExame: '', nomeExame: '', inicio: '', fim: '', capacidade: 3,
  situacao: 'DISPONIVEL',
});

const edicao = reactive({
  unidade: '',
  codigoExame: '',
  nomeExame: '',
  inicio: '',
  fim: '',
  capacidade: 3,
  status: 'DISPONIVEL' as AgendaSlot['status'],
});

interface OpcaoExame {
  codigo: string;
  nome: string;
}

const opcoesExame = computed<OpcaoExame[]>(() => {
  const porCodigo = new Map<string, string>();
  slots.value.forEach((slot) => {
    if (slot.codigoExame) porCodigo.set(slot.codigoExame, slot.nomeExame);
  });
  return [
    { codigo: 'TODOS', nome: 'Todos os exames' },
    ...Array.from(porCodigo, ([codigo, nome]) => ({ codigo, nome }))
      .sort((a, b) => a.nome.localeCompare(b.nome)),
  ];
});

const nomeExameSelecionado = computed(() =>
  opcoesExame.value.find((exame) => exame.codigo === codigoSelecionado.value)?.nome ?? '');

const slotsDoExame = computed(() => codigoSelecionado.value === 'TODOS'
  ? slots.value
  : slots.value.filter((slot) => slot.codigoExame === codigoSelecionado.value));

const slotsDoDia = computed(() => slotsDoExame.value
  .filter((slot) => diaLocal(slot.inicio) === diaSelecionado.value)
  .sort((a, b) => a.inicio.localeCompare(b.inicio) || a.unidade.localeCompare(b.unidade)));

const unidades = computed(() => Array.from(
  new Set(slotsDoExame.value.map((slot) => slot.unidade)),
).sort());

function autor(): string {
  return auth.user?.displayName?.[0] ?? auth.user?.username ?? 'Operador';
}

function mensagem(erro: unknown): string {
  const candidato = erro as { response?: { data?: { detail?: string } }; message?: string };
  return candidato?.response?.data?.detail ?? candidato?.message ?? 'Não foi possível concluir a operação.';
}

function dois(valor: number): string {
  return String(valor).padStart(2, '0');
}

function dataIso(data: Date): string {
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
}

function formatarData(iso: string): string {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
    .format(new Date(`${diaLocal(iso)}T12:00:00`));
}

function formatarHora(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
    .format(new Date(iso));
}

function inicioSemana(data: string): Date {
  const dia = new Date(`${data.slice(0, 10)}T12:00:00`);
  dia.setDate(dia.getDate() - ((dia.getDay() + 6) % 7));
  dia.setHours(12, 0, 0, 0);
  return dia;
}

function selecionarExame(codigo: string): void {
  codigoSelecionado.value = codigo;
  selecionadoId.value = '';
  novo.value.codigoExame = codigo === 'TODOS' ? '' : codigo;
  novo.value.nomeExame = codigo === 'TODOS' ? '' : nomeExameSelecionado.value;
}

function selecionarDia(data: string): void {
  diaSelecionado.value = data.slice(0, 10);
  selecionadoId.value = '';
  const horaInicio = novo.value.inicio.slice(11, 16) || '08:00';
  const horaFim = novo.value.fim.slice(11, 16) || '10:00';
  novo.value.inicio = `${diaSelecionado.value}T${horaInicio}`;
  novo.value.fim = `${diaSelecionado.value}T${horaFim}`;
  if (codigoSelecionado.value !== 'TODOS') {
    novo.value.codigoExame = codigoSelecionado.value;
    novo.value.nomeExame = nomeExameSelecionado.value;
  }
  if (!novo.value.unidade && unidades.value.length) novo.value.unidade = unidades.value[0];
}

async function carregar(): Promise<void> {
  carregando.value = true;
  erroLocal.value = '';
  try {
    slots.value = await listarSlotsAdmin();
    selecionadoId.value = '';
    if (!copiarOrigem.value) copiarOrigem.value = dataIso(inicioSemana(diaSelecionado.value));
    if (!copiarDestino.value) {
      const proxima = inicioSemana(diaSelecionado.value);
      proxima.setDate(proxima.getDate() + 7);
      copiarDestino.value = dataIso(proxima);
    }
    if (codigoSelecionado.value !== 'TODOS'
      && !opcoesExame.value.some((exame) => exame.codigo === codigoSelecionado.value)) {
      selecionarExame('TODOS');
    }
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    carregando.value = false;
  }
}

watch(() => props.show, (aberto) => {
  if (aberto) void carregar();
});

function editar(slot: AgendaSlot): void {
  selecionadoId.value = slot.id;
  Object.assign(edicao, {
    unidade: slot.unidade,
    codigoExame: slot.codigoExame,
    nomeExame: slot.nomeExame,
    // O input datetime-local trabalha na hora local; a API devolve UTC.
    inicio: paraInputLocal(slot.inicio),
    fim: paraInputLocal(slot.fim),
    capacidade: slot.capacidade,
    status: slot.status,
  });
}

async function criar(): Promise<void> {
  if (!diaSelecionado.value) {
    erroLocal.value = 'Selecione um dia no calendário antes de acrescentar a vaga.';
    return;
  }
  salvando.value = true;
  erroLocal.value = '';
  try {
    const inicioLocal = `${diaSelecionado.value}T${novo.value.inicio.slice(11, 16) || '08:00'}`;
    const fimLocal = `${diaSelecionado.value}T${novo.value.fim.slice(11, 16) || '10:00'}`;
    await criarSlotAdmin({
      ...novo.value,
      inicio: paraApiIso(inicioLocal),
      fim: paraApiIso(fimLocal),
    }, autor());
    await carregar();
    emit('alterado');
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    salvando.value = false;
  }
}

async function salvar(id: string): Promise<void> {
  salvandoItem.value = id;
  erroLocal.value = '';
  try {
    await atualizarSlotAdmin(id, {
      ...edicao,
      inicio: paraApiIso(edicao.inicio),
      fim: paraApiIso(edicao.fim),
    }, autor());
    selecionadoId.value = '';
    await carregar();
    emit('alterado');
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    salvandoItem.value = '';
  }
}

async function remover(slot: AgendaSlot): Promise<void> {
  if (!window.confirm(`Remover a vaga de ${formatarHora(slot.inicio)} (${slot.unidade})?`)) return;
  erroLocal.value = '';
  try {
    await removerSlotAdmin(slot.id, autor());
    if (selecionadoId.value === slot.id) selecionadoId.value = '';
    await carregar();
    emit('alterado');
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  }
}

async function copiarSemana(): Promise<void> {
  if (!copiarOrigem.value || !copiarDestino.value) {
    erroLocal.value = 'Informe a semana de origem e a semana de destino.';
    return;
  }
  copiando.value = true;
  erroLocal.value = '';
  resultadoCopia.value = '';
  try {
    const resultado = await copiarSemanaAdmin({
      origem: dataIso(inicioSemana(copiarOrigem.value)),
      destino: dataIso(inicioSemana(copiarDestino.value)),
      codigoExame: codigoSelecionado.value === 'TODOS' ? undefined : codigoSelecionado.value,
    }, autor());
    await carregar();
    resultadoCopia.value = `${resultado.criadas.length} vaga(s) copiada(s) para a semana de ${resultado.destino}; ${resultado.ignoradas} já existiam.`;
    if (resultado.criadas.length) emit('alterado');
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    copiando.value = false;
  }
}
</script>

<style scoped>
.campo {
  width: 100%;
  border-radius: 0.25rem;
  border: 1px solid #d1d5db;
  padding: 0.4rem 0.6rem;
  font-size: 0.875rem;
}
</style>
