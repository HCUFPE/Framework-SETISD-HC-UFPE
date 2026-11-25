<template>
  <Modal :show="show" @close="emit('close')">
    <template #header>Gestão de vagas da agenda</template>

    <LoadingIndicator v-if="carregando" />
    <p v-if="erroLocal" class="mb-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ erroLocal }}</p>

    <div class="rounded-lg border border-gray-200 p-3">
      <h3 class="mb-2 text-sm font-bold text-gray-700">Nova vaga</h3>
      <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <input v-model="novo.unidade" placeholder="Unidade" class="campo" list="unidades-vaga" />
        <datalist id="unidades-vaga">
          <option v-for="unidade in unidades" :key="unidade" :value="unidade" />
        </datalist>
        <input v-model="novo.codigoExame" placeholder="Código do exame" class="campo" />
        <input v-model="novo.nomeExame" placeholder="Nome do exame" class="campo" />
        <input v-model="novo.inicio" type="datetime-local" class="campo" />
        <input v-model="novo.fim" type="datetime-local" class="campo" />
        <input v-model.number="novo.capacidade" type="number" min="1" class="campo" placeholder="Capacidade" />
      </div>
      <div class="mt-3 flex justify-end">
        <Button variant="primary" :loading="salvando" @click="criar">Criar vaga</Button>
      </div>
    </div>

    <div class="mt-4">
      <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 class="text-sm font-bold text-gray-700">Vagas cadastradas</h3>
        <input v-model="diaFiltro" type="date" class="campo w-auto" aria-label="Filtrar vagas por data" />
      </div>
      <DataTable :headers="colunas" :items="slotsDoDia">
        <template #actions="{ item }">
          <div class="flex items-center gap-1">
            <input
              type="number"
              min="1"
              class="w-16 rounded border border-gray-300 px-1 py-1 text-xs"
              :value="capacidadeAjustada(String(item.id), Number(item.capacidade))"
              @change="definirCapacidade(String(item.id), $event)"
            />
            <select
              class="rounded border border-gray-300 px-1 py-1 text-xs"
              :value="situacaoAjustada(String(item.id), String(item.status))"
              @change="definirSituacao(String(item.id), $event)"
            >
              <option value="DISPONIVEL">Disponível</option>
              <option value="LOTADO">Lotada</option>
              <option value="ENCERRADO">Encerrada</option>
            </select>
            <Button variant="info" :loading="salvandoItem === String(item.id)" @click="salvar(String(item.id))">Salvar</Button>
          </div>
        </template>
      </DataTable>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import Button from '../Button.vue';
import DataTable from '../DataTable.vue';
import LoadingIndicator from '../LoadingIndicator.vue';
import Modal from '../Modal.vue';
import { agoraIso } from '../../config/tempo';
import { listarSlotsAdmin, criarSlotAdmin, atualizarSlotAdmin, type DadosNovoSlot } from '../../services/sae';
import { useAuthStore } from '../../stores/auth';
import type { AgendaSlot } from '../../types/sae';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{ close: []; alterado: [] }>();

const auth = useAuthStore();
const slots = ref<AgendaSlot[]>([]);
const carregando = ref(false);
const salvando = ref(false);
const salvandoItem = ref('');
const erroLocal = ref('');
const diaFiltro = ref(agoraIso().slice(0, 10));
const ajustes = ref<Record<string, { capacidade: number; status: AgendaSlot['status'] }>>({});

const novo = ref<DadosNovoSlot>({
  unidade: '', codigoExame: '', nomeExame: '', inicio: '', fim: '', capacidade: 3,
});

const colunas = [
  { text: 'Início', value: 'inicio' },
  { text: 'Unidade', value: 'unidade' },
  { text: 'Exame', value: 'nomeExame' },
  { text: 'Cap.', value: 'capacidade' },
  { text: 'Ocup.', value: 'ocupadas' },
  { text: 'Situação', value: 'status' },
];

const unidades = computed(() => Array.from(new Set(slots.value.map((slot) => slot.unidade))).sort());
const slotsDoDia = computed(() => {
  const itens = diaFiltro.value
    ? slots.value.filter((slot) => slot.inicio.slice(0, 10) === diaFiltro.value)
    : slots.value;
  return itens.slice(0, 60);
});

function autor(): string {
  return auth.user?.displayName?.[0] ?? auth.user?.username ?? 'Operador';
}

function mensagem(erro: unknown): string {
  const candidato = erro as { response?: { data?: { detail?: string } }; message?: string };
  return candidato?.response?.data?.detail ?? candidato?.message ?? 'Não foi possível concluir a operação.';
}

async function carregar(): Promise<void> {
  carregando.value = true;
  erroLocal.value = '';
  try {
    slots.value = await listarSlotsAdmin();
    ajustes.value = {};
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    carregando.value = false;
  }
}

watch(() => props.show, (aberto) => {
  if (aberto) void carregar();
});

function capacidadeAjustada(id: string, atual: number): number {
  return ajustes.value[id]?.capacidade ?? atual;
}

function situacaoAjustada(id: string, atual: string): AgendaSlot['status'] {
  return ajustes.value[id]?.status ?? (atual as AgendaSlot['status']);
}

function definirCapacidade(id: string, evento: Event): void {
  const slot = slots.value.find((item) => item.id === id);
  if (!slot) return;
  ajustes.value[id] = {
    capacidade: Number((evento.target as HTMLInputElement).value),
    status: ajustes.value[id]?.status ?? slot.status,
  };
}

function definirSituacao(id: string, evento: Event): void {
  const slot = slots.value.find((item) => item.id === id);
  if (!slot) return;
  ajustes.value[id] = {
    capacidade: ajustes.value[id]?.capacidade ?? slot.capacidade,
    status: (evento.target as HTMLSelectElement).value as AgendaSlot['status'],
  };
}

async function criar(): Promise<void> {
  salvando.value = true;
  erroLocal.value = '';
  try {
    await criarSlotAdmin({ ...novo.value }, autor());
    novo.value = { unidade: '', codigoExame: '', nomeExame: '', inicio: '', fim: '', capacidade: 3 };
    await carregar();
    emit('alterado');
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    salvando.value = false;
  }
}

async function salvar(id: string): Promise<void> {
  const ajuste = ajustes.value[id];
  if (!ajuste) return;
  salvandoItem.value = id;
  erroLocal.value = '';
  try {
    await atualizarSlotAdmin(id, ajuste, autor());
    await carregar();
    emit('alterado');
  } catch (erro) {
    erroLocal.value = mensagem(erro);
  } finally {
    salvandoItem.value = '';
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
