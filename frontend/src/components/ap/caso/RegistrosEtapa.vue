<template>
  <div>
    <p class="mb-3 inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-xs font-bold text-gray-600">
      <LockClosedIcon class="h-3.5 w-3.5" aria-hidden="true" /> Somente leitura neste fluxo
    </p>
    <p v-if="registros.length === 0" class="rounded-md border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
      {{ vazio }}
    </p>
    <div v-else class="space-y-4">
      <article v-for="(registro, i) in registros" :key="i" class="rounded-lg border border-gray-200 p-4">
        <header class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h3 class="font-bold text-gray-800">{{ registro.titulo }}</h3>
          <p class="text-xs text-gray-500">{{ registro.responsavel.nome }} · {{ formatarDataHora(registro.registradoEm) }}</p>
        </header>
        <dl class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="campo in registro.campos" :key="campo.rotulo">
            <dt class="text-xs font-bold uppercase text-gray-500">{{ campo.rotulo }}</dt>
            <dd class="text-sm text-gray-800">{{ campo.valor }}</dd>
          </div>
        </dl>
        <p v-if="registro.texto" class="mt-3 whitespace-pre-line rounded-md bg-gray-50 p-3 text-sm text-gray-800">{{ registro.texto }}</p>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LockClosedIcon } from '@heroicons/vue/24/outline';
import { formatarDataHora } from '../../../helpers/formato';
import type { RegistroEtapa } from '../../../types/ap';

/** Registros de etapas posteriores à recepção (dados mockados, somente leitura). */
defineProps<{ registros: RegistroEtapa[]; vazio: string }>();
</script>
