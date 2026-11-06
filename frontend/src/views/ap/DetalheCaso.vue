<template>
  <div class="space-y-4">
    <router-link
      to="/casos"
      class="focus-ring inline-flex items-center gap-1 rounded text-sm font-semibold text-paper-primary-strong hover:underline active:opacity-70"
    >
      <ArrowLeftIcon class="h-4 w-4" aria-hidden="true" /> Consulta de casos
    </router-link>

    <Card v-if="carregando && !caso">
      <p class="py-8 text-center text-gray-500" role="status">Carregando caso...</p>
    </Card>

    <!-- Caso inexistente -->
    <Card v-else-if="!caso">
      <div class="py-8 text-center">
        <DocumentMagnifyingGlassIcon class="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
        <h2 class="mt-2 text-xl font-bold text-gray-800">Caso não encontrado</h2>
        <p class="mt-1 text-sm text-gray-500">Não existe caso com o número {{ numero }}.</p>
        <router-link
          to="/casos"
          class="focus-ring mt-4 inline-flex items-center rounded bg-paper-primary px-4 py-2 font-bold text-white transition hover:bg-paper-primary-hover active:bg-paper-primary-strong"
        >
          Voltar à Consulta de casos
        </router-link>
      </div>
    </Card>

    <template v-else>
      <!-- Cabeçalho -->
      <Card>
        <!-- Número, selos e ações na mesma linha; as ações quebram para baixo só sem espaço -->
        <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
          <div class="flex min-w-0 flex-wrap items-center gap-2">
            <h2 class="text-3xl font-extrabold tracking-tight text-gray-900 tabular-nums">{{ caso.numeroInterno }}</h2>
            <button
              type="button"
              class="focus-ring rounded-md p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-800 active:bg-gray-200 active:scale-95"
              :aria-label="`Copiar ${caso.numeroInterno}`"
              title="Copiar número"
              @click="copiar"
            >
              <ClipboardDocumentIcon class="h-5 w-5" />
            </button>
            <StatusCasoBadge :status="caso.status" size="md" />
            <span v-if="caso.urgente" class="group relative">
              <span
                tabindex="0"
                aria-describedby="motivo-urgencia"
                class="focus-ring inline-flex cursor-help items-center rounded-md bg-paper-danger-soft px-2.5 py-1 text-sm font-bold text-paper-danger-strong"
              >
                URGENTE
              </span>
              <span
                id="motivo-urgencia"
                role="tooltip"
                class="invisible absolute left-0 top-full z-20 mt-1 w-64 rounded-md bg-gray-900 px-3 py-2 text-xs font-semibold text-white opacity-0 shadow-lg transition group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100"
              >
                Motivo da urgência: {{ caso.motivoUrgencia }}
              </span>
            </span>
          </div>

          <!-- Ações: Não conformidade, Cancelar caso, Imprimir -->
          <div class="flex flex-wrap gap-2">
            <Button v-if="ativo" variant="danger" @click="ncAberta = true">
              <ExclamationTriangleIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Não conformidade
            </Button>
            <Button v-if="ativo" variant="secondary" @click="cancelamentoAberto = true">
              <XCircleIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Cancelar caso
            </Button>
            <div class="relative">
              <Button variant="outline" :aria-expanded="menuImpressao" aria-haspopup="menu" @click="menuImpressao = !menuImpressao">
                <PrinterIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Imprimir
                <ChevronDownIcon class="h-4 w-4 ml-1" aria-hidden="true" />
              </Button>
              <div v-if="menuImpressao" class="fixed inset-0 z-10" @click="menuImpressao = false"></div>
              <div
                v-if="menuImpressao"
                role="menu"
                class="absolute right-0 z-20 mt-1 w-56 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg"
              >
                <button
                  v-for="opcao in opcoesImpressao"
                  :key="opcao.tipo"
                  type="button"
                  role="menuitem"
                  class="focus-ring [--focus-ring-offset:-2px] block w-full px-4 py-2.5 text-left text-sm font-semibold text-gray-700 transition hover:bg-gray-50 active:bg-gray-100"
                  @click="imprimir(opcao.tipo)"
                >
                  {{ opcao.rotulo }}
                </button>
              </div>
            </div>
          </div>
        </div>
        <p class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
          <span><strong>{{ caso.tipoExame }}</strong> · {{ TIPOS_EXAME[caso.tipoExame].nome }}</span>
          <span>{{ caso.solicitacao.nomePaciente }} · Pront. {{ caso.solicitacao.prontuario }}</span>
          <span>Material: {{ caso.solicitacao.descricaoMaterial }}</span>
          <span>Entrada: {{ formatarDataHora(caso.dataEntradaSap) }}</span>
        </p>

        <!-- Faixa de bloqueio -->
        <div
          v-if="textoBloqueio"
          class="mt-4 flex items-center gap-2 rounded-md border border-gray-300 bg-gray-100 px-4 py-3 text-sm font-semibold text-gray-700"
          role="status"
        >
          <LockClosedIcon class="h-5 w-5 shrink-0" aria-hidden="true" />
          {{ textoBloqueio }}
        </div>

        <div class="mt-5 border-t border-gray-100 pt-5">
          <FluxoCaso :caso="caso" />
        </div>
      </Card>

      <!-- Abas -->
      <Card>
        <Tabs v-model="aba" :tabs="abas">
          <template #resumo>
            <div class="grid gap-6 lg:grid-cols-3">
              <div class="lg:col-span-2">
                <dl class="grid gap-4 sm:grid-cols-2">
                  <div v-for="campo in camposResumo" :key="campo.rotulo">
                    <dt class="text-xs font-bold uppercase text-gray-500">{{ campo.rotulo }}</dt>
                    <dd class="text-sm font-semibold text-gray-800">
                      {{ campo.valor }}
                      <Badge v-if="campo.alerta" variant="warning" size="sm" class="ml-1">{{ campo.alerta }}</Badge>
                    </dd>
                  </div>
                </dl>
                <div class="mt-5 rounded-lg border border-paper-info/40 bg-paper-info-soft p-4">
                  <p class="text-xs font-bold uppercase text-paper-info-strong">Informações clínicas (AGHU)</p>
                  <p class="mt-1 text-sm text-gray-800">{{ caso.solicitacao.informacoesClinicas || 'Não informadas.' }}</p>
                </div>
              </div>
              <div>
                <h3 class="mb-2 font-bold text-gray-800">Últimas movimentações</h3>
                <ol class="space-y-2">
                  <li v-for="evento in historicoOrdenado.slice(0, 5)" :key="evento.id" class="border-l-2 border-paper-primary pl-3">
                    <p class="text-sm font-semibold text-gray-800">{{ evento.titulo }}</p>
                    <p class="text-xs text-gray-500">{{ formatarDataHora(evento.ocorridoEm) }} · {{ evento.usuario.nome }}</p>
                  </li>
                </ol>
                <button
                  type="button"
                  class="focus-ring mt-3 rounded text-sm font-semibold text-paper-primary-strong hover:underline active:opacity-70"
                  @click="aba = 'historico'"
                >
                  Ver histórico completo
                </button>
              </div>
            </div>
          </template>

          <template #aghu>
            <DadosSolicitacao :solicitacao="caso.solicitacao" />
          </template>

          <template #recepcao>
            <dl class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div v-for="campo in camposRecepcao" :key="campo.rotulo" :class="campo.largo ? 'sm:col-span-2' : ''">
                <dt class="text-xs font-bold uppercase text-gray-500">{{ campo.rotulo }}</dt>
                <dd class="text-sm font-semibold text-gray-800">{{ campo.valor }}</dd>
              </div>
            </dl>
            <div class="mt-5 rounded-lg border border-gray-200 p-4">
              <div class="mb-3 flex flex-wrap items-center gap-2">
                <h3 class="font-bold text-gray-800">Conferência de recebimento</h3>
                <Badge v-if="caso.conferencia" :variant="caso.conferencia.resultado === 'ACEITA' ? 'success' : 'danger'" size="sm">
                  {{ RESULTADOS_CONFERENCIA[caso.conferencia.resultado] }}
                </Badge>
              </div>
              <template v-if="caso.conferencia">
                <ul class="grid gap-2 sm:grid-cols-2">
                  <li v-for="item in ITENS_CONFERENCIA" :key="item.chave" class="flex items-center gap-2 text-sm">
                    <CheckCircleIcon v-if="caso.conferencia[item.chave]" class="h-5 w-5 text-paper-success" aria-label="Confere" />
                    <XCircleIcon v-else class="h-5 w-5 text-paper-danger" aria-label="Não confere" />
                    {{ item.rotulo }}
                  </li>
                </ul>
                <p class="mt-3 text-xs text-gray-500">
                  Conferido por {{ caso.conferencia.conferidoPor.nome }} em {{ formatarDataHora(caso.conferencia.conferidoEm) }}
                </p>
              </template>
              <p v-else class="text-sm text-gray-500">Nenhuma conferência registrada para este caso.</p>
            </div>
          </template>

          <template #macroscopia>
            <RegistrosEtapa
              :registros="registrosDe(['MACROSCOPIA', 'CONGELACAO'])"
              :vazio="caso.tipoExame === 'CO' ? 'O exame intraoperatório (congelação) ainda não foi registrado para este caso.' : 'A macroscopia ainda não foi registrada para este caso.'"
            />
          </template>
          <template #processamento>
            <RegistrosEtapa :registros="registrosDe(['PROCESSAMENTO'])" vazio="O processamento técnico ainda não foi registrado para este caso." />
          </template>
          <template #ihq>
            <p v-if="caso.ihqs.length === 0" class="rounded-md border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
              Nenhuma IHQ vinculada a este caso.
            </p>
            <div v-else class="grid gap-4 md:grid-cols-2">
              <article v-for="ihq in caso.ihqs" :key="ihq.codigoInternoIhq" class="rounded-lg border border-gray-200 p-4">
                <header class="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <h3 class="text-lg font-extrabold text-gray-900">{{ ihq.codigoInternoIhq }}</h3>
                  <Badge :variant="STATUS_EXAME_IHQ[ihq.status].variante" size="sm">{{ STATUS_EXAME_IHQ[ihq.status].rotulo }}</Badge>
                </header>
                <dl class="grid gap-3 sm:grid-cols-2 text-sm">
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Solicitação AGHU</dt><dd>{{ ihq.solicitacaoAghuCodigo }}</dd></div>
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Recebida em</dt><dd>{{ formatarDataHora(ihq.recebidaEm) }}</dd></div>
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Registrada por</dt><dd>{{ ihq.registradaPor.nome }}</dd></div>
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Anticorpos</dt><dd>{{ ihq.anticorpos.join(', ') || 'A definir pela IHQ' }}</dd></div>
                  <div v-if="ihq.laboratorioExterno" class="sm:col-span-2"><dt class="text-xs font-bold uppercase text-gray-500">Laboratório externo</dt><dd>{{ ihq.laboratorioExterno }}</dd></div>
                  <div v-if="ihq.resultadoTecnico" class="sm:col-span-2"><dt class="text-xs font-bold uppercase text-gray-500">Resultado técnico</dt><dd>{{ ihq.resultadoTecnico }}</dd></div>
                  <div v-if="ihq.observacao" class="sm:col-span-2"><dt class="text-xs font-bold uppercase text-gray-500">Observação</dt><dd>{{ ihq.observacao }}</dd></div>
                </dl>
              </article>
            </div>
          </template>
          <template #microscopia>
            <RegistrosEtapa :registros="registrosDe(['TRIAGEM_CITO', 'MICROSCOPIA'])" vazio="A microscopia ainda não foi registrada para este caso." />
          </template>
          <template #laudo>
            <RegistrosEtapa :registros="registrosDe(['APROVACAO'])" vazio="O laudo ainda não foi registrado para este caso." />
          </template>
          <template #arquivo>
            <RegistrosEtapa :registros="registrosDe(['ARQUIVO'])" vazio="O arquivamento ainda não foi registrado para este caso." />
          </template>

          <template #materiais>
            <p class="mb-3 text-sm font-semibold text-gray-700">{{ totaisMateriais }}</p>
            <ArvoreMateriais :itens="caso.materiais" :destaque="itemDestacado" />
          </template>

          <template #ncs>
            <p
              v-if="caso.naoConformidades.length === 0 && !caso.cancelamento"
              class="rounded-md border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500"
            >
              Nenhuma não conformidade registrada neste caso.
            </p>
            <div class="space-y-4">
              <article v-for="nc in caso.naoConformidades" :key="nc.id" class="rounded-lg border border-paper-danger/40 p-4">
                <header class="mb-2 flex flex-wrap items-center gap-2">
                  <h3 class="font-bold text-gray-900">{{ TIPOS_NAO_CONFORMIDADE[nc.tipo] }}</h3>
                  <Badge variant="default" size="sm">{{ STATUS_NAO_CONFORMIDADE[nc.status] }}</Badge>
                  <Badge v-if="devolucaoDe(nc.id)" :variant="SITUACOES_DEVOLUCAO[devolucaoDe(nc.id)!.situacao].variante" size="sm">
                    {{ SITUACOES_DEVOLUCAO[devolucaoDe(nc.id)!.situacao].rotulo }}
                  </Badge>
                </header>
                <p class="text-sm text-gray-800">{{ nc.descricao }}</p>
                <dl class="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Setor / etapa</dt><dd>{{ nc.setor }} · {{ nc.etapa }}</dd></div>
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Data/hora</dt><dd>{{ formatarDataHora(nc.registradoEm) }}</dd></div>
                  <div><dt class="text-xs font-bold uppercase text-gray-500">Registrada por</dt><dd>{{ nc.registradoPor.nome }}</dd></div>
                  <template v-if="devolucaoDe(nc.id)">
                    <div><dt class="text-xs font-bold uppercase text-gray-500">Unidade de origem</dt><dd>{{ devolucaoDe(nc.id)!.unidadeOrigem }}</dd></div>
                    <div><dt class="text-xs font-bold uppercase text-gray-500">Devolvido por</dt><dd>{{ devolucaoDe(nc.id)!.devolvidoPor.nome }}</dd></div>
                    <div><dt class="text-xs font-bold uppercase text-gray-500">Nova amostra solicitada</dt><dd>{{ devolucaoDe(nc.id)!.novaAmostraSolicitada ? 'Sim' : 'Não' }}</dd></div>
                  </template>
                </dl>
              </article>
              <article v-if="caso.cancelamento" class="rounded-lg border border-gray-300 bg-gray-50 p-4">
                <h3 class="font-bold text-gray-900">Cancelamento do caso</h3>
                <p class="mt-1 text-sm text-gray-800">{{ caso.cancelamento.motivo }}</p>
                <p class="mt-2 text-xs text-gray-500">
                  {{ caso.cancelamento.canceladoPor.nome }} · {{ formatarDataHora(caso.cancelamento.canceladoEm) }}
                </p>
              </article>
            </div>
          </template>

          <template #historico>
            <p class="mb-3 inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-xs font-bold text-gray-600">
              <LockClosedIcon class="h-3.5 w-3.5" aria-hidden="true" /> Registro imutável
            </p>
            <ol class="space-y-3">
              <li v-for="evento in historicoOrdenado" :key="evento.id" class="relative border-l-2 border-gray-200 pl-4">
                <span class="absolute -left-[5px] top-1.5 h-2 w-2 rounded-full bg-paper-primary" aria-hidden="true"></span>
                <p class="text-sm font-bold text-gray-800">{{ evento.titulo }}</p>
                <p v-if="evento.descricao" class="text-sm text-gray-700">{{ evento.descricao }}</p>
                <p class="text-xs text-gray-500">{{ evento.setor }} · {{ evento.usuario.nome }} · {{ formatarDataHora(evento.ocorridoEm) }}</p>
              </li>
            </ol>
          </template>
        </Tabs>
      </Card>

      <NaoConformidadeModal
        :show="ncAberta"
        :contexto="{ tipo: 'CASO', casoNumero: caso.numeroInterno }"
        :caso="caso"
        @close="ncAberta = false"
        @registrado="aposAlteracao"
      />
      <CancelarCasoModal :show="cancelamentoAberto" :caso="caso" @close="cancelamentoAberto = false" @cancelado="cancelamentoAberto = false" />
      <PrintPreview :show="impressao !== null" :caso="caso" :tipo="impressao ?? 'ETIQUETAS'" @close="impressao = null" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from 'vue-toastification';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  ClipboardDocumentIcon,
  DocumentMagnifyingGlassIcon,
  ExclamationTriangleIcon,
  LockClosedIcon,
  PrinterIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline';
import Badge from '../../components/Badge.vue';
import Button from '../../components/Button.vue';
import Card from '../../components/Card.vue';
import Tabs, { type TabItem } from '../../components/Tabs.vue';
import DadosSolicitacao from '../../components/ap/DadosSolicitacao.vue';
import NaoConformidadeModal from '../../components/ap/NaoConformidadeModal.vue';
import PrintPreview from '../../components/ap/PrintPreview.vue';
import StatusCasoBadge from '../../components/ap/StatusCasoBadge.vue';
import ArvoreMateriais from '../../components/ap/caso/ArvoreMateriais.vue';
import CancelarCasoModal from '../../components/ap/caso/CancelarCasoModal.vue';
import FluxoCaso from '../../components/ap/caso/FluxoCaso.vue';
import RegistrosEtapa from '../../components/ap/caso/RegistrosEtapa.vue';
import {
  ETAPAS,
  ITENS_CONFERENCIA,
  PRAZO_ETAPA_HORAS,
  RESULTADOS_CONFERENCIA,
  SITUACOES_DEVOLUCAO,
  STATUS_BLOQUEADOS,
  STATUS_EXAME_IHQ,
  STATUS_NAO_CONFORMIDADE,
  TIPOS_EXAME,
  TIPOS_ITEM_MATERIAL,
  TIPOS_NAO_CONFORMIDADE,
  casoEstaAtivo,
} from '../../constants/ap';
import { formatarDataHora, horasDesde, tempoDecorrido } from '../../helpers/formato';
import { useCasosStore } from '../../stores/casos';
import type { EtapaCodigo, ItemMaterial, TipoImpressao, TipoItemMaterial } from '../../types/ap';

const props = defineProps<{ numero: string }>();

const route = useRoute();
const toast = useToast();
const casosStore = useCasosStore();

const caso = computed(() => casosStore.casoAtual);
const carregando = computed(() => casosStore.carregandoCaso);
const aba = ref('resumo');
const itemDestacado = ref<string | undefined>();
const ncAberta = ref(false);
const cancelamentoAberto = ref(false);
const menuImpressao = ref(false);
const impressao = ref<TipoImpressao | null>(null);

const ativo = computed(() => !!caso.value && casoEstaAtivo(caso.value.status));
const textoBloqueio = computed(() => (caso.value ? STATUS_BLOQUEADOS[caso.value.status] : undefined));

const opcoesImpressao: { tipo: TipoImpressao; rotulo: string }[] = [
  { tipo: 'ETIQUETAS', rotulo: 'Etiquetas das amostras' },
  { tipo: 'FICHA_TRABALHO', rotulo: 'Ficha de trabalho' },
];

/** Conta todos os itens da árvore por tipo. */
const contarItens = (itens: ItemMaterial[], acc: Partial<Record<TipoItemMaterial, number>> = {}) => {
  for (const item of itens) {
    acc[item.tipoItem] = (acc[item.tipoItem] ?? 0) + 1;
    contarItens(item.filhos, acc);
  }
  return acc;
};

const contagemMateriais = computed(() => contarItens(caso.value?.materiais ?? []));

const totaisMateriais = computed(() => {
  const ordem: TipoItemMaterial[] = ['AMOSTRA', 'FRAGMENTO', 'BLOCO', 'CELL_BLOCK', 'LAMINA'];
  return ordem
    .filter((tipo) => contagemMateriais.value[tipo])
    .map((tipo) => {
      const n = contagemMateriais.value[tipo]!;
      return `${n} ${n === 1 ? TIPOS_ITEM_MATERIAL[tipo].singular : TIPOS_ITEM_MATERIAL[tipo].plural}`;
    })
    .join(' · ');
});

const abas = computed<TabItem[]>(() => {
  const c = caso.value;
  const total = Object.values(contagemMateriais.value).reduce((a, b) => a + (b ?? 0), 0);
  return [
    { key: 'resumo', label: 'Resumo' },
    { key: 'aghu', label: 'Solicitação AGHU' },
    { key: 'recepcao', label: 'Recepção' },
    { key: 'macroscopia', label: c?.tipoExame === 'CO' ? 'Macroscopia / congelação' : 'Macroscopia' },
    { key: 'processamento', label: 'Processamento' },
    { key: 'ihq', label: 'IHQ', count: c?.ihqs.length },
    { key: 'microscopia', label: 'Microscopia' },
    { key: 'laudo', label: 'Laudo' },
    { key: 'arquivo', label: 'Arquivo' },
    { key: 'materiais', label: 'Materiais', count: total },
    { key: 'ncs', label: 'Não conformidades', count: c?.naoConformidades.length },
    { key: 'historico', label: 'Histórico', count: c?.historico.length },
  ];
});

const historicoOrdenado = computed(() => [...(caso.value?.historico ?? [])].sort((a, b) => b.ocorridoEm.localeCompare(a.ocorridoEm) || b.id - a.id));

const camposResumo = computed(() => {
  const c = caso.value;
  if (!c) return [];
  const naEtapa = c.etapaAtual ? tempoDecorrido(c.etapaAtualDesde) : '—';
  const acimaDoPrazo = c.etapaAtual && casoEstaAtivo(c.status) && horasDesde(c.etapaAtualDesde) > PRAZO_ETAPA_HORAS[c.etapaAtual];
  return [
    { rotulo: 'Tipo de exame', valor: `${c.tipoExame} · ${TIPOS_EXAME[c.tipoExame].nome}` },
    { rotulo: 'Etapa atual', valor: c.etapaAtual ? ETAPAS[c.etapaAtual] : 'Fluxo concluído' },
    { rotulo: 'Tempo na etapa atual', valor: naEtapa, alerta: acimaDoPrazo ? 'Acima do prazo padrão' : undefined },
    { rotulo: 'Data de entrada', valor: formatarDataHora(c.dataEntradaSap) },
    { rotulo: 'Procedimento', valor: c.procedimento },
    { rotulo: 'Quantidade de amostras', valor: String(c.quantidade) },
    { rotulo: 'Responsável pela entrada', valor: c.responsavelEntrada.nome },
    { rotulo: 'Solicitação AGHU', valor: c.solicitacao.codigoSolicitacao },
  ];
});

const camposRecepcao = computed(() => {
  const c = caso.value;
  if (!c) return [];
  return [
    { rotulo: 'Entrada no SAP', valor: formatarDataHora(c.dataEntradaSap) },
    { rotulo: 'Responsável', valor: c.responsavelEntrada.nome },
    { rotulo: 'Tipo de exame', valor: `${c.tipoExame} · ${TIPOS_EXAME[c.tipoExame].nome}` },
    { rotulo: 'Quantidade de peças/frascos', valor: String(c.quantidade) },
    { rotulo: 'Urgente', valor: c.urgente ? `Sim — ${c.motivoUrgencia}` : 'Não', largo: c.urgente },
    { rotulo: 'Procedimento', valor: c.procedimento },
    { rotulo: 'Observações', valor: c.observacoes || '—', largo: true },
  ];
});

const registrosDe = (etapas: EtapaCodigo[]) => (caso.value?.registros ?? []).filter((r) => etapas.includes(r.etapa));

const devolucaoDe = (naoConformidadeId: number) => caso.value?.devolucoes.find((d) => d.naoConformidadeId === naoConformidadeId);

const copiar = async () => {
  if (!caso.value) return;
  try {
    await navigator.clipboard.writeText(caso.value.numeroInterno);
    toast.success(`Nº ${caso.value.numeroInterno} copiado.`);
  } catch {
    toast.error('Não foi possível copiar. Selecione o número e copie manualmente.');
  }
};

const imprimir = (tipo: TipoImpressao) => {
  menuImpressao.value = false;
  impressao.value = tipo;
};

const aposAlteracao = async () => {
  ncAberta.value = false;
  await casosStore.recarregarCasoAtual();
};

/** Aba e item destacados conforme a URL (ex.: leitura do código de um item). */
const aplicarQuery = async () => {
  const abaQuery = typeof route.query.aba === 'string' ? route.query.aba : undefined;
  const itemQuery = typeof route.query.item === 'string' ? route.query.item : undefined;
  aba.value = abaQuery && abas.value.some((t) => t.key === abaQuery) ? abaQuery : 'resumo';
  itemDestacado.value = itemQuery;
  if (itemQuery) {
    await nextTick();
    document.getElementById(`material-${itemQuery}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
};

watch(
  () => props.numero,
  async (numero) => {
    await casosStore.carregarCaso(numero);
    await aplicarQuery();
  },
  { immediate: true },
);
watch(() => route.query, aplicarQuery);
</script>
