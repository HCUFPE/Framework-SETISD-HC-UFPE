<template>
  <div class="space-y-5">
    <Card>
      <template #header>
        <div class="flex items-start gap-3">
          <ArrowPathIcon class="h-7 w-7 shrink-0 text-paper-text" />
          <div>
            <h1 class="text-2xl font-bold text-paper-text">Integração Microsoft Forms → AGHUX</h1>
            <p class="mt-1 max-w-3xl text-sm leading-relaxed text-gray-600">
              Cada resposta do formulário chega por webhook com assinatura HMAC; quando o envio não está disponível,
              o agendador faz uma busca híbrida (pull) e cruza os dados com o AGHUX para apontar divergências e alertas
              antes de entrar na fila de marcação.
            </p>
          </div>
        </div>
      </template>

      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-xs text-gray-500">Acompanhe os últimos eventos processados e reprocesse falhas e duplicidades.</p>
        <Button variant="secondary" :loading="store.carregando" @click="store.listar()">Atualizar eventos</Button>
      </div>
    </Card>

    <Card>
      <template #header>
        <div class="flex items-center gap-2">
          <DocumentTextIcon class="h-6 w-6 text-gray-500" />
          <h2 class="text-lg font-bold text-paper-text">Eventos de integração</h2>
        </div>
      </template>

      <p v-if="store.erro" class="mb-4 flex items-start gap-2 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        <ExclamationTriangleIcon class="mt-0.5 h-4 w-4 shrink-0" />
        <span>{{ store.erro }}</span>
        <Button variant="secondary" @click="store.listar()">Tentar novamente</Button>
      </p>
      <p v-if="store.mensagem" class="mb-4 flex items-start gap-2 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
        <CheckCircleIcon class="mt-0.5 h-4 w-4 shrink-0" />
        <span>{{ store.mensagem }}</span>
      </p>

      <div v-if="store.carregando" class="flex flex-col items-center justify-center gap-3 py-12 text-sm text-gray-500">
        <div class="h-8 w-8 animate-spin rounded-full border-b-4 border-t-4 border-paper-primary"></div>
        <span>Carregando eventos de integração...</span>
      </div>

      <div v-else-if="store.eventos.length === 0" class="flex flex-col items-center justify-center gap-2 py-12 text-center text-sm text-gray-500">
        <InboxIcon class="h-10 w-10 text-gray-300" />
        <p class="font-semibold text-gray-600">Nenhum evento recebido</p>
        <p>Os eventos do Microsoft Forms aparecerão aqui após o primeiro envio.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th class="px-3 py-2">Response ID</th>
              <th class="px-3 py-2">Formulário</th>
              <th class="px-3 py-2">Status</th>
              <th class="px-3 py-2 text-center">Tentativas</th>
              <th class="px-3 py-2">Recebido em</th>
              <th class="px-3 py-2">Processado em</th>
              <th class="px-3 py-2">Último erro</th>
              <th class="px-3 py-2 text-center">Divergências</th>
              <th class="px-3 py-2 text-center">Alertas</th>
              <th class="px-3 py-2 text-right">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="evento in store.eventos" :key="evento.responseId" class="bg-white">
              <td class="px-3 py-2 font-mono text-xs text-gray-800">{{ evento.responseId }}</td>
              <td class="px-3 py-2 text-gray-600">{{ evento.formId }}</td>
              <td class="px-3 py-2">
                <span :class="classesStatus[evento.status]" class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold">
                  {{ evento.status }}
                </span>
              </td>
              <td class="px-3 py-2 text-center text-gray-600">{{ evento.tentativas }}</td>
              <td class="px-3 py-2 text-gray-600">{{ formatarIso(evento.recebidoEm) }}</td>
              <td class="px-3 py-2 text-gray-600">{{ formatarIso(evento.processadoEm) }}</td>
              <td class="max-w-xs px-3 py-2 text-xs text-red-600">{{ evento.ultimoErro ?? '—' }}</td>
              <td class="px-3 py-2 text-center text-gray-600">{{ evento.divergencias }}</td>
              <td class="px-3 py-2 text-center text-gray-600">{{ evento.alertas }}</td>
              <td class="px-3 py-2 text-right">
                <Button
                  variant="warning"
                  :disabled="!podeReprocessar(evento.status) || store.reprocessandoId === evento.responseId"
                  :loading="store.reprocessandoId === evento.responseId"
                  @click="reprocessar(evento.responseId)"
                >
                  Reprocessar
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useToast } from 'vue-toastification';
import { ArrowPathIcon, CheckCircleIcon, DocumentTextIcon, ExclamationTriangleIcon, InboxIcon } from '@heroicons/vue/24/outline';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import { useIntegracoesStore } from '../stores/integracoes';
import type { StatusFormsEvento } from '../types/sae';
import { formatarDataHora } from '../utils/format';

const store = useIntegracoesStore();
const toast = useToast();

const classesStatus: Record<StatusFormsEvento, string> = {
  PENDENTE: 'bg-amber-100 text-amber-800',
  PROCESSADA: 'bg-emerald-100 text-emerald-800',
  DUPLICADA: 'bg-indigo-100 text-indigo-800',
  ERRO: 'bg-red-100 text-red-800',
};

function formatarIso(iso: string | null): string {
  return iso ? formatarDataHora(iso) : '—';
}

function podeReprocessar(status: StatusFormsEvento): boolean {
  return status === 'ERRO' || status === 'DUPLICADA';
}

async function reprocessar(responseId: string): Promise<void> {
  const status = await store.reprocessar(responseId);
  if (status) {
    toast.success(`Evento ${responseId} reprocessado: ${status}.`);
  } else {
    toast.error(store.erro || 'Não foi possível reprocessar o evento.');
  }
}

onMounted(() => {
  void store.listar();
});
</script>
