<template>
  <div class="space-y-6">
    <!-- Filtros (query params snake_case; o filtro geográfico não altera o score) -->
    <Card>
      <form class="grid grid-cols-1 md:grid-cols-4 gap-x-4" @submit.prevent="aplicarFiltros">
        <div class="form-group md:col-span-2">
          <label for="filtroBusca" class="form-label">Busca</label>
          <input id="filtroBusca" v-model="filtros.busca" type="search" class="form-control"
            placeholder="Prontuário, nº da solicitação ou nome do paciente">
        </div>
        <div class="form-group">
          <label for="filtroExame" class="form-label">Código do exame</label>
          <input id="filtroExame" v-model="filtros.codigo_exame" type="text" class="form-control" placeholder="Ex.: USAX">
        </div>
        <div class="form-group">
          <label for="filtroUnidade" class="form-label">Unidade solicitante</label>
          <input id="filtroUnidade" v-model="filtros.unidade" type="text" class="form-control" placeholder="Ex.: Oncologia">
        </div>
        <div class="form-group">
          <label for="filtroMunicipio" class="form-label">Município</label>
          <input id="filtroMunicipio" v-model="filtros.municipio" type="text" class="form-control" placeholder="Ex.: Recife">
        </div>
        <div class="form-group">
          <label for="filtroRegiao" class="form-label">Região</label>
          <select id="filtroRegiao" v-model="filtros.regiao" class="form-control" @change="aplicarFiltros">
            <option :value="undefined">Todas</option>
            <option v-for="(rotulo, valor) in ROTULO_REGIAO" :key="valor" :value="valor">{{ rotulo }}</option>
          </select>
        </div>
        <div class="form-group">
          <label for="filtroStatus" class="form-label">Status operacional</label>
          <select id="filtroStatus" v-model="filtros.status_operacional" class="form-control" @change="aplicarFiltros">
            <option :value="undefined">Fila ativa (padrão)</option>
            <option v-for="(rotulo, valor) in ROTULO_STATUS" :key="valor" :value="valor">{{ rotulo }}</option>
          </select>
        </div>
        <div class="form-group">
          <label for="filtroHigienizacao" class="form-label">Higienização</label>
          <select id="filtroHigienizacao" v-model="filtros.status_higienizacao" class="form-control" @change="aplicarFiltros">
            <option :value="undefined">Válidas (padrão)</option>
            <option v-for="(rotulo, valor) in ROTULO_HIGIENIZACAO" :key="valor" :value="valor">{{ rotulo }}</option>
          </select>
        </div>
        <div class="md:col-span-4 flex flex-wrap items-center gap-x-6 gap-y-3">
          <label class="inline-flex items-center gap-2 text-sm text-paper-text">
            <input v-model="filtros.apenas_tfd" type="checkbox" class="h-4 w-4" @change="aplicarFiltros">
            Apenas TFD
          </label>
          <label class="inline-flex items-center gap-2 text-sm text-paper-text">
            <input v-model="filtros.apenas_24h_vencidos" type="checkbox" class="h-4 w-4" @change="aplicarFiltros">
            Apenas 24h vencidos
          </label>
          <div class="flex gap-2 md:ml-auto">
            <Button type="button" variant="default" @click="limparFiltros">Limpar</Button>
            <Button type="submit" variant="primary" :loading="store.carregando">
              <template #icon><FunnelIcon class="h-5 w-5" /></template>
              Filtrar
            </Button>
          </div>
        </div>
      </form>
    </Card>

    <!-- Fila priorizada (ordem da API) -->
    <Card>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p class="text-sm text-paper-text" aria-live="polite">
          <span v-if="store.carregando">Carregando fila…</span>
          <span v-else>{{ inicioPagina }}–{{ fimPagina }} de {{ store.total }} solicitações</span>
        </p>
        <label class="inline-flex items-center gap-2 text-sm text-paper-text">
          Itens por página
          <select v-model.number="limite" class="form-control w-auto">
            <option v-for="n in [10, 25, 50]" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
      </div>

      <p v-if="store.erro" class="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
        {{ store.erro }}
      </p>

      <DataTable :headers="colunas" :items="linhas">
        <template #cell-prioridade="{ item }">
          <div class="flex flex-col items-center gap-1">
            <span class="font-semibold text-gray-800">{{ item.posicao }}º</span>
            <span
              tabindex="0"
              class="inline-block min-w-10 rounded-full bg-paper-primary px-2.5 py-1 text-center text-sm font-bold text-white cursor-help"
              :title="item.motivosPrioridade.join('\n') || 'Sem motivos informados'"
              :aria-label="`Score ${item.scorePrioridade}: ${item.motivosPrioridade.join('; ')}`"
            >{{ item.scorePrioridade }}</span>
          </div>
        </template>
        <template #cell-paciente="{ item }">
          <p class="font-medium text-gray-800">{{ item.nomePaciente }}</p>
          <p class="text-xs text-gray-500">Pront. {{ item.prontuario ?? '—' }} · Solic. {{ item.codigoSolicitacao }}</p>
          <p class="text-xs text-gray-500">
            {{ item.municipio ?? 'Município não informado' }} · {{ ROTULO_REGIAO[item.regiaoGeografica as RegiaoGeografica] }}
            <span v-if="item.utilizaTfd" class="ml-1 rounded bg-indigo-100 px-1.5 py-0.5 font-semibold text-indigo-800">TFD</span>
          </p>
        </template>
        <template #cell-exame="{ item }">
          <p>{{ item.nomeExame ?? '—' }}</p>
          <p class="text-xs text-gray-500">{{ item.codigoExame ?? 'sem código' }} · {{ item.unidadeSolicitante ?? 'unidade não informada' }}</p>
        </template>
        <template #cell-status="{ item }">
          <div class="flex flex-col items-start gap-1">
            <span :class="COR_STATUS[item.statusOperacional as StatusOperacional]" class="rounded-full px-2 py-0.5 text-xs font-semibold whitespace-nowrap">
              {{ ROTULO_STATUS[item.statusOperacional as StatusOperacional] }}
            </span>
            <span v-if="item.statusHigienizacao !== 'VALIDA'" class="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-semibold text-orange-800 whitespace-nowrap">
              {{ ROTULO_HIGIENIZACAO[item.statusHigienizacao as StatusHigienizacao] }}
            </span>
            <span v-if="item.prazo" :class="item.prazo.vencido ? 'bg-red-600 text-white' : 'bg-amber-50 text-amber-800'"
              class="rounded px-2 py-0.5 text-xs font-semibold whitespace-nowrap">
              {{ item.prazo.texto }}
            </span>
          </div>
        </template>
        <template #cell-alertas="{ item }">
          <div class="flex flex-wrap gap-1">
            <span
              v-for="(alerta, i) in (item.alertasTabela as IAlertaExame[])"
              :key="i"
              :class="COR_SEVERIDADE[alerta.severidade]"
              :title="alerta.mensagem"
              class="rounded px-2 py-0.5 text-xs font-semibold whitespace-nowrap cursor-help"
            >{{ ROTULO_ALERTA[alerta.tipo] }}</span>
          </div>
        </template>
        <template #actions="{ item }">
          <div class="flex flex-wrap gap-2">
            <Button variant="info" title="Ver detalhe" aria-label="Ver detalhe" @click="abrirDetalhe(item.id as number)">
              <EyeIcon class="h-4 w-4" />
            </Button>
            <Button
              variant="primary"
              :disabled="item.statusHigienizacao !== 'VALIDA'"
              :title="item.statusHigienizacao === 'VALIDA' ? 'Atualizar status' : 'Só solicitações com higienização válida mudam de status'"
              aria-label="Atualizar status"
              @click="abrirStatus(item as IItemFila)"
            >
              <ArrowPathIcon class="h-4 w-4" />
            </Button>
            <Button
              v-if="HIGIENIZACAO_VINCULAVEL.includes(item.statusHigienizacao as StatusHigienizacao)"
              variant="warning"
              title="Busca ativa no AGHU"
              aria-label="Busca ativa no AGHU"
              @click="abrirBusca(item as IItemFila)"
            >
              <MagnifyingGlassIcon class="h-4 w-4" />
            </Button>
          </div>
        </template>
      </DataTable>

      <div class="mt-4 flex items-center justify-between gap-3">
        <Button variant="default" :disabled="offset === 0 || store.carregando" @click="irPara(offset - limite)">Anterior</Button>
        <span class="text-sm text-paper-text">Página {{ paginaAtual }} de {{ totalPaginas }}</span>
        <Button variant="default" :disabled="fimPagina >= store.total || store.carregando" @click="irPara(offset + limite)">Próxima</Button>
      </div>
    </Card>

    <!-- Detalhe da solicitação -->
    <Modal :show="detalheAberto" largura="max-w-3xl" @close="detalheAberto = false">
      <template #header>Detalhe da solicitação</template>
      <div class="max-h-[65vh] overflow-y-auto pr-1 space-y-5 text-sm">
        <p v-if="store.carregandoDetalhe">Carregando…</p>
        <p v-else-if="store.erroDetalhe" class="rounded-md bg-red-50 px-4 py-3 text-red-800" role="alert">{{ store.erroDetalhe }}</p>
        <template v-else-if="store.detalhe">
          <section class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1">
            <p><span class="font-medium">Paciente:</span> {{ store.detalhe.nomePaciente }}</p>
            <p><span class="font-medium">Prontuário:</span> {{ store.detalhe.prontuario ?? '—' }}</p>
            <p><span class="font-medium">Solicitação:</span> {{ store.detalhe.codigoSolicitacao }}</p>
            <p><span class="font-medium">Exame:</span> {{ store.detalhe.nomeExame ?? '—' }} ({{ store.detalhe.codigoExame ?? 'sem código' }})</p>
            <p><span class="font-medium">Telefone:</span> {{ store.detalhe.telefoneContato ?? '—' }}</p>
            <p><span class="font-medium">Unidade:</span> {{ store.detalhe.unidadeSolicitante ?? '—' }}</p>
            <p>
              <span class="font-medium">Município:</span> {{ store.detalhe.municipio ?? '—' }}
              ({{ ROTULO_REGIAO[store.detalhe.regiaoGeografica] }}{{ store.detalhe.utilizaTfd ? ' · TFD' : '' }})
            </p>
            <p><span class="font-medium">Data da solicitação:</span> {{ formatarData(store.detalhe.dataSolicitacao) }}</p>
            <p><span class="font-medium">Retorno médico:</span> {{ formatarData(store.detalhe.dataRetornoMedico) }}</p>
            <p><span class="font-medium">Status:</span> {{ ROTULO_STATUS[store.detalhe.statusOperacional] }} · {{ ROTULO_HIGIENIZACAO[store.detalhe.statusHigienizacao] }}</p>
            <p><span class="font-medium">Contato iniciado:</span> {{ formatarDataHora(store.detalhe.contatoIniciadoEm) }}</p>
            <p><span class="font-medium">Prazo de confirmação:</span> {{ formatarDataHora(store.detalhe.prazoConfirmacaoEm) }}</p>
            <p><span class="font-medium">Agendado no AGHU:</span> {{ formatarDataHora(store.detalhe.dataAgendadaAghu) }}</p>
            <p><span class="font-medium">Preparo orientado:</span> {{ store.detalhe.preparoOrientado ? 'Sim' : 'Não' }}</p>
          </section>

          <section>
            <h3 class="font-semibold text-gray-800 mb-1">Score {{ store.detalhe.scorePrioridade }} — motivos</h3>
            <ul class="list-disc pl-5">
              <li v-for="motivo in store.detalhe.motivosPrioridade" :key="motivo">{{ motivo }}</li>
            </ul>
          </section>

          <section>
            <h3 class="font-semibold text-gray-800 mb-1">Alertas</h3>
            <p v-if="!store.detalhe.alertas.length" class="text-gray-500">Nenhum alerta.</p>
            <ul v-else class="space-y-1">
              <li v-for="(alerta, i) in store.detalhe.alertas" :key="i" class="flex items-start gap-2">
                <span :class="COR_SEVERIDADE[alerta.severidade]" class="shrink-0 rounded px-2 py-0.5 text-xs font-semibold">
                  {{ alerta.severidade }}
                </span>
                <span><span class="font-medium">{{ ROTULO_ALERTA[alerta.tipo] }}:</span> {{ alerta.mensagem }}</span>
              </li>
            </ul>
          </section>

          <section>
            <h3 class="font-semibold text-gray-800 mb-1">Outros exames do prontuário</h3>
            <DataTable :headers="colunasOutros" :items="outrosExames">
              <template #cell-exame="{ item }">{{ item.nomeExame ?? '—' }} ({{ item.codigoExame ?? '—' }})</template>
              <template #cell-status="{ item }">
                {{ item.statusOperacional ? ROTULO_STATUS[item.statusOperacional as StatusOperacional] : '—' }}
              </template>
              <template #cell-dataAgendada="{ item }">{{ formatarDataHora(item.dataAgendada) }}</template>
            </DataTable>
          </section>

          <section>
            <h3 class="font-semibold text-gray-800 mb-1">Orientações de preparo</h3>
            <p class="whitespace-pre-line">{{ store.detalhe.orientacoesPreparo || 'Sem orientações cadastradas para este exame.' }}</p>
          </section>
        </template>
      </div>
      <template #footer>
        <Button
          v-if="store.detalhe && HIGIENIZACAO_VINCULAVEL.includes(store.detalhe.statusHigienizacao)"
          variant="warning"
          @click="abrirBusca(store.detalhe)"
        >Busca ativa no AGHU</Button>
        <Button
          v-if="store.detalhe"
          variant="primary"
          :disabled="store.detalhe.statusHigienizacao !== 'VALIDA'"
          @click="abrirStatus(store.detalhe)"
        >Atualizar status</Button>
        <Button variant="default" @click="detalheAberto = false">Fechar</Button>
      </template>
    </Modal>

    <!-- Atualização de status (só transições permitidas pelo backend) -->
    <Modal :show="itemStatus !== null" @close="itemStatus = null">
      <template #header>Atualizar status</template>
      <form v-if="itemStatus" id="formStatus" class="space-y-4 text-sm" @submit.prevent="salvarStatus">
        <p>
          <span class="font-medium">{{ itemStatus.nomePaciente }}</span> — {{ itemStatus.nomeExame ?? itemStatus.codigoExame }}<br>
          Status atual: <span class="font-semibold">{{ ROTULO_STATUS[itemStatus.statusOperacional] }}</span>
        </p>
        <p v-if="itemStatus.statusHigienizacao !== 'VALIDA'" class="rounded-md bg-orange-50 px-4 py-3 text-orange-800" role="alert">
          Solicitação com higienização "{{ ROTULO_HIGIENIZACAO[itemStatus.statusHigienizacao] }}" não pode mudar de status.
          Corrija a solicitação pela busca ativa antes.
        </p>
        <p v-else-if="!opcoesStatus.length" class="rounded-md bg-gray-50 px-4 py-3">
          Status final: não há transições disponíveis.
        </p>
        <template v-else>
          <fieldset class="space-y-2">
            <legend class="form-label">Nova situação</legend>
            <label v-for="opcao in opcoesStatus" :key="opcao" class="flex items-center gap-2">
              <input v-model="formStatus.novo" type="radio" name="novoStatus" :value="opcao" class="h-4 w-4">
              {{ ROTULO_ACAO[opcao] }}
            </label>
          </fieldset>
          <template v-if="formStatus.novo === 'CONFIRMADO_AGENDADO_AGHU'">
            <div>
              <label for="dataAgendada" class="form-label">Data e hora agendadas no AGHU *</label>
              <input id="dataAgendada" v-model="formStatus.dataAgendada" type="datetime-local" required class="form-control">
            </div>
            <label class="flex items-center gap-2">
              <input v-model="formStatus.preparoOrientado" type="checkbox" class="h-4 w-4">
              Preparo orientado ao paciente
            </label>
          </template>
          <div>
            <label for="observacoes" class="form-label">Observações internas</label>
            <textarea id="observacoes" v-model="formStatus.observacoes" rows="3" maxlength="2000" class="form-control"></textarea>
          </div>
        </template>
        <p v-if="store.erroAcao" class="rounded-md bg-red-50 px-4 py-3 text-red-800" role="alert">{{ store.erroAcao }}</p>
      </form>
      <template #footer>
        <Button type="button" variant="default" @click="itemStatus = null">Cancelar</Button>
        <Button type="submit" form="formStatus" variant="success" :disabled="!statusValido" :loading="store.salvando">Salvar</Button>
      </template>
    </Modal>

    <!-- Busca ativa no AGHU e vinculação (só NAO_ENCONTRADA / DIVERGENCIA_EXAME) -->
    <Modal :show="itemBusca !== null" largura="max-w-4xl" @close="itemBusca = null">
      <template #header>Busca ativa no AGHU</template>
      <div v-if="itemBusca" class="max-h-[65vh] overflow-y-auto pr-1 space-y-4 text-sm">
        <p>
          Item informado: <span class="font-medium">{{ itemBusca.nomePaciente }}</span> ·
          solicitação {{ itemBusca.codigoSolicitacao }} · exame {{ itemBusca.codigoExame ?? '—' }}
          ({{ ROTULO_HIGIENIZACAO[itemBusca.statusHigienizacao] }})
        </p>
        <form class="flex flex-wrap items-end gap-2" @submit.prevent="buscar">
          <div>
            <label for="campoBusca" class="form-label">Buscar por</label>
            <select id="campoBusca" v-model="formBusca.campo" class="form-control">
              <option value="prontuario">Prontuário</option>
              <option value="codigo_solicitacao">Nº da solicitação</option>
              <option value="nome">Nome (mín. 3 letras)</option>
            </select>
          </div>
          <div class="flex-1 min-w-48">
            <label for="valorBusca" class="form-label">Valor</label>
            <input id="valorBusca" v-model="formBusca.valor" type="search" class="form-control">
          </div>
          <Button type="submit" variant="primary" :loading="store.buscandoAghu">Buscar</Button>
        </form>
        <p v-if="avisoBusca" class="text-orange-700" role="alert">{{ avisoBusca }}</p>
        <p v-if="store.erroAghu" class="rounded-md bg-red-50 px-4 py-3 text-red-800" role="alert">{{ store.erroAghu }}</p>
        <p v-if="store.erroAcao" class="rounded-md bg-red-50 px-4 py-3 text-red-800" role="alert">{{ store.erroAcao }}</p>
        <DataTable v-if="buscaFeita" :headers="colunasAghu" :items="resultadosAghu">
          <template #cell-exame="{ item }">{{ item.nome_exame ?? '—' }} ({{ item.codigo_exame }})</template>
          <template #cell-data_solicitacao="{ item }">{{ formatarData(item.data_solicitacao) }}</template>
          <template #actions="{ item }">
            <Button variant="success" :loading="store.salvando" @click="vincular(item.codigo_solicitacao, item.codigo_exame)">Vincular</Button>
          </template>
        </DataTable>
      </div>
      <template #footer>
        <Button variant="default" @click="itemBusca = null">Fechar</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useToast } from 'vue-toastification';
import { ArrowPathIcon, EyeIcon, FunnelIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';
import DataTable from '../components/DataTable.vue';
import Modal from '../components/Modal.vue';
import { useExamesStore } from '../stores/exames';
import {
  HIGIENIZACAO_VINCULAVEL,
  TRANSICOES_PERMITIDAS,
  type IAlertaExame,
  type IAtualizarStatusRequest,
  type IBuscaAghuParams,
  type IFiltrosFila,
  type IItemFila,
  type RegiaoGeografica,
  type SeveridadeAlerta,
  type StatusHigienizacao,
  type StatusOperacional,
  type TipoAlerta,
} from '../types/exames';

const store = useExamesStore();
const toast = useToast();

const ROTULO_STATUS: Record<StatusOperacional, string> = {
  NA_FILA: 'Na fila',
  AGUARDANDO_CONFIRMACAO_24H: 'Aguardando confirmação 24h',
  CONFIRMADO_AGENDADO_AGHU: 'Confirmado / agendado no AGHU',
  SEM_RESPOSTA_24H: 'Sem resposta 24h',
  CANCELADO: 'Cancelado',
};
const COR_STATUS: Record<StatusOperacional, string> = {
  NA_FILA: 'bg-gray-100 text-gray-800',
  AGUARDANDO_CONFIRMACAO_24H: 'bg-amber-100 text-amber-800',
  CONFIRMADO_AGENDADO_AGHU: 'bg-green-100 text-green-800',
  SEM_RESPOSTA_24H: 'bg-rose-100 text-rose-800',
  CANCELADO: 'bg-gray-300 text-gray-700',
};
const ROTULO_ACAO: Record<StatusOperacional, string> = {
  NA_FILA: 'Devolver à fila',
  AGUARDANDO_CONFIRMACAO_24H: 'Iniciar aguardo de 24h (paciente contatado)',
  CONFIRMADO_AGENDADO_AGHU: 'Confirmar agendamento no AGHU',
  SEM_RESPOSTA_24H: 'Marcar sem resposta em 24h (libera a vaga)',
  CANCELADO: 'Cancelar solicitação',
};
const ROTULO_HIGIENIZACAO: Record<StatusHigienizacao, string> = {
  VALIDA: 'Válida',
  DUPLICADA: 'Duplicada',
  DIVERGENCIA_EXAME: 'Divergência de exame',
  NAO_ENCONTRADA: 'Não encontrada no AGHU',
  JA_REALIZADA: 'Já realizada',
};
const ROTULO_REGIAO: Record<RegiaoGeografica, string> = {
  CAPITAL: 'Capital',
  RMR: 'RMR',
  INTERIOR: 'Interior',
  NAO_INFORMADO: 'Não informado',
};
const ROTULO_ALERTA: Record<TipoAlerta, string> = {
  INCOMPATIBILIDADE: 'Conflito',
  JANELA_RETORNO: 'Janela de retorno',
  ANTECEDENCIA_PREPARO: 'Preparo',
  JEJUM_CLINICO: 'Jejum',
  IDADE_MAMOGRAFIA: 'Idade',
  PRAZO_24H_VENCIDO: '24h vencido',
  DUPLICIDADE: 'Duplicidade',
};
const COR_SEVERIDADE: Record<SeveridadeAlerta, string> = {
  ALTA: 'bg-red-100 text-red-800',
  MEDIA: 'bg-amber-100 text-amber-800',
  INFO: 'bg-sky-100 text-sky-800',
};

const colunas = [
  { text: 'Prioridade', value: 'prioridade' },
  { text: 'Paciente / município', value: 'paciente' },
  { text: 'Exame / unidade', value: 'exame' },
  { text: 'Status', value: 'status' },
  { text: 'Alertas', value: 'alertas' },
];
const colunasOutros = [
  { text: 'Solicitação', value: 'codigoSolicitacao' },
  { text: 'Exame', value: 'exame' },
  { text: 'Origem', value: 'origem' },
  { text: 'Status', value: 'status' },
  { text: 'Agendado', value: 'dataAgendada' },
];
const colunasAghu = [
  { text: 'Solicitação', value: 'codigo_solicitacao' },
  { text: 'Prontuário', value: 'prontuario' },
  { text: 'Paciente', value: 'nome' },
  { text: 'Exame', value: 'exame' },
  { text: 'Data', value: 'data_solicitacao' },
  { text: 'Unidade', value: 'unidade_solicitante' },
];

// ---- Datas -------------------------------------------------------------
/** Campos de data-hora da fila vêm em UTC sem "Z"; sem isso o navegador leria como hora local. */
function dataUtc(valor: string): Date {
  return new Date(/(Z|[+-]\d{2}:?\d{2})$/i.test(valor) ? valor : `${valor}Z`);
}
function formatarDataHora(valor: string | null): string {
  return valor ? dataUtc(valor).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '—';
}
/** Datas do AGHU e de retorno: só o dia, sem conversão de fuso (evita cair no dia anterior). */
function formatarData(valor: string | null): string {
  return valor ? valor.slice(0, 10).split('-').reverse().join('/') : '—';
}

// Relógio da tela: o destaque de "vencido" aparece sem recarregar a fila.
const agora = ref(Date.now());
const relogio = window.setInterval(() => (agora.value = Date.now()), 60_000);
onUnmounted(() => window.clearInterval(relogio));

function prazo24h(item: IItemFila): { vencido: boolean; texto: string } | null {
  if (item.statusOperacional !== 'AGUARDANDO_CONFIRMACAO_24H' || !item.prazoConfirmacaoEm) return null;
  const vencido = dataUtc(item.prazoConfirmacaoEm).getTime() < agora.value;
  return { vencido, texto: `${vencido ? 'Prazo vencido em' : 'Confirmar até'} ${formatarDataHora(item.prazoConfirmacaoEm)}` };
}

// ---- Fila, filtros e paginação ----------------------------------------
const filtrosVazios = (): IFiltrosFila => ({
  busca: '',
  codigo_exame: '',
  unidade: '',
  municipio: '',
  regiao: undefined,
  status_operacional: undefined,
  status_higienizacao: undefined,
  apenas_tfd: false,
  apenas_24h_vencidos: false,
});
const filtros = reactive<IFiltrosFila>(filtrosVazios());
// Paginação usa os filtros aplicados, não o que ainda está sendo digitado.
const filtrosAplicados = ref<IFiltrosFila>(filtrosVazios());
const limite = ref(10);
const offset = ref(0);

const linhas = computed(() =>
  store.itens.map((item, i) => ({
    ...item,
    posicao: offset.value + i + 1,
    prazo: prazo24h(item),
    alertasTabela: item.alertas.filter((alerta) => alerta.severidade !== 'INFO'), // INFO só no detalhe
  })),
);
const inicioPagina = computed(() => (store.total ? offset.value + 1 : 0));
const fimPagina = computed(() => offset.value + store.itens.length);
const paginaAtual = computed(() => Math.floor(offset.value / limite.value) + 1);
const totalPaginas = computed(() => Math.max(1, Math.ceil(store.total / limite.value)));

async function carregar() {
  await store.carregarFila(filtrosAplicados.value, limite.value, offset.value);
  // Se a página ficou vazia (ex.: item confirmado saiu da fila), volta para a última página com itens.
  if (!store.itens.length && offset.value > 0 && store.total > 0) {
    offset.value = Math.floor((store.total - 1) / limite.value) * limite.value;
    await store.carregarFila(filtrosAplicados.value, limite.value, offset.value);
  }
}
function aplicarFiltros() {
  filtrosAplicados.value = { ...filtros };
  offset.value = 0;
  carregar();
}
function limparFiltros() {
  Object.assign(filtros, filtrosVazios());
  aplicarFiltros();
}
function irPara(novoOffset: number) {
  offset.value = Math.max(0, novoOffset);
  carregar();
}
watch(limite, () => irPara(0));
onMounted(carregar);

// ---- Detalhe ------------------------------------------------------------
const detalheAberto = ref(false);
const outrosExames = computed(() =>
  (store.detalhe?.outrosExames ?? []).map((outro, i) => ({ ...outro, id: `${outro.origem}-${i}` })),
);
function abrirDetalhe(id: number) {
  detalheAberto.value = true;
  store.carregarDetalhe(id);
}

// ---- Status ---------------------------------------------------------------
const itemStatus = ref<IItemFila | null>(null);
const formStatus = reactive({
  novo: undefined as StatusOperacional | undefined,
  dataAgendada: '',
  preparoOrientado: false,
  observacoes: '',
});
const opcoesStatus = computed(() => (itemStatus.value ? TRANSICOES_PERMITIDAS[itemStatus.value.statusOperacional] : []));
const statusValido = computed(
  () =>
    itemStatus.value?.statusHigienizacao === 'VALIDA' &&
    !!formStatus.novo &&
    (formStatus.novo !== 'CONFIRMADO_AGENDADO_AGHU' || !!formStatus.dataAgendada),
);

function abrirStatus(item: IItemFila) {
  detalheAberto.value = false;
  store.erroAcao = null;
  Object.assign(formStatus, { novo: undefined, dataAgendada: '', preparoOrientado: item.preparoOrientado, observacoes: '' });
  itemStatus.value = item;
}

async function salvarStatus() {
  if (!itemStatus.value || !statusValido.value || !formStatus.novo) return;
  const corpo: IAtualizarStatusRequest = { statusOperacional: formStatus.novo };
  if (formStatus.novo === 'CONFIRMADO_AGENDADO_AGHU') {
    // datetime-local está no fuso do navegador; toISOString envia em UTC com "Z".
    corpo.dataAgendadaAghu = new Date(formStatus.dataAgendada).toISOString();
    corpo.preparoOrientado = formStatus.preparoOrientado;
  }
  if (formStatus.observacoes.trim()) corpo.observacoes = formStatus.observacoes.trim();

  const atualizado = await store.atualizarStatus(itemStatus.value.id, corpo);
  if (!atualizado) return;
  const agendado = atualizado.dataAgendadaAghu ? ` Agendado para ${formatarDataHora(atualizado.dataAgendadaAghu)}.` : '';
  toast.success(`Status atualizado: ${ROTULO_STATUS[atualizado.statusOperacional]}.${agendado}`);
  itemStatus.value = null;
  carregar();
}

// ---- Busca ativa no AGHU -------------------------------------------------
const itemBusca = ref<IItemFila | null>(null);
const formBusca = reactive<{ campo: keyof IBuscaAghuParams; valor: string }>({ campo: 'prontuario', valor: '' });
const avisoBusca = ref('');
const buscaFeita = ref(false);
const resultadosAghu = computed(() =>
  store.resultadosAghu.map((linha) => ({ ...linha, id: `${linha.codigo_solicitacao}-${linha.codigo_exame}` })),
);

function abrirBusca(item: IItemFila) {
  detalheAberto.value = false;
  store.resultadosAghu = [];
  store.erroAghu = null;
  store.erroAcao = null;
  avisoBusca.value = '';
  buscaFeita.value = false;
  Object.assign(formBusca, item.prontuario ? { campo: 'prontuario', valor: item.prontuario } : { campo: 'nome', valor: item.nomePaciente });
  itemBusca.value = item;
}

async function buscar() {
  const valor = formBusca.valor.trim().replace(/\s+/g, ' ');
  if (!valor) {
    avisoBusca.value = 'Informe o valor da busca.';
    return;
  }
  if (formBusca.campo === 'nome' && valor.length < 3) {
    avisoBusca.value = 'A busca por nome exige ao menos 3 letras.';
    return;
  }
  avisoBusca.value = '';
  await store.buscarAghu({ [formBusca.campo]: valor });
  buscaFeita.value = true;
}

async function vincular(codigoSolicitacao: string, codigoExame: string) {
  if (!itemBusca.value) return;
  const atualizado = await store.vincularSolicitacao(itemBusca.value.id, { codigoSolicitacao, codigoExame });
  if (!atualizado) return;
  toast.success(`Solicitação ${atualizado.codigoSolicitacao} vinculada (${ROTULO_HIGIENIZACAO[atualizado.statusHigienizacao]}).`);
  itemBusca.value = null;
  carregar();
}
</script>
