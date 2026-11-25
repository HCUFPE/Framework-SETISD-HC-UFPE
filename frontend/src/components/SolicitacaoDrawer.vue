<template>
  <Teleport to="body">
    <div v-if="solicitacao" class="fixed inset-0 z-50 flex justify-end">
      <div class="absolute inset-0 bg-gray-900/50" @click="emit('close')"></div>
      <aside class="relative h-full w-full max-w-3xl overflow-y-auto bg-paper-bg shadow-2xl">
        <header class="sticky top-0 z-10 flex items-start justify-between border-b border-gray-200 bg-white px-6 py-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ solicitacao.protocolo }}</p>
            <h2 class="text-xl font-bold text-paper-text">{{ solicitacao.pacienteNome }}</h2>
            <p class="mt-1 text-sm text-gray-500">
              Solicitação AGHUX {{ solicitacao.codigoSolicitacaoAghux }} · prontuário {{ solicitacao.prontuario }}
            </p>
            <p class="text-sm text-gray-500">
              {{ solicitacao.setorSolicitante }} · solicitante {{ solicitacao.solicitanteNome }} ({{ solicitacao.solicitanteCodigo }})
            </p>
          </div>
          <button class="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700" aria-label="Fechar painel" @click="emit('close')">
            <XMarkIcon class="h-6 w-6" />
          </button>
        </header>

        <div v-if="erro" class="mx-6 mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ erro }}</div>

        <div class="space-y-6 px-6 py-5">
          <section class="flex flex-wrap items-center gap-2">
            <PriorityBadge :prioridade="solicitacao.prioridade" />
            <StatusBadge :status="solicitacao.status" />
            <DivergenciaBadge :quantidade="divergenciasPendentes.length" />
            <span class="text-xs text-gray-500">Pontuação {{ solicitacao.pontuacao }} · recebida em {{ formatarDataHora(solicitacao.recebidaEm) }}</span>
          </section>

          <section class="rounded-lg bg-white p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-paper-text">Exames solicitados ({{ solicitacao.itensExame.length }})</h3>
            <ul class="space-y-2">
              <li v-for="item in solicitacao.itensExame" :key="item.codigoExame" class="rounded border border-gray-200 p-2 text-sm">
                <span class="font-mono text-xs text-paper-primary">{{ item.codigoExame }}</span>
                <span class="ml-2 text-gray-700">{{ item.nomeExame }}</span>
              </li>
            </ul>
            <p class="mt-3 text-xs text-gray-500">
              Contato: {{ solicitacao.telefone }} · {{ solicitacao.cidade }}/{{ solicitacao.estado }}
            </p>
          </section>

          <section class="rounded-lg bg-white p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-paper-text">Dados cadastrados no AGHUX</h3>
            <dl class="grid grid-cols-1 gap-x-6 gap-y-2 text-sm md:grid-cols-2">
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Nome</dt><dd class="text-gray-800">{{ solicitacao.pacienteNome }}</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Prontuário</dt><dd class="text-gray-800">{{ solicitacao.prontuario }}</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Telefone</dt><dd class="text-gray-800">{{ solicitacao.telefone }}</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Cidade / UF</dt><dd class="text-gray-800">{{ solicitacao.cidade }}/{{ solicitacao.estado }}</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Unidade solicitante</dt><dd class="text-gray-800">{{ solicitacao.setorSolicitante }}</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Solicitante</dt><dd class="text-gray-800">{{ solicitacao.solicitanteNome }} ({{ solicitacao.solicitanteCodigo }})</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Data da solicitação</dt><dd class="text-gray-800">{{ formatarDataHora(solicitacao.recebidaEm) }}</dd></div>
              <div><dt class="text-xs uppercase tracking-wide text-gray-500">Exames</dt><dd class="text-gray-800">{{ solicitacao.itensExame.map((item) => item.nomeExame).join(', ') }}</dd></div>
            </dl>
            <p class="mt-3 text-xs text-gray-500">
              Somente dados presentes no export AGHUX. CPF/CNS e endereço não constam na fonte e não foram inventados.
            </p>
          </section>

          <section v-if="divergenciasPendentes.length" class="rounded-lg border border-red-200 bg-red-50 p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-red-800">
              Divergências apontadas ({{ divergenciasPendentes.length }} pendente(s))
            </h3>
            <ul class="space-y-2">
              <li v-for="divergencia in divergenciasPendentes" :key="divergencia.id" class="rounded border border-red-200 bg-white p-2 text-sm">
                <strong class="text-gray-700">{{ divergencia.campo }}</strong>
                <p class="mt-1 text-gray-600">Formulário: {{ divergencia.valorFormulario }} · AGHUX: {{ divergencia.valorAghux }}</p>
                <p class="mt-1 text-xs italic text-gray-500">Trate a divergência ou justifique antes de validar.</p>
              </li>
            </ul>
          </section>

          <section v-if="solicitacao.alertas.length" class="rounded-lg border border-amber-200 bg-amber-50 p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-amber-800">Alertas</h3>
            <ul class="space-y-2">
              <li v-for="alerta in solicitacao.alertas" :key="alerta.id" class="rounded border border-amber-200 bg-white p-2 text-sm text-amber-800">
                <strong>{{ alerta.campo }}:</strong> {{ alerta.mensagem }} ({{ alerta.severidade }})
              </li>
            </ul>
          </section>

          <section v-if="podeEditar" class="rounded-lg bg-white p-5 shadow-paper">
            <h3 class="mb-4 font-semibold text-paper-text">Ações do operador (assinatura eletrônica)</h3>
            <div class="space-y-4">
              <div>
                <label class="form-label" for="justificativa">Justificativa da validação</label>
                <textarea id="justificativa" v-model="justificativa" class="form-control" rows="2" placeholder="Obrigatória quando houver divergência pendente"></textarea>
                <Button variant="primary" class="mt-2" :loading="ocupado" @click="emit('validar', justificativa)">Corrigir e validar</Button>
              </div>

              <div class="border-t border-gray-100 pt-4">
                <label class="form-label" for="resultado-contato">Retorno do contato com o paciente</label>
                <div class="flex flex-col gap-2 md:flex-row">
                  <select id="resultado-contato" v-model="resultado" class="form-control">
                    <option value="ACEITE">Aceite</option>
                    <option value="RECUSA">Recusa</option>
                    <option value="SEM_RESPOSTA">Sem resposta</option>
                  </select>
                  <input v-model="observacao" class="form-control" placeholder="Observação do contato" />
                  <Button variant="info" :loading="ocupado" @click="emit('contato', resultado, observacao)">Registrar contato</Button>
                </div>
              </div>

              <div class="border-t border-gray-100 pt-4">
                <p class="mb-2 text-sm text-gray-700">
                  Encaminhe o paciente com os dados já preenchidos para a fila de agendamento.
                </p>
                <Button variant="success" :loading="ocupado" @click="emit('efetuar-marcacao', solicitacao)">
                  Efetuar marcação
                </Button>
              </div>
            </div>
          </section>

          <section class="rounded-lg bg-white p-5 shadow-paper">
            <h3 class="mb-3 font-semibold text-paper-text">Histórico e auditoria</h3>
            <HistoryTimeline :eventos="solicitacao.historico" />
          </section>
        </div>
      </aside>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import Button from './Button.vue';
import DivergenciaBadge from './DivergenciaBadge.vue';
import HistoryTimeline from './HistoryTimeline.vue';
import PriorityBadge from './PriorityBadge.vue';
import StatusBadge from './StatusBadge.vue';
import { formatarDataHora } from '../utils/format';
import type { ResultadoContato, Solicitacao } from '../types/sae';

const props = defineProps<{ solicitacao: Solicitacao | null; podeEditar: boolean; erro?: string; ocupado?: boolean }>();

/** A seção de divergências só aparece enquanto houver pendências a tratar. */
const divergenciasPendentes = computed(() =>
  props.solicitacao?.divergencias.filter((divergencia) => !divergencia.tratada) ?? []);

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'validar', justificativa: string): void;
  (e: 'contato', resultado: ResultadoContato, observacao: string): void;
  (e: 'efetuar-marcacao', solicitacao: Solicitacao): void;
}>();

const justificativa = ref('');
const observacao = ref('');
const resultado = ref<ResultadoContato>('ACEITE');

watch(() => props.solicitacao?.id, () => {
  justificativa.value = '';
  observacao.value = '';
  resultado.value = 'ACEITE';
}, { immediate: true });
</script>
