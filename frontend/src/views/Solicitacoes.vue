<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="space-y-1">
        <h2 class="text-3xl font-bold text-slate-900">Solicitacoes de Vaga</h2>
      </div>
      <div class="flex flex-wrap gap-3">
        <UiButton variant="outline" size="sm" class="shadow-sm">
          <CalendarIcon class="h-5 w-5 text-slate-600" />
          Filtrar Data
        </UiButton>
        <UiButton size="sm" class="shadow-sm">
          <PlusIcon class="h-5 w-5 text-white" />
          Nova Solicitacao
        </UiButton>
      </div>
    </div>

    <div class="grid gap-4">
      <article
        v-for="sol in solicitacoes"
        :key="sol.id"
        class="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <header class="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Prontuario</p>
            <p class="text-lg font-semibold text-slate-900">{{ sol.prontuario }}</p>
            <p class="mt-1 text-sm text-slate-600">
              {{ sol.idade }} anos
              <span class="text-slate-400">•</span>
              {{ sol.especialidade }}
            </p>
          </div>
          <UiBadge :class="statusClass[sol.status]">
            {{ sol.status }}
          </UiBadge>
        </header>

        <div class="px-5 py-4">
          <div class="grid gap-4 sm:grid-cols-3">
            <div>
              <p class="text-xs uppercase tracking-wide text-slate-500">Tipo</p>
              <p class="mt-1 font-medium text-slate-900">{{ sol.tipo }}</p>
            </div>
            <div>
              <p class="text-xs uppercase tracking-wide text-slate-500">Turno</p>
              <p class="mt-1 font-medium text-slate-900">{{ sol.turno }}</p>
            </div>
            <div>
              <p class="text-xs uppercase tracking-wide text-slate-500">Destino</p>
              <p class="mt-1 font-medium text-slate-900">
                {{ sol.destino ?? 'Pendente' }}
              </p>
            </div>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <UiButton
              v-if="sol.status === 'Pendente'"
              size="sm"
            >
              Reservar Leito
            </UiButton>
            <UiButton
              v-if="sol.status === 'Pendente'"
              size="sm"
              variant="destructive"
            >
              Cancelar Solicitacao
            </UiButton>
            <UiButton
              v-else-if="sol.status === 'Reservado'"
              size="sm"
              variant="outline"
            >
              Cancelar Reserva
            </UiButton>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { CalendarIcon, PlusIcon } from '@heroicons/vue/24/outline';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';

type SolicitacaoStatus = 'Pendente' | 'Reservado';

type Solicitacao = {
  id: string;
  prontuario: string;
  idade: number;
  especialidade: string;
  tipo: string;
  status: SolicitacaoStatus;
  turno: string;
  destino?: string;
};

const solicitacoes: Solicitacao[] = [
  {
    id: '1',
    prontuario: '123456',
    idade: 67,
    especialidade: 'Cardiologia',
    tipo: 'Cirurgico',
    status: 'Pendente',
    turno: 'Manha',
  },
  {
    id: '2',
    prontuario: '789012',
    idade: 45,
    especialidade: 'Oncologia',
    tipo: 'HEM',
    status: 'Reservado',
    destino: 'Leito 05',
    turno: 'Tarde',
  },
  {
    id: '3',
    prontuario: '345678',
    idade: 29,
    especialidade: 'Obstetricia',
    tipo: 'Obstetrico',
    status: 'Pendente',
    turno: 'Noite',
  },
];

const statusClass: Record<SolicitacaoStatus, string> = {
  Pendente: 'border-rose-300 bg-rose-500/80 text-rose-100',
  Reservado: 'border-emerald-300 bg-emerald-500/80 text-emerald-100',
};
</script>
