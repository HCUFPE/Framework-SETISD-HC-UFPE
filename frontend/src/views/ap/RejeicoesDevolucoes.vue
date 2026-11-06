<template>
  <div class="space-y-4">
    <p class="text-sm text-gray-600">
      Materiais devolvidos por não conformidade: rejeições na recepção (sem caso aberto) e devoluções de casos, com o
      acompanhamento da resolução.
    </p>

    <Card>
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label for="dev-periodo" class="form-label">Período</label>
          <select id="dev-periodo" v-model.number="filtros.periodoDias" class="form-control">
            <option :value="0">Qualquer data</option>
            <option :value="7">Últimos 7 dias</option>
            <option :value="30">Últimos 30 dias</option>
          </select>
        </div>
        <div>
          <label for="dev-natureza" class="form-label">Natureza</label>
          <select id="dev-natureza" v-model="filtros.natureza" class="form-control">
            <option value="">Todas</option>
            <option value="REJEICAO">Rejeição na recepção</option>
            <option value="DEVOLUCAO">Devolução de caso</option>
          </select>
        </div>
        <div>
          <label for="dev-tipo" class="form-label">Tipo de não conformidade</label>
          <select id="dev-tipo" v-model="filtros.tipo" class="form-control">
            <option value="">Todos</option>
            <option v-for="(rotulo, codigo) in TIPOS_NAO_CONFORMIDADE" :key="codigo" :value="codigo">{{ rotulo }}</option>
          </select>
        </div>
        <div>
          <label for="dev-origem" class="form-label">Origem</label>
          <select id="dev-origem" v-model="filtros.origem" class="form-control">
            <option value="">Todas</option>
            <option v-for="origem in origens" :key="origem" :value="origem">{{ origem }}</option>
          </select>
        </div>
        <div>
          <label for="dev-etapa" class="form-label">Etapa identificada</label>
          <select id="dev-etapa" v-model="filtros.etapa" class="form-control">
            <option value="">Todas</option>
            <option v-for="etapa in etapas" :key="etapa" :value="etapa">{{ ETAPAS[etapa] }}</option>
          </select>
        </div>
        <p class="ml-auto self-center text-sm text-gray-500" aria-live="polite">{{ filtradas.length }} registro(s)</p>
      </div>

      <div class="mt-4">
        <DataTable
          :key="assinaturaFiltros"
          :headers="colunas"
          :items="linhas"
          :page-size="10"
          :loading="store.carregando"
          empty-text="Nenhuma devolução para os filtros selecionados."
        >
          <template #cell-natureza="{ item }">
            <Badge :variant="item.rejeicao ? 'warning' : 'info'" size="sm">
              {{ item.rejeicao ? 'Rejeição na recepção' : 'Devolução de caso' }}
            </Badge>
          </template>
          <template #cell-tipo="{ item }">
            <span class="block font-bold text-gray-800">{{ item.tipo }}</span>
            <span class="block max-w-xs text-xs text-gray-500">{{ item.descricao }}</span>
          </template>
          <template #cell-origem="{ item }">
            <span class="block">{{ item.origem }}</span>
            <span class="block text-xs text-gray-500">Identificada em: {{ item.etapa }}</span>
          </template>
          <template #cell-caso="{ item }">
            <router-link
              v-if="item.casoNumero"
              :to="rotaDoCaso(item.casoNumero)"
              class="focus-ring whitespace-nowrap rounded font-bold text-paper-primary-strong underline-offset-2 hover:underline active:opacity-70"
            >
              {{ item.casoNumero }}
            </router-link>
            <span v-else-if="item.solicitacaoCodigo" class="whitespace-nowrap text-gray-600">AGHU {{ item.solicitacaoCodigo }}</span>
            <span v-else class="text-gray-500">Sem etiqueta do AGHU</span>
          </template>
          <template #cell-pessoas="{ item }">
            <span class="block">{{ item.devolvidoPor }}</span>
            <span class="block text-xs text-gray-500">Recebido por {{ item.recebidoPor }}</span>
          </template>
          <template #cell-situacao="{ item }">
            <label :for="`situacao-${item.id}`" class="sr-only">Situação da devolução {{ item.id }}</label>
            <select
              :id="`situacao-${item.id}`"
              :value="item.situacao"
              :disabled="salvando === item.id"
              class="form-control min-w-48 py-1 text-sm"
              @change="alterarSituacao(item.id, ($event.target as HTMLSelectElement).value as SituacaoDevolucao)"
            >
              <option v-for="(info, codigo) in SITUACOES_DEVOLUCAO" :key="codigo" :value="codigo">{{ info.rotulo }}</option>
            </select>
          </template>
        </DataTable>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useToast } from 'vue-toastification';
import Badge from '../../components/Badge.vue';
import Card from '../../components/Card.vue';
import DataTable from '../../components/DataTable.vue';
import { ETAPAS, SITUACOES_DEVOLUCAO, TIPOS_NAO_CONFORMIDADE } from '../../constants/ap';
import { formatarDataHora } from '../../helpers/formato';
import { rotaDoCaso } from '../../helpers/rotas';
import { mensagemDeErro } from '../../services/ap';
import { useDevolucoesStore } from '../../stores/devolucoes';
import type { EtapaCodigo, SituacaoDevolucao, TipoNaoConformidadeCodigo } from '../../types/ap';

const toast = useToast();
const store = useDevolucoesStore();
const salvando = ref<number | null>(null);

const filtros = reactive({
  periodoDias: 0,
  natureza: '' as '' | 'REJEICAO' | 'DEVOLUCAO',
  tipo: '' as '' | TipoNaoConformidadeCodigo,
  origem: '',
  etapa: '' as '' | EtapaCodigo,
});

const colunas = [
  { text: 'Data/hora', value: 'data' },
  { text: 'Natureza', value: 'natureza' },
  { text: 'Tipo e detalhamento', value: 'tipo' },
  { text: 'Origem / etapa', value: 'origem' },
  { text: 'Caso', value: 'caso' },
  { text: 'Devolvido / recebido por', value: 'pessoas' },
  { text: 'Nova amostra', value: 'novaAmostra' },
  { text: 'Situação', value: 'situacao' },
];

const origens = computed(() => [...new Set(store.devolucoes.map((d) => d.unidadeOrigem))].sort());
const etapas = computed(() => [...new Set(store.devolucoes.map((d) => d.naoConformidade.etapaCodigo))]);

/** Devoluções que atendem aos filtros (a lista já vem da mais recente para a mais antiga). */
const filtradas = computed(() => {
  const limite = filtros.periodoDias > 0 ? Date.now() - filtros.periodoDias * 86_400_000 : null;
  return store.devolucoes.filter((d) => {
    if (limite !== null && new Date(d.devolvidaEm).getTime() < limite) return false;
    if (filtros.natureza === 'REJEICAO' && !d.rejeicaoNaRecepcao) return false;
    if (filtros.natureza === 'DEVOLUCAO' && d.rejeicaoNaRecepcao) return false;
    if (filtros.tipo && d.naoConformidade.tipo !== filtros.tipo) return false;
    if (filtros.origem && d.unidadeOrigem !== filtros.origem) return false;
    if (filtros.etapa && d.naoConformidade.etapaCodigo !== filtros.etapa) return false;
    return true;
  });
});

const linhas = computed(() =>
  filtradas.value.map((d) => ({
    id: d.id,
    data: formatarDataHora(d.devolvidaEm),
    rejeicao: d.rejeicaoNaRecepcao,
    tipo: TIPOS_NAO_CONFORMIDADE[d.naoConformidade.tipo],
    descricao: d.naoConformidade.descricao,
    origem: d.unidadeOrigem,
    etapa: d.naoConformidade.etapa,
    casoNumero: d.casoNumero,
    solicitacaoCodigo: d.solicitacaoCodigo,
    devolvidoPor: d.devolvidoPor.nome,
    recebidoPor: d.recebidoPorNome,
    novaAmostra: d.novaAmostraSolicitada ? 'Sim' : 'Não',
    situacao: d.situacao,
  })),
);

/** Muda a cada alteração de filtro e recria a tabela, voltando à primeira página. */
const assinaturaFiltros = computed(() => JSON.stringify(filtros));

const alterarSituacao = async (id: number, situacao: SituacaoDevolucao) => {
  salvando.value = id;
  try {
    await store.atualizarSituacao(id, situacao);
    toast.success(`Situação atualizada para "${SITUACOES_DEVOLUCAO[situacao].rotulo}".`);
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível atualizar a situação.'));
    await store.carregar();
  } finally {
    salvando.value = null;
  }
};

onMounted(() => {
  store.carregar();
});
</script>
