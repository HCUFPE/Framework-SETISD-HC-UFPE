<template>
  <Card v-if="recepcao.resultados.length">
    <div class="mx-auto max-w-2xl text-center">
      <CheckCircleIcon class="mx-auto h-14 w-14 text-paper-success" aria-hidden="true" />
      <h2 class="mt-2 text-lg font-bold text-gray-800">Conferência confirmada · solicitação {{ solicitacaoCodigo }}</h2>
      <p class="text-sm text-gray-600">
        {{ recepcao.resultados.length === 1 ? 'Foi gerado 1 registro.' : `Foram gerados ${recepcao.resultados.length} registros, um por tipo de exame.` }}
      </p>

      <div class="mt-5 space-y-4">
        <ItemResultado
          v-for="resultado in recepcao.resultados"
          :key="resultado.tipo === 'IHQ' ? resultado.ihq.codigoInternoIhq : resultado.caso.numeroInterno"
          :resultado="resultado"
        />
      </div>

      <Alert variant="warning" class="mt-5 text-left">
        <strong>Lembrete:</strong> registrar o recebimento no AGHU (solicitação {{ solicitacaoCodigo }}).
      </Alert>

      <Alert v-if="recepcao.outrosExamesPendentes.length" variant="info" title="Exames que ficaram para depois" class="mt-4 text-left">
        A solicitação {{ solicitacaoCodigo }} ainda tem
        <strong>{{ recepcao.outrosExamesPendentes.map((e) => `${e.tipoExameSugerido} (${rotuloNumerosAmostras(e.amostras)})`).join(', ') }}</strong>
        aguardando recebimento.
      </Alert>

      <div class="mt-6 flex justify-center">
        <Button @click="emit('proxima')">
          <ArrowPathIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Receber próxima amostra
        </Button>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ArrowPathIcon, CheckCircleIcon } from '@heroicons/vue/24/outline';
import Alert from '../../Alert.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import ItemResultado from './ItemResultado.vue';
import { rotuloNumerosAmostras } from '../../../helpers/aghu';
import { useRecepcaoStore } from '../../../stores/recepcao';

const emit = defineEmits<{ (e: 'proxima'): void }>();

const recepcao = useRecepcaoStore();
const solicitacaoCodigo = computed(() => recepcao.solicitacao?.codigoSolicitacao ?? '');
</script>
