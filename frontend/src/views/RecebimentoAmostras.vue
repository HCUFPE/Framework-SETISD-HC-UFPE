<template>
  <div class="space-y-4">
    <div ref="blocoBusca" class="flex items-center gap-3 px-4 py-3 bg-white shadow-paper rounded-lg scroll-mt-24">
      <label for="codigoSolicitacao" class="text-sm font-medium text-paper-text whitespace-nowrap">Etiqueta ou código</label>
      <input
        id="codigoSolicitacao"
        ref="campoCodigo"
        v-model="codigo"
        type="text"
        autocomplete="off"
        placeholder="Bipe a etiqueta ou digite: código, código + amostra em 3 dígitos, ou código-amostra"
        class="form-control"
        @keydown.enter.prevent="buscar"
      >
      <Button
        variant="primary"
        class="whitespace-nowrap"
        :loading="store.carregando"
        @click="buscar"
      >
        Buscar
      </Button>
    </div>

    <Card
      v-if="store.resultado?.tipo === 'recebimento'"
      class="border-2"
      :class="store.resultado.falhas.length ? 'border-yellow-500' : 'border-green-600'"
      data-testid="resultado-recebimento"
    >
      <div class="text-sm font-medium text-gray-600">
        Solicitação {{ store.resultado.codigo }}
        {{ store.resultado.falhas.length ? 'recebida em parte' : 'recebida' }}. Nº interno para o frasco:
      </div>
      <div
        v-if="store.resultado.falhas.length"
        class="pt-3 mt-4 border-t border-yellow-300 text-sm"
        data-testid="falhas-recebimento"
      >
        <p class="font-bold text-red-700">Não foi possível receber:</p>
        <p v-for="falha in store.resultado.falhas" :key="falha.tipo" class="text-red-700">
          {{ falha.tipo }} (amostra{{ falha.amostras.length > 1 ? 's' : '' }} {{ falha.amostras.join(', ') }}):
          {{ falha.detail }}
        </p>
        <p class="mt-1 text-xs text-gray-600">
          As demais bancadas foram gravadas. Confira a solicitação e receba novamente as pendentes.
        </p>
      </div>
    </Card>

    <Card
      v-if="store.resultado?.tipo === 'devolucao'"
      class="border-2 border-yellow-500"
      data-testid="resultado-devolucao"
    >
      <p class="text-lg font-bold text-yellow-700">
        Solicitação {{ store.resultado.codigo }} devolvida ao setor de origem.
      </p>
      <p class="text-sm text-gray-600 mt-1">Motivo: {{ store.resultado.motivo }}. Nenhum nº interno foi gerado.</p>
    </Card>

    <ListaSolicitacoes v-if="!store.solicitacao" @abrir="abrirDaLista" />

    <template v-else>
      <div class="px-5 py-4 bg-white shadow-paper rounded-lg" data-testid="resumo-solicitacao">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-baseline gap-2">
              <span class="text-xs font-semibold tracking-wider text-gray-500 uppercase">Solicitação</span>
              <h2 class="text-xl font-extrabold text-gray-800" data-testid="titulo-solicitacao">{{ store.solicitacao.codigo }}</h2>
            </div>
            <span
              class="px-2 py-0.5 rounded-full text-xs font-semibold"
              :class="SITUACOES[store.solicitacao.situacao].classe"
              data-testid="situacao-solicitacao"
            >
              {{ SITUACOES[store.solicitacao.situacao].rotulo }}
            </span>
            <span
              v-if="store.solicitacao.urgente"
              class="px-2 py-0.5 rounded-full bg-red-600 text-xs font-bold text-white"
              data-testid="urgente"
            >
              Urgente
            </span>
          </div>
          <Button variant="default" data-testid="voltar-lista" @click="voltarParaLista">Voltar para a lista</Button>
        </div>

        <dl class="grid grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-2 mt-3 text-sm">
          <div v-for="campo in campos" :key="campo.rotulo">
            <dt class="text-xs text-gray-500">{{ campo.rotulo }}</dt>
            <dd class="font-medium text-gray-800">{{ campo.valor }}</dd>
          </div>
        </dl>

        <div class="mt-3 pt-3 border-t border-gray-100 text-sm" data-testid="informacoes-clinicas">
          <p class="text-xs text-gray-500">Informações clínicas</p>
          <p class="text-gray-800 whitespace-pre-line" :class="{ 'line-clamp-2': textoRecolhido }">{{ informacoesClinicas }}</p>
          <button
            v-if="textoLongo"
            type="button"
            class="mt-1 text-xs font-bold text-paper-primary-hover hover:underline"
            data-testid="alternar-informacoes"
            @click="clinicasExpandidas = !clinicasExpandidas"
          >
            {{ clinicasExpandidas ? 'Mostrar menos' : 'Ler tudo' }}
          </button>
        </div>
      </div>

      <div
        v-if="naoConformidadesPendentes.length"
        class="px-5 py-3 border border-orange-300 bg-orange-50 rounded-lg text-sm text-orange-900"
        data-testid="alerta-devolucao"
      >
        <p class="font-bold">Devolvida à origem. Confira se o problema foi resolvido antes de receber.</p>
        <p v-for="(registro, indice) in naoConformidadesPendentes" :key="indice">
          {{ registro.tipo }}: {{ registro.motivo }}
        </p>
      </div>

      <Card>
        <div class="w-full overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs font-semibold tracking-wider text-left text-gray-500 uppercase border-b border-gray-200 bg-gray-50">
                <th class="px-2 py-2 text-center">Amostra</th>
                <th class="px-2 py-2">Exame</th>
                <th class="px-2 py-2">Material</th>
                <th class="px-2 py-2">Status no AGHU</th>
                <th class="px-2 py-2 text-center">Receber</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="linha in store.linhas"
                :key="linha.numero_amostra"
                data-testid="linha-amostra"
                :data-amostra="linha.numero_amostra"
                :class="[
                  linha.numero_amostra === store.solicitacao.numero_amostra_lida ? 'bg-blue-50' : '',
                  !linha.recebivel ? 'bg-gray-50' : '',
                ]"
              >
                <td class="px-2 py-2 text-center whitespace-nowrap">
                  <span class="font-bold">{{ linha.numero_amostra }}</span>
                  <span
                    class="inline-block ml-2 px-2 py-0.5 rounded bg-gray-200 text-xs font-bold text-gray-700"
                    :title="`Bancada ${linha.bancada}`"
                  >
                    {{ linha.bancada }}
                  </span>
                  <span
                    v-if="linha.numero_amostra === store.solicitacao.numero_amostra_lida"
                    class="block mt-1 text-xs font-bold text-blue-700"
                  >
                    Lida agora
                  </span>
                </td>
                <td class="px-2 py-2">
                  <span class="font-medium">{{ linha.nome_exame }}</span>
                  <p class="text-xs text-gray-500">Sigla {{ linha.sigla_exame }} · Lab. {{ linha.codigo_lab }}</p>
                </td>
                <td class="px-2 py-2 min-w-40">
                  <span v-if="linha.descricao_material">{{ linha.descricao_material }}</span>
                  <span v-else-if="linha.material_informado">
                    {{ linha.material_informado }}
                    <span class="block text-xs text-gray-500">Informado na recepção</span>
                  </span>
                  <template v-else-if="linha.recebivel">
                    <label :for="`material${linha.numero_amostra}`" class="block mb-1 text-xs text-red-600 font-medium">
                      Sem descrição no AGHU. Informe o material do frasco:
                    </label>
                    <input
                      :id="`material${linha.numero_amostra}`"
                      v-model="linha.descricao_informada"
                      type="text"
                      maxlength="200"
                      class="form-control"
                      :disabled="!linha.receber"
                    >
                  </template>
                  <span v-else class="text-gray-500">Sem descrição no AGHU</span>
                  <p v-if="linha.motivo_bloqueio && !linha.recebida" class="mt-1 text-xs text-red-600 font-medium">
                    {{ linha.motivo_bloqueio }}
                  </p>
                </td>
                <td class="px-2 py-2 whitespace-nowrap">
                  <span
                    class="inline-block px-2 py-0.5 rounded-full text-xs font-semibold"
                    :class="linha.recebivel || linha.recebida ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'"
                  >
                    {{ linha.status_item_exame }}
                  </span>
                  <p class="mt-1 text-xs text-gray-500">Código {{ linha.cod_status_item }}</p>
                </td>
                <td v-if="linha.recebida" class="px-2 py-2 text-center text-xs" data-testid="amostra-recebida">
                  <span class="font-bold text-green-800">Recebida</span>
                  <span v-if="linha.conferencia" class="block text-gray-600">
                    Conferida por {{ linha.conferencia.conferido_por }} em {{ formatarData(linha.conferencia.conferido_em) }}
                  </span>
                </td>
                <td v-else class="px-2 py-2 text-center">
                  <input
                    v-model="linha.receber"
                    type="checkbox"
                    class="h-5 w-5"
                    :disabled="!linha.recebivel"
                    :aria-label="`Receber a amostra ${linha.numero_amostra}`"
                  >
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <fieldset v-if="store.marcadas.length" class="mt-4 border-t border-gray-200 pt-3" data-testid="checklist">
          <legend class="pr-2 text-sm font-bold text-gray-800">Checklist do recebimento (obrigatório)</legend>
          <div class="flex flex-wrap gap-x-8 gap-y-2 mt-2 text-sm text-gray-800">
            <label class="flex items-center gap-2 cursor-pointer">
              <input id="checklistSigla" v-model="store.siglaConfere" type="checkbox" class="h-5 w-5">
              Siglas conferem com o conteúdo dos frascos
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input id="checklistDescricao" v-model="store.descricaoConfere" type="checkbox" class="h-5 w-5">
              Descrições conferem com os frascos
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input id="checklistRecipientes" v-model="store.recipientesConfere" type="checkbox" class="h-5 w-5">
              Nº de recipientes confere
            </label>
          </div>
        </fieldset>

        <fieldset v-if="store.recebeHp" class="mt-4 border-t border-gray-200 pt-3" data-testid="dados-hp">
          <legend class="pr-2 text-sm font-bold text-gray-800">Dados do HP (obrigatórios)</legend>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
            <div class="form-group">
              <label for="quantidadePecas" class="form-label">Quantidade de peças</label>
              <input
                id="quantidadePecas"
                v-model.number="store.quantidadePecas"
                type="number"
                min="1"
                step="1"
                class="form-control"
              >
            </div>
            <div class="form-group">
              <span class="form-label">Urgência</span>
              <div class="flex items-center space-x-4 mt-2 text-sm">
                <label><input v-model="store.urgente" type="radio" name="urgenciaHp" :value="true"> Sim</label>
                <label><input v-model="store.urgente" type="radio" name="urgenciaHp" :value="false"> Não</label>
              </div>
            </div>
            <div class="form-group">
              <label for="procedimentoHp" class="form-label">Procedimento</label>
              <select id="procedimentoHp" v-model="store.procedimentoId" class="form-control">
                <option :value="null" disabled>Selecione o procedimento</option>
                <option v-for="procedimento in store.procedimentosHp" :key="procedimento.id" :value="procedimento.id">
                  {{ procedimento.descricao }}
                </option>
              </select>
            </div>
          </div>
        </fieldset>

        <div v-if="store.recebeIhq" class="form-group mt-4 border-t border-gray-200 pt-3" data-testid="referencia-hp">
          <label for="referenciaHp" class="form-label">HP de origem da IHQ, se houver (ex.: HP-2025/24)</label>
          <input
            id="referenciaHp"
            v-model="store.referenciaHp"
            type="text"
            maxlength="30"
            autocomplete="off"
            class="form-control"
          >
          <p v-if="!store.referenciaHpValida" class="text-red-600 text-sm font-medium mt-1">
            Use o formato HP-AAAA/N.
          </p>
        </div>

        <div
          class="sticky bottom-0 z-10 flex flex-wrap items-center justify-between gap-3 -mx-6 -mb-6 mt-4 px-6 py-3 bg-white border-t border-gray-200 rounded-b-lg"
          data-testid="barra-acoes"
        >
          <p class="text-sm font-medium text-gray-700" data-testid="progresso-conferencia">
            <template v-if="store.marcadas.length">
              {{ store.marcadas.length }} de {{ store.recebiveis.length }} amostras marcadas ·
              Checklist {{ store.itensConferidos }} de {{ store.TOTAL_ITENS_CHECKLIST }}
            </template>
            <template v-else>Nenhuma amostra marcada para receber</template>
          </p>
          <div class="flex flex-wrap gap-3">
            <Button
              variant="danger"
              :disabled="!store.podeDevolver || store.gravando"
              @click="abrirModal"
            >
              Registrar não conformidade
            </Button>
            <Button
              variant="success"
              :disabled="!store.podeConcluir"
              :loading="store.gravando"
              @click="concluir"
            >
              Concluir recebimento
            </Button>
          </div>
        </div>
      </Card>

      <Card v-if="store.solicitacao.exames.length" data-testid="historico">
        <h3 class="mb-3 text-xs font-semibold tracking-wider text-gray-500 uppercase">Histórico no sistema</h3>
        <ul class="divide-y divide-gray-100 text-sm">
          <li v-for="(exame, indice) in store.solicitacao.exames" :key="indice" class="py-3 first:pt-0 last:pb-0">
            <p class="text-gray-800">
              <span class="font-bold">{{ exame.numero_interno || exame.tipo }}</span>:
              {{ exame.status === 'RECEBIDO' ? 'recebido' : 'devolvido' }}
              por {{ exame.recebido_por }} em {{ formatarData(exame.recebido_em) }}
              <span
                v-if="exame.urgente"
                class="ml-1 px-2 py-0.5 rounded-full bg-red-100 text-xs font-bold text-red-800"
              >
                Urgente
              </span>
            </p>
            <dl v-if="dadosDoExame(exame).length" class="flex flex-wrap gap-x-6 gap-y-1 mt-1 text-gray-600">
              <div v-for="dado in dadosDoExame(exame)" :key="dado.rotulo">
                <dt class="inline text-gray-500">{{ dado.rotulo }}: </dt>
                <dd class="inline font-medium">{{ dado.valor }}</dd>
              </div>
            </dl>
            <div
              v-for="(registro, posicao) in exame.nao_conformidades"
              :key="posicao"
              class="mt-2 pl-3 border-l-4"
              :class="registro.resolvida ? 'border-green-400' : 'border-orange-400'"
              data-testid="nao-conformidade"
            >
              <p class="font-medium text-gray-800">{{ registro.motivo }}</p>
              <p class="text-gray-700 whitespace-pre-line">{{ registro.observacao }}</p>
              <p v-if="registro.numero_cmce || registro.medico_solicitante" class="text-gray-600">
                <template v-if="registro.numero_cmce">Nº no CMCE: {{ registro.numero_cmce }}</template>
                <template v-if="registro.numero_cmce && registro.medico_solicitante"> · </template>
                <template v-if="registro.medico_solicitante">Médico solicitante: {{ registro.medico_solicitante }}</template>
              </p>
              <p class="text-xs" :class="registro.resolvida ? 'text-green-800' : 'text-orange-800'">
                <template v-if="registro.resolvida && registro.resolvida_em">
                  Resolvida: recebida por {{ registro.resolvida_por }} em {{ formatarData(registro.resolvida_em) }}
                </template>
                <template v-else>Pendente de resolução</template>
              </p>
            </div>
          </li>
        </ul>
      </Card>
    </template>

    <Modal :show="modalAberto" @close="fecharModal">
      <template #header>Registrar não conformidade</template>
      <p class="text-sm mb-4">
        Os itens ainda não recebidos serão marcados como devolvidos ao setor de origem, sem gerar nº interno.
      </p>
      <div class="form-group">
        <label for="motivoNaoConformidade" class="form-label">Motivo</label>
        <select id="motivoNaoConformidade" v-model="motivoId" class="form-control">
          <option :value="null" disabled>Selecione o motivo</option>
          <option v-for="motivo in store.motivos" :key="motivo.id" :value="motivo.id">
            {{ motivo.descricao }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="observacaoNaoConformidade" class="form-label">Observação</label>
        <textarea
          id="observacaoNaoConformidade"
          v-model="observacao"
          rows="3"
          maxlength="2000"
          class="form-control"
        ></textarea>
      </div>
      <div class="form-group">
        <label for="numeroCmce" class="form-label">Nº da solicitação no CMCE, se houver</label>
        <input id="numeroCmce" v-model="numeroCmce" type="text" maxlength="30" autocomplete="off" class="form-control">
      </div>
      <div class="form-group">
        <label for="medicoSolicitante" class="form-label">Médico solicitante, se legível</label>
        <input id="medicoSolicitante" v-model="medicoSolicitante" type="text" maxlength="200" autocomplete="off" class="form-control">
      </div>
      <template #footer>
        <Button variant="default" @click="fecharModal">Cancelar</Button>
        <Button
          variant="danger"
          :disabled="!motivoId || !observacao.trim()"
          :loading="store.gravando"
          @click="registrarDevolucao"
        >
          Confirmar devolução
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import Modal from '../components/Modal.vue';
import ListaSolicitacoes from '../components/recebimento/ListaSolicitacoes.vue';
import { classificarErroDaBusca, mensagemDeErro, SITUACOES, useRecebimentoStore } from '../stores/recebimento';
import type { ExameDetalhado } from '../stores/recebimento';

// Acima disto, o texto clínico começa recolhido para não empurrar as amostras para baixo.
const LIMITE_TEXTO_RECOLHIDO = 180;
const LIMITE_LINHAS_RECOLHIDAS = 2;

const store = useRecebimentoStore();
const toast = useToast();

const campoCodigo = ref<HTMLInputElement | null>(null);
const blocoBusca = ref<HTMLElement | null>(null);
const codigo = ref('');
const modalAberto = ref(false);
const motivoId = ref<number | null>(null);
const observacao = ref('');
const numeroCmce = ref('');
const medicoSolicitante = ref('');
const clinicasExpandidas = ref(false);

/** Devolve o foco ao campo de código, com o texto selecionado para a próxima leitura substituí-lo. */
const focarCodigo = async () => {
  await nextTick();
  campoCodigo.value?.focus();
  campoCodigo.value?.select();
  // O cabeçalho é fixo e poderia cobrir o campo se a página já estivesse rolada.
  blocoBusca.value?.scrollIntoView({ block: 'start' });
};

/** Mostra data e hora no fuso do hospital. */
const formatarData = (valor: string) =>
  new Date(valor).toLocaleString('pt-BR', { timeZone: 'America/Recife' });

/** Mostra uma data AAAA-MM-DD do AGHU como DD/MM/AAAA, sem conversão de fuso. */
const formatarDia = (valor: string | null) =>
  valor ? valor.split('-').reverse().join('/') : 'Não informada';

/** Todos os campos da solicitação vindos do AGHU, fora as amostras e o texto clínico. */
const campos = computed(() => {
  const dados = store.solicitacao;
  if (!dados) return [];
  const { paciente } = dados;
  const idade = paciente.idade !== null ? ` (${paciente.idade} anos)` : '';
  return [
    { rotulo: 'Nome', valor: paciente.nome },
    { rotulo: 'Prontuário', valor: paciente.prontuario || 'Sem prontuário' },
    { rotulo: 'Nascimento', valor: `${formatarDia(paciente.data_nascimento)}${idade}` },
    { rotulo: 'Solicitada em', valor: formatarDia(dados.data_solicitacao) },
    { rotulo: 'Origem', valor: dados.origem },
    { rotulo: 'Clínica', valor: dados.especialidade || 'Não informada' },
    { rotulo: 'Unidade', valor: dados.unidade || 'Não informada' },
    { rotulo: 'Convênio', valor: dados.convenio || 'Não informado' },
  ];
});

const informacoesClinicas = computed(
  () => store.solicitacao?.informacoes_clinica || 'Não informadas no AGHU',
);
const textoLongo = computed(
  () =>
    informacoesClinicas.value.length > LIMITE_TEXTO_RECOLHIDO ||
    informacoesClinicas.value.split('\n').length > LIMITE_LINHAS_RECOLHIDAS,
);
const textoRecolhido = computed(() => textoLongo.value && !clinicasExpandidas.value);

const naoConformidadesPendentes = computed(() =>
  (store.solicitacao?.exames ?? []).flatMap((exame) =>
    exame.nao_conformidades
      .filter((registro) => !registro.resolvida)
      .map((registro) => ({ tipo: exame.tipo, motivo: registro.motivo })),
  ),
);

/** Dados que a recepção acrescentou ao exame, só os preenchidos. */
const dadosDoExame = (exame: ExameDetalhado) => {
  const recebidas = exame.amostras.filter((amostra) => amostra.recebida);
  return [
    { rotulo: 'Quantidade de peças', valor: exame.quantidade_pecas },
    { rotulo: 'Procedimento', valor: exame.procedimento },
    { rotulo: 'HP de origem', valor: exame.referencia_hp },
    {
      rotulo: 'Amostras recebidas',
      valor: recebidas.length ? recebidas.map((amostra) => amostra.numero_amostra).join(', ') : null,
    },
  ].filter((dado) => dado.valor !== null);
};

// Cada solicitação aberta começa com o texto clínico recolhido.
watch(
  () => store.solicitacao?.codigo,
  () => {
    clinicasExpandidas.value = false;
  },
);

/** Leva a amostra bipada para o centro da tela, mesmo em solicitações com muitas amostras. */
const mostrarAmostraLida = async () => {
  const numero = store.solicitacao?.numero_amostra_lida;
  if (!numero) return;
  await nextTick();
  document.querySelector(`[data-amostra="${numero}"]`)?.scrollIntoView({ block: 'center' });
};

/** Atualiza a lista inicial e avisa se a leitura falhar. */
const atualizarLista = async () => {
  try {
    await store.carregarLista();
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível carregar a lista de solicitações.'));
  }
};

/** Busca a solicitação. O leitor envia Enter, e leituras repetidas são ignoradas durante a busca. */
const buscar = async () => {
  const valor = codigo.value.trim();
  if (!valor) {
    toast.error('Bipe a etiqueta ou digite o código da solicitação.');
    await focarCodigo();
    return;
  }
  if (store.carregando) return;
  try {
    await store.buscar(valor);
  } catch (erro) {
    store.limparConferencia();
    const { tipo, mensagem } = classificarErroDaBusca(erro);
    if (tipo === 'nao_encontrada') {
      toast.warning(mensagem);
    } else {
      toast.error(mensagem);
    }
  }
  await focarCodigo();
  await mostrarAmostraLida();
};

/** Abre pela lista o mesmo fluxo da leitura da etiqueta. */
const abrirDaLista = async (codigoDaLinha: string) => {
  codigo.value = codigoDaLinha;
  await buscar();
};

const voltarParaLista = async () => {
  store.limparConferencia();
  store.resultado = null;
  codigo.value = '';
  await focarCodigo();
  await atualizarLista();
};

/** Limpa a tela, atualiza a situação na lista e prepara a próxima leitura depois de uma gravação. */
const prepararProximaLeitura = async () => {
  codigo.value = '';
  await focarCodigo();
  await atualizarLista();
};

const concluir = async () => {
  if (store.gravando) return;
  try {
    const falhas = await store.concluirRecebimento();
    if (falhas.length) {
      toast.warning('Recebimento parcial: algumas bancadas não foram gravadas. Veja os detalhes acima.');
    } else {
      toast.success('Recebimento concluído.');
    }
    await prepararProximaLeitura();
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível concluir o recebimento. Tente novamente.'));
  }
};

const abrirModal = () => {
  motivoId.value = null;
  observacao.value = '';
  numeroCmce.value = '';
  medicoSolicitante.value = '';
  modalAberto.value = true;
};

const fecharModal = () => {
  modalAberto.value = false;
};

const registrarDevolucao = async () => {
  if (store.gravando || !motivoId.value) return;
  try {
    await store.registrarNaoConformidade({
      motivo_id: motivoId.value,
      observacao: observacao.value.trim(),
      numero_cmce: numeroCmce.value.trim() || null,
      medico_solicitante: medicoSolicitante.value.trim() || null,
    });
    fecharModal();
    toast.success('Não conformidade registrada.');
    await prepararProximaLeitura();
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível registrar a não conformidade. Tente novamente.'));
  }
};

onMounted(async () => {
  await focarCodigo();
  await atualizarLista();
  try {
    await store.carregarListas();
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível carregar as listas de motivos e procedimentos.'));
  }
});

// A conferência não fica pendente ao sair da tela.
onUnmounted(() => {
  store.limparConferencia();
  store.resultado = null;
});
</script>
