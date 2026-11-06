<template>
  <div class="space-y-6">
    <Card>
      <div class="mx-auto max-w-2xl text-center">
        <QrCodeIcon class="mx-auto h-10 w-10 text-paper-info" aria-hidden="true" />
        <h2 class="mt-2 text-xl font-bold text-gray-800">Ler etiqueta do AGHU</h2>
        <p class="mt-1 text-sm text-gray-500">Leia o código da etiqueta no frasco ou digite o número da solicitação e pressione Enter.</p>

        <Alert v-if="recepcao.aghuIndisponivel" variant="warning" title="Recepção bloqueada" class="mt-4 text-left">
          AGHU indisponível no momento. A recepção de novas amostras está bloqueada. O registro de material sem
          etiqueta continua disponível.
        </Alert>

        <form class="mt-5 flex flex-col gap-3 sm:flex-row" novalidate @submit.prevent="ler">
          <label for="recepcao-leitura" class="sr-only">Número da solicitação AGHU</label>
          <input
            id="recepcao-leitura"
            ref="campo"
            v-model="codigo"
            type="text"
            inputmode="numeric"
            autocomplete="off"
            placeholder="Leia ou digite o nº da solicitação AGHU"
            :disabled="recepcao.aghuIndisponivel"
            :aria-invalid="recepcao.mensagemLeitura ? 'true' : undefined"
            aria-describedby="recepcao-leitura-mensagem"
            :class="recepcao.mensagemLeitura ? 'border-2 border-paper-danger' : ''"
            class="form-control h-14 flex-1 text-center text-lg font-bold tracking-wider tabular-nums disabled:cursor-not-allowed disabled:bg-gray-100"
            @input="recepcao.mensagemLeitura = null"
          />
          <Button type="submit" class="h-14 sm:w-36" :loading="recepcao.lendo" :disabled="recepcao.aghuIndisponivel">
            Ler
          </Button>
        </form>

        <div id="recepcao-leitura-mensagem" aria-live="polite" class="text-left">
          <Alert v-if="recepcao.mensagemLeitura" variant="danger" class="mt-3">
            <p class="font-semibold">{{ recepcao.mensagemLeitura.texto }}</p>
            <p v-if="recepcao.mensagemLeitura.dica" class="mt-1">{{ recepcao.mensagemLeitura.dica }}</p>
            <router-link
              v-if="recepcao.mensagemLeitura.casoNumero"
              :to="rotaDoCaso(recepcao.mensagemLeitura.casoNumero)"
              class="focus-ring mt-2 inline-block rounded font-bold underline hover:no-underline active:opacity-70"
            >
              Abrir o caso {{ recepcao.mensagemLeitura.casoNumero }}
            </router-link>
          </Alert>
        </div>

        <div class="mt-6 border-t border-gray-100 pt-5">
          <Button variant="danger" @click="emit('sem-etiqueta')">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2" aria-hidden="true" />
            Material sem etiqueta do AGHU — registrar não conformidade
          </Button>
        </div>
      </div>
    </Card>

    <Card>
      <template #header>
        <div>
          <h2 class="text-lg font-bold text-gray-800">Solicitações do AGHU aguardando recebimento</h2>
          <p class="text-sm text-gray-500">Na rotina, a leitura da etiqueta abre a solicitação. A lista também permite abri-la manualmente.</p>
        </div>
      </template>
      <DataTable
        :headers="colunas"
        :items="linhas"
        :loading="recepcao.carregandoPendentes"
        :empty-text="recepcao.aghuIndisponivel ? 'Lista indisponível enquanto o AGHU estiver fora do ar.' : 'Nenhuma solicitação aguardando recebimento.'"
      >
        <template #cell-codigoSolicitacao="{ value }">
          <span class="font-bold tabular-nums text-gray-900">{{ value }}</span>
        </template>
        <template #cell-exame="{ item }">
          <Badge variant="primary" size="sm">{{ item.tipo }}</Badge>
          <span class="ml-2">{{ item.exame }}</span>
        </template>
        <template #actions="{ item }">
          <Button variant="outline" size="sm" :disabled="recepcao.aghuIndisponivel" @click="lerDaLista(item.codigoSolicitacao)">
            Ler etiqueta
          </Button>
        </template>
      </DataTable>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useToast } from 'vue-toastification';
import { ExclamationTriangleIcon, QrCodeIcon } from '@heroicons/vue/24/outline';
import Alert from '../../Alert.vue';
import Badge from '../../Badge.vue';
import Button from '../../Button.vue';
import Card from '../../Card.vue';
import DataTable from '../../DataTable.vue';
import { ORIGENS } from '../../../constants/ap';
import { formatarDataHora } from '../../../helpers/formato';
import { rotaDoCaso } from '../../../helpers/rotas';
import { mensagemDeErro } from '../../../services/ap';
import { useRecepcaoStore } from '../../../stores/recepcao';

const emit = defineEmits<{ (e: 'sem-etiqueta'): void }>();

const toast = useToast();
const recepcao = useRecepcaoStore();
const campo = ref<HTMLInputElement | null>(null);
const codigo = ref('');

const colunas = [
  { text: 'Nº AGHU', value: 'codigoSolicitacao' },
  { text: 'Exame', value: 'exame' },
  { text: 'Material', value: 'material' },
  { text: 'Origem', value: 'origem' },
  { text: 'Solicitação', value: 'data' },
];

const linhas = computed(() =>
  recepcao.pendentes.map((s) => ({
    id: s.codigoSolicitacao,
    codigoSolicitacao: s.codigoSolicitacao,
    tipo: s.tipoExameSugerido,
    exame: s.nomeExame,
    material: s.descricaoMaterial,
    origem: `${s.unidade} · ${ORIGENS[s.origem]}`,
    data: formatarDataHora(s.dataSolicitacao),
  })),
);

/** Lê o número digitado/lido. */
const ler = async () => {
  try {
    await recepcao.lerCodigo(codigo.value);
    if (recepcao.passo === 1) codigo.value = '';
  } catch (erro) {
    toast.error(mensagemDeErro(erro));
  }
};

/** "Ler etiqueta" na lista equivale a ler o número. */
const lerDaLista = async (numero: string) => {
  codigo.value = numero;
  await ler();
};

onMounted(async () => {
  await nextTick();
  campo.value?.focus();
});

defineExpose({ focar: () => campo.value?.focus() });
</script>
