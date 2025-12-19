<template>
  <section class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">Solicitacoes de Alta</h2>
      </div>
    </div>

    <div class="grid gap-4">
      <article
        v-for="alta in altas"
        :key="alta.id"
        class="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <header class="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Prontuario</p>
            <p class="text-lg font-semibold text-slate-900">{{ alta.prontuario }}</p>
            <div class="mt-2 flex items-center gap-2 text-sm text-slate-600">
              <ClockIcon class="h-4 w-4" />
              <span>{{ alta.dataHora }}</span>
            </div>
          </div>
          <UiBadge :class="alta.leitoDestino.includes('Pendente') ? badgeClasses.pendente : badgeClasses.definido">
            {{ alta.leitoDestino.includes('Pendente') ? 'Aguardando NIR' : 'Destino Definido' }}
          </UiBadge>
        </header>

        <div class="px-5 py-4">
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex-1">
              <p class="text-xs uppercase tracking-wide text-slate-500">Leito Atual</p>
              <p class="text-xl font-bold text-slate-900">Leito {{ alta.leitoAtual }}</p>
            </div>
            <ArrowRightIcon class="h-5 w-5 text-slate-400" />
            <div class="flex-1">
              <p class="text-xs uppercase tracking-wide text-slate-500">Destino</p>
              <p class="font-semibold text-slate-900">{{ alta.leitoDestino }}</p>
            </div>
          </div>

          <div
            v-if="alta.necessidadesEspeciais"
            class="mt-4 border-l-4 border-blue-500 pl-3"
          >
            <p class="text-sm font-medium text-slate-700">Necessidades Especiais</p>
            <p class="mt-1 text-sm text-slate-600">{{ alta.necessidadesEspeciais }}</p>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <template v-if="alta.leitoDestino.includes('Pendente')">
              <UiButton size="sm">
                Indicar Necessidades Especiais
              </UiButton>
              <UiButton size="sm" variant="destructive">
                Cancelar Alta
              </UiButton>
            </template>
            <template v-else>
              <UiButton size="sm">
                Confirmar Transferencia
              </UiButton>
              <UiButton size="sm" variant="outline">
                Alterar Destino
              </UiButton>
              <UiButton size="sm" variant="destructive">
                Cancelar Alta
              </UiButton>
            </template>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ClockIcon, ArrowRightIcon } from '@heroicons/vue/24/outline';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';

type Alta = {
  id: string;
  prontuario: string;
  leitoAtual: string;
  leitoDestino: string;
  dataHora: string;
  necessidadesEspeciais?: string;
};

const altas: Alta[] = [
  {
    id: '1',
    prontuario: '456789',
    leitoAtual: '03',
    leitoDestino: 'Pendente (NIR)',
    dataHora: '2025-11-18 08:30',
    necessidadesEspeciais: 'Oxigenio portatil',
  },
  {
    id: '2',
    prontuario: '234567',
    leitoAtual: '07',
    leitoDestino: 'Enfermaria 2B - Leito 12',
    dataHora: '2025-11-18 10:15',
    necessidadesEspeciais: '',
  },
  {
    id: '3',
    prontuario: '890123',
    leitoAtual: '11',
    leitoDestino: 'Pendente (NIR)',
    dataHora: '2025-11-18 14:00',
    necessidadesEspeciais: 'Isolamento de contato',
  },
];

const badgeClasses = {
  pendente: 'border-amber-300 bg-amber-500/70 text-amber-800',
  definido: 'border-emerald-300 bg-emerald-500/80 text-emerald-100',
};
</script>
