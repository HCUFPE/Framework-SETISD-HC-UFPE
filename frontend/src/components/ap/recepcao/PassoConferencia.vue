<template>
  <div v-if="recepcao.solicitacao" class="grid gap-6 lg:grid-cols-3">
    <Card class="lg:col-span-2">
      <template #header>
        <h2 class="text-lg font-bold text-gray-800">Dados da solicitação</h2>
      </template>
      <DadosSolicitacao :solicitacao="recepcao.solicitacao" />
    </Card>

    <div class="lg:sticky lg:top-28 self-start">
      <Card>
        <template #header>
          <h2 class="text-lg font-bold text-gray-800">Conferência</h2>
          <p class="text-sm text-gray-500">Compare a amostra física e a requisição em papel com os dados do AGHU.</p>
        </template>

        <fieldset>
          <legend class="sr-only">Itens da conferência</legend>
          <div class="space-y-2">
            <label
              v-for="item in ITENS_CONFERENCIA"
              :key="item.chave"
              :class="recepcao.conferencia[item.chave] ? 'border-paper-success bg-paper-success-soft' : 'border-gray-200 bg-white hover:bg-gray-50'"
              class="flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm font-semibold text-gray-800 transition active:bg-gray-100"
            >
              <input
                v-model="recepcao.conferencia[item.chave]"
                type="checkbox"
                class="focus-ring mt-0.5 h-5 w-5 shrink-0 rounded accent-[var(--color-paper-success)]"
                @change="tentouAvancar = false"
              />
              {{ item.rotulo }}
            </label>
          </div>
        </fieldset>

        <Alert v-if="tentouAvancar && !recepcao.conferenciaCompleta" variant="danger" class="mt-4">
          Marque todos os itens da conferência. Se algo não confere, registre uma não conformidade.
        </Alert>

        <div class="mt-5 flex flex-col gap-2">
          <Button @click="confirmar">
            <CheckCircleIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Confirmar conferência
          </Button>
          <Button variant="danger" @click="emit('nao-conformidade')">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Registrar não conformidade
          </Button>
          <button
            type="button"
            class="focus-ring self-center rounded px-2 py-1 text-sm font-semibold text-paper-primary-strong underline-offset-2 transition hover:underline active:opacity-70"
            @click="recepcao.reiniciar()"
          >
            Ler outra etiqueta
          </button>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import Alert from '../../Alert.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import DadosSolicitacao from '../DadosSolicitacao.vue';
import { ITENS_CONFERENCIA } from '../../../constants/ap';
import { useRecepcaoStore } from '../../../stores/recepcao';

const emit = defineEmits<{ (e: 'nao-conformidade'): void }>();

const recepcao = useRecepcaoStore();
const tentouAvancar = ref(false);

const confirmar = () => {
  tentouAvancar.value = true;
  recepcao.confirmarConferencia();
};
</script>
