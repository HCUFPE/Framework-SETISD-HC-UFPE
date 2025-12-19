<template>
  <section class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-3xl font-bold text-slate-900">Indicadores Operacionais</h2>
    </div>

    <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
      <article
        v-for="indicador in indicadores"
        :key="indicador.titulo"
        class="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <header class="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <p class="text-sm font-medium text-slate-600">{{ indicador.titulo }}</p>
          <div class="rounded-lg bg-blue-50 p-2">
            <component :is="indicador.icone" class="h-5 w-5 text-blue-600" />
          </div>
        </header>
        <div class="px-5 py-4">
          <div class="space-y-2">
            <div>
              <p class="text-4xl font-bold text-slate-900">{{ indicador.valor }}</p>
              <p class="mt-1 text-sm text-slate-600">{{ indicador.subtitulo }}</p>
            </div>
            <p class="border-t pt-2 text-xs text-slate-500">
              {{ indicador.tendencia }}
            </p>
          </div>
        </div>
      </article>
    </div>

    <article class="rounded-xl border border-slate-200 bg-white shadow-sm">
      <header class="border-b border-slate-100 px-5 py-4">
        <h3 class="text-lg font-semibold text-slate-900">Grafico de Ocupacao Semanal</h3>
      </header>
      <div class="flex h-64 items-center justify-center bg-slate-50 text-slate-500">
        Grafico de linha sera implementado aqui
      </div>
    </article>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <article class="rounded-xl border border-slate-200 bg-white shadow-sm">
        <header class="border-b border-slate-100 px-5 py-4">
          <h3 class="text-lg font-semibold text-slate-900">Distribuicao por Especialidade</h3>
        </header>
        <div class="flex h-64 items-center justify-center bg-slate-50 text-slate-500">
          Grafico de pizza sera implementado aqui
        </div>
      </article>

      <article class="rounded-xl border border-slate-200 bg-white shadow-sm">
        <header class="border-b border-slate-100 px-5 py-4">
          <h3 class="text-lg font-semibold text-slate-900">Tempo de Espera (UTI Fechada)</h3>
        </header>
        <div class="flex h-64 items-center justify-center bg-slate-50 text-slate-500">
          Grafico de barras sera implementado aqui
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import {
  UsersIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  CalendarDaysIcon,
} from '@heroicons/vue/24/outline';

type Indicador = {
  titulo: string;
  valor: string;
  subtitulo: string;
  icone: any;
  tendencia: string;
};

const indicadores: Indicador[] = [
  {
    titulo: 'Internacoes Semanais (Media)',
    valor: '42',
    subtitulo: 'internacoes/semana',
    icone: UsersIcon,
    tendencia: '+8% vs semana anterior',
  },
  {
    titulo: 'Tempo Medio de Ocupacao',
    valor: '5.2',
    subtitulo: 'dias',
    icone: ClockIcon,
    tendencia: '-0.3 dias vs mes anterior',
  },
  {
    titulo: 'Taxa de Atendimento',
    valor: '87%',
    subtitulo: 'das solicitacoes',
    icone: CheckCircleIcon,
    tendencia: '+5% vs mes anterior',
  },
  {
    titulo: 'Taxa de Cancelamento',
    valor: '13%',
    subtitulo: 'das solicitacoes',
    icone: XCircleIcon,
    tendencia: '-2% vs mes anterior',
  },
  {
    titulo: 'Tempo Solicitacao -> Ocupacao',
    valor: '3.8h',
    subtitulo: 'tempo medio',
    icone: ArrowTrendingUpIcon,
    tendencia: '-0.5h vs mes anterior',
  },
  {
    titulo: 'Horario Medio de Reservas',
    valor: '14:30',
    subtitulo: 'hora pico: tarde',
    icone: CalendarDaysIcon,
    tendencia: 'Consistente',
  },
];
</script>
