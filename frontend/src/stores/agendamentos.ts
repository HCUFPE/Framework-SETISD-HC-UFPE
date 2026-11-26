/** Estado da tela de agendamentos: calendário, paciente, sugestões e mutações. */
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { USAR_MOCKS } from '../config/mocks';
import { agora, paraIsoLocal } from '../config/tempo';
import {
  agendarDaFila,
  agendarExame,
  buscarPacientesAgendamento,
  cancelarAgendamento,
  confirmarPropostaAgendamento,
  gerarPropostasAgendamento,
  listarAgendamentosPaciente,
  listarCalendarioAgendamentos,
  listarFila,
  listarPropostasAgendamento,
  listarSugestoesAgendamento,
  moverPropostaAgendamento,
  alterarStatusLoteAgendamento,
  obterSolicitacao,
  registrarNaoConfirmacaoAgendamento,
  remarcarAgendamento,
  type ResultadoSimulacaoAgenda,
} from '../services/sae';
import type {
  AgendaSlot,
  Agendamento,
  CalendarioAgendamentos,
  PacienteAgendamentos,
  PropostaAgendamentoFila,
  Solicitacao,
  SugestaoAgendamento,
} from '../types/sae';
import { useAuthStore } from './auth';

export type ModoAcaoAgendamento = 'agendar' | 'remarcar' | 'cancelar';

interface ErroComStatus {
  message?: string;
  response?: { status?: number; data?: { detail?: unknown } };
}

function mensagemErro(erro: unknown, fallback: string): string {
  const candidato = erro as ErroComStatus;
  const detail = candidato?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const mensagens = detail
      .map((item) => (item && typeof item === 'object' && 'msg' in item ? String(item.msg) : ''))
      .filter(Boolean);
    if (mensagens.length > 0) return mensagens.join('; ');
  }
  return candidato?.message?.trim() || fallback;
}

function periodoInicial(): { de: string; ate: string } {
  const referencia = agora();
  return {
    de: paraIsoLocal(referencia),
    ate: paraIsoLocal(referencia + 30 * 86_400_000),
  };
}

export const useAgendamentosStore = defineStore('agendamentos', () => {
  const auth = useAuthStore();

  const calendario = ref<CalendarioAgendamentos | null>(null);
  const periodo = ref(periodoInicial());
  const filtros = ref({ unidade: '', codigoExame: '', pacienteChave: '' });
  const carregando = ref(false);
  const salvando = ref(false);
  const erro = ref('');
  const erroStatus = ref<number | null>(null);

  const diaSelecionado = ref('');
  const slotsDoDia = ref<AgendaSlot[]>([]);
  const slotSelecionado = ref<AgendaSlot | null>(null);

  const pacientes = ref<PacienteAgendamentos[]>([]);
  const pacienteChave = ref('');
  const agendamentosPaciente = ref<Agendamento[]>([]);

  const solicitacoes = ref<Solicitacao[]>([]);
  const solicitacao = ref<Solicitacao | null>(null);
  const sugestoes = ref<SugestaoAgendamento[]>([]);
  const propostas = ref<PropostaAgendamentoFila[]>([]);
  /** Última edição em lote executada, guardada para possibilitar reverter. */
  const ultimoLote = ref<{
    novoStatus: string;
    itens: Array<{ agendamentoId: string; statusAnterior: string }>;
  } | null>(null);
  const modalSugestoes = ref(false);
  const modalAcao = ref(false);
  const modalDia = ref(false);
  const modoPopup = ref<'agendar' | 'remarcar'>('agendar');
  const agendamentoPopup = ref<Agendamento | null>(null);
  const modoAcao = ref<ModoAcaoAgendamento>('agendar');
  const agendamentoSelecionado = ref<Agendamento | null>(null);

  const podeEditar = computed(() => !auth.temPerfil('COORDENACAO'));
  const podeGerirVagas = computed(() => USAR_MOCKS
    ? auth.temPerfil('CHEFIA', 'AREA_GESTORA', 'ADMIN_TI')
    : auth.isAdmin || auth.temPerfil('CHEFIA', 'AREA_GESTORA', 'ADMIN_TI')
      || (auth.user?.groups?.includes('CHEFIA') ?? false));

  const unidades = ref<string[]>([]);
  const exames = ref<Array<{ codigo: string; nome: string }>>([]);

  const agendamentos = computed(() => calendario.value?.agendamentos ?? []);
  const slots = computed(() => calendario.value?.slots ?? []);

  /**
   * Acumula unidades/exames já vistos para que os selects não percam opções
   * quando um dos filtros está ativo (a resposta do calendário vem filtrada).
   */
  function acumularOpcoesDeSlots(lista: AgendaSlot[]): void {
    const proximasUnidades = new Set(unidades.value);
    const proximosExames = new Map(exames.value.map((item) => [item.codigo, item]));
    for (const slot of lista) {
      if (slot.unidade) proximasUnidades.add(slot.unidade);
      if (slot.codigoExame) {
        proximosExames.set(slot.codigoExame, {
          codigo: slot.codigoExame,
          nome: slot.nomeExame,
        });
      }
    }
    unidades.value = Array.from(proximasUnidades).sort();
    exames.value = Array.from(proximosExames.values())
      .sort((a, b) => a.nome.localeCompare(b.nome));
  }

  function autor(): string {
    return auth.user?.displayName?.[0] ?? auth.user?.username ?? 'Operador';
  }

  function limparErro(): void {
    erro.value = '';
    erroStatus.value = null;
  }

  function registrarErro(candidato: unknown, fallback: string): void {
    const erroApi = candidato as ErroComStatus;
    erro.value = mensagemErro(candidato, fallback);
    erroStatus.value = erroApi?.response?.status ?? null;
  }

  async function carregar(): Promise<void> {
    carregando.value = true;
    limparErro();
    try {
      const [calendarioResultado, propostasResultado] = await Promise.allSettled([
        listarCalendarioAgendamentos({
          de: periodo.value.de,
          ate: periodo.value.ate,
          unidade: filtros.value.unidade,
          codigoExame: filtros.value.codigoExame,
          pacienteChave: filtros.value.pacienteChave,
        }),
        listarPropostasAgendamento(filtros.value),
      ]);
      if (calendarioResultado.status === 'rejected') throw calendarioResultado.reason;
      calendario.value = calendarioResultado.value;
      acumularOpcoesDeSlots(calendarioResultado.value.slots);
      propostas.value = propostasResultado.status === 'fulfilled' ? propostasResultado.value : [];
      if (diaSelecionado.value) selecionarDia(diaSelecionado.value);
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível carregar o calendário de agendamentos.');
    } finally {
      carregando.value = false;
    }
  }

  function definirPeriodo(de: string, ate: string): void {
    if (periodo.value.de === de && periodo.value.ate === ate) return;
    periodo.value = { de, ate };
    void carregar();
  }

  function aoFiltrar(): void {
    void carregar();
  }

  function selecionarDia(dataIso: string): void {
    diaSelecionado.value = dataIso.slice(0, 10);
    const dia = diaSelecionado.value;
    slotsDoDia.value = slots.value
      .filter((slot) => slot.inicio.slice(0, 10) === dia)
      .sort((a, b) => a.inicio.localeCompare(b.inicio)
        || a.unidade.localeCompare(b.unidade));
    const aindaSelecionado = slotsDoDia.value.find((slot) => slot.id === slotSelecionado.value?.id);
    if (slotSelecionado.value && !aindaSelecionado) slotSelecionado.value = null;
  }

  function selecionarSlot(slot: AgendaSlot): void {
    slotSelecionado.value = slot;
    selecionarDia(slot.inicio);
  }

  /** Abre o popup de vagas do dia clicado no calendário. */
  function abrirDia(
    dataIso: string,
    modo: 'agendar' | 'remarcar' = 'agendar',
    agendamento: Agendamento | null = null,
  ): void {
    selecionarDia(dataIso);
    modoPopup.value = modo;
    agendamentoPopup.value = agendamento;
    modalDia.value = true;
  }

  function fecharDia(): void {
    modalDia.value = false;
  }

  /** Marca a solicitação selecionada (ou remarcar proposta) na vaga escolhida. */
  function marcarNoSlot(slot: AgendaSlot): void {
    modalDia.value = false;
    if (modoPopup.value === 'remarcar' && agendamentoPopup.value) {
      iniciarRemarcacao(agendamentoPopup.value, slot);
      return;
    }
    iniciarAgendamento(slot);
  }

  async function buscarPacientes(q: string): Promise<void> {
    limparErro();
    try {
      pacientes.value = await buscarPacientesAgendamento(q);
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível buscar pacientes.');
    }
  }

  async function selecionarPaciente(chave: string): Promise<void> {
    pacienteChave.value = chave;
    filtros.value.pacienteChave = chave;
    await Promise.all([carregar(), carregarPaciente(chave)]);
  }

  async function carregarPaciente(chave: string): Promise<void> {
    limparErro();
    try {
      agendamentosPaciente.value = await listarAgendamentosPaciente(chave);
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível carregar os agendamentos do paciente.');
    }
  }

  async function buscarSolicitacoes(q: string): Promise<void> {
    limparErro();
    try {
      const resultado = await listarFila({
        busca: q, status: '', tipoExame: '', unidadeSolicitante: '',
        periodo: 'todos', pagina: 1, porPagina: 12,
      });
      solicitacoes.value = resultado.itens;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível buscar solicitações.');
    }
  }

  async function selecionarSolicitacao(id: string): Promise<void> {
    limparErro();
    try {
      solicitacao.value = await obterSolicitacao(id);
      const encontrados = await buscarPacientesAgendamento(solicitacao.value.prontuario);
      const paciente = encontrados.find((item) => item.prontuario === solicitacao.value?.prontuario);
      if (paciente) {
        pacientes.value = encontrados;
        await selecionarPaciente(paciente.pacienteChave);
      }
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível carregar a solicitação.');
    }
  }

  function limparSolicitacao(): void {
    solicitacao.value = null;
    solicitacoes.value = [];
  }

  function abrirAgendamento(agendamento: Agendamento): void {
    agendamentoSelecionado.value = agendamento;
    solicitacao.value = null;
    void selecionarPaciente(agendamento.pacienteChave);
    void selecionarSolicitacao(agendamento.solicitacaoId);
  }

  async function abrirSugestoes(): Promise<void> {
    if (!solicitacao.value) {
      erro.value = 'Selecione uma solicitação antes de pedir sugestões de horário.';
      return;
    }
    limparErro();
    try {
      sugestoes.value = await listarSugestoesAgendamento(solicitacao.value.id, 3);
      modalSugestoes.value = true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível calcular sugestões de horário.');
    }
  }

  function iniciarAgendamento(slot?: AgendaSlot): void {
    if (!podeEditar.value) return;
    if (slot) slotSelecionado.value = slot;
    if (!solicitacao.value) {
      erro.value = 'Selecione uma solicitação para agendar o exame.';
      return;
    }
    modoAcao.value = 'agendar';
    agendamentoSelecionado.value = null;
    limparErro();
    modalAcao.value = true;
  }

  function iniciarRemarcacao(agendamento: Agendamento, slot?: AgendaSlot): void {
    if (!podeEditar.value) return;
    agendamentoSelecionado.value = agendamento;
    if (slot) slotSelecionado.value = slot;
    modoAcao.value = 'remarcar';
    limparErro();
    modalAcao.value = true;
  }

  function iniciarCancelamento(agendamento: Agendamento): void {
    if (!podeEditar.value) return;
    agendamentoSelecionado.value = agendamento;
    modoAcao.value = 'cancelar';
    limparErro();
    modalAcao.value = true;
  }

  function usarSugestao(slot: AgendaSlot): void {
    modalSugestoes.value = false;
    const ativo = agendamentosPaciente.value.find((item) =>
      (item.status === 'ATIVO' || item.status === 'PROPOSTO')
      && item.solicitacaoId === solicitacao.value?.id);
    if (ativo && podeEditar.value) iniciarRemarcacao(ativo, slot);
    else iniciarAgendamento(slot);
  }

  /**
   * Recupera o agendamento de uma linha da fila. A fila é global, mas o
   * calendário pode estar filtrado por paciente/unidade/exame; nesse caso a
   * linha da fila já traz os campos necessários para remarcar ou cancelar.
   */
  function agendamentoDaProposta(proposta: PropostaAgendamentoFila): Agendamento {
    const existente = agendamentos.value.find((item) => item.id === proposta.agendamentoId);
    if (existente) return existente;
    return {
      id: proposta.agendamentoId,
      solicitacaoId: proposta.solicitacaoId,
      protocolo: proposta.protocolo,
      pacienteChave: proposta.prontuario,
      pacienteNome: proposta.pacienteNome,
      prontuario: proposta.prontuario,
      unidade: proposta.unidade,
      exame: proposta.nomeExame,
      slotId: '',
      dataHora: proposta.dataHora,
      status: 'PROPOSTO',
      confirmadoPor: '',
      criadoEm: proposta.recebidaEm,
      justificativa: null,
    };
  }

  async function gerarPropostas(dias = 30): Promise<ResultadoSimulacaoAgenda | null> {
    if (!podeEditar.value) return null;
    salvando.value = true;
    limparErro();
    try {
      const resultado = await gerarPropostasAgendamento(dias, autor(), filtros.value);
      await recarregarTudo();
      return resultado;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível simular a agenda.');
      return null;
    } finally {
      salvando.value = false;
    }
  }

  async function confirmarProposta(proposta: PropostaAgendamentoFila): Promise<boolean> {
    if (!podeEditar.value || proposta.status !== 'PROPOSTO') return false;
    salvando.value = true;
    limparErro();
    try {
      const confirmado = await confirmarPropostaAgendamento(proposta.agendamentoId, autor());
      await focarPacienteDoAgendamento(confirmado);
      return true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível confirmar a proposta.');
      return false;
    } finally {
      salvando.value = false;
    }
  }

  /** Move uma proposta de horário via arrastar e soltar no calendário. */
  async function moverProposta(
    proposta: PropostaAgendamentoFila, slot: AgendaSlot,
  ): Promise<boolean> {
    if (!podeEditar.value || proposta.status !== 'PROPOSTO') return false;
    salvando.value = true;
    limparErro();
    try {
      const movida = await moverPropostaAgendamento(proposta.agendamentoId, slot.id, autor());
      await focarPacienteDoAgendamento(movida);
      return true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível mover a proposta.');
      return false;
    } finally {
      salvando.value = false;
    }
  }

  /** Altera o status de vários agendamentos de uma só vez (edição em lote).
   * Guarda os estados anteriores para possibilitar reverter. */
  async function alterarStatusLote(
    agendamentoIds: string[], novoStatus: string, justificativa: string,
  ): Promise<{ processados: number; novoStatus: string; itens: any[] } | null> {
    if (!podeEditar.value) return null;
    salvando.value = true;
    limparErro();
    try {
      const resultado = await alterarStatusLoteAgendamento(
        agendamentoIds, novoStatus, justificativa, autor(),
      );
      // Guarda para reverter: cada item com seu status anterior.
      ultimoLote.value = {
        novoStatus,
        itens: resultado.itens.map((item) => ({
          agendamentoId: item.agendamentoId,
          statusAnterior: item.statusAnterior,
        })),
      };
      await recarregarTudo();
      return resultado;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível aplicar a edição em lote.');
      return null;
    } finally {
      salvando.value = false;
    }
  }

  /** Reverte a última edição em lote, restaurando os status anteriores. */
  async function reverterUltimoLote(): Promise<boolean> {
    if (!podeEditar.value || !ultimoLote.value) return false;
    salvando.value = true;
    limparErro();
    try {
      const lote = ultimoLote.value;
      await alterarStatusLoteAgendamento(
        lote.itens.map((item: { agendamentoId: string; statusAnterior: string }) =>
          item.agendamentoId,
        ),
        lote.itens[0]?.statusAnterior ?? '',
        `Reversão de edição em lote (${lote.novoStatus} → ${lote.itens[0]?.statusAnterior ?? ''})`,
        autor(),
      );
      ultimoLote.value = null;
      await recarregarTudo();
      return true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível reverter a edição em lote.');
      return false;
    } finally {
      salvando.value = false;
    }
  }

  async function registrarNaoConfirmacao(
    proposta: PropostaAgendamentoFila, justificativa: string,
  ): Promise<boolean> {
    if (!podeEditar.value) return false;
    salvando.value = true;
    limparErro();
    try {
      await registrarNaoConfirmacaoAgendamento(proposta.agendamentoId, justificativa, autor());
      await recarregarTudo();
      return true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível registrar a não confirmação.');
      return false;
    } finally {
      salvando.value = false;
    }
  }

  async function recarregarTudo(): Promise<void> {
    await carregar();
    if (pacienteChave.value) await carregarPaciente(pacienteChave.value);
    if (solicitacao.value) {
      try {
        solicitacao.value = await obterSolicitacao(solicitacao.value.id);
      } catch {
        // A solicitação pode ter mudado de estado; mantém a última leitura válida.
      }
    }
  }

  /**
   * Garante que o agendamento recém-criado/alterado apareça no calendário.
   * Se houver um filtro de paciente ativo para outra pessoa, ele passa a
   * apontar para o paciente do agendamento (o calendário só lista os
   * agendamentos do paciente filtrado).
   */
  async function focarPacienteDoAgendamento(agendamento: Agendamento): Promise<void> {
    const chave = agendamento.pacienteChave;
    if (chave && filtros.value.pacienteChave && filtros.value.pacienteChave !== chave) {
      filtros.value.pacienteChave = chave;
      pacienteChave.value = chave;
    }
    await recarregarTudo();
  }

  async function confirmarAcao(justificativa: string): Promise<boolean> {
    if (modoAcao.value === 'cancelar') return cancelar(justificativa);
    if (!slotSelecionado.value) {
      erro.value = 'Selecione uma vaga no calendário ou nas sugestões.';
      return false;
    }
    salvando.value = true;
    limparErro();
    try {
      let resultado: Agendamento | null = null;
      if (modoAcao.value === 'remarcar' && agendamentoSelecionado.value) {
        resultado = await remarcarAgendamento(
          agendamentoSelecionado.value.id,
          slotSelecionado.value.id,
          justificativa,
          autor(),
        );
      } else if (solicitacao.value?.status === 'RECEBIDA') {
        // RN-07: a solicitação recebida reserva a vaga antes do contato com o paciente,
        // por isso usa o fluxo da fila, que não exige aceite prévio.
        await agendarDaFila(solicitacao.value.id, slotSelecionado.value.id, autor());
        solicitacao.value = await obterSolicitacao(solicitacao.value.id);
      } else if (solicitacao.value) {
        resultado = await agendarExame(solicitacao.value.id, slotSelecionado.value.id, autor());
      } else {
        throw new Error('Selecione uma solicitação antes de confirmar o agendamento.');
      }
      modalAcao.value = false;
      if (resultado) await focarPacienteDoAgendamento(resultado);
      else await recarregarTudo();
      return true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível concluir a operação.');
      return false;
    } finally {
      salvando.value = false;
    }
  }

  async function cancelar(justificativa: string): Promise<boolean> {
    if (!agendamentoSelecionado.value) return false;
    salvando.value = true;
    limparErro();
    try {
      await cancelarAgendamento(agendamentoSelecionado.value.id, justificativa, autor());
      modalAcao.value = false;
      await recarregarTudo();
      return true;
    } catch (candidato) {
      registrarErro(candidato, 'Não foi possível cancelar o agendamento.');
      return false;
    } finally {
      salvando.value = false;
    }
  }

  return {
    calendario,
    periodo,
    filtros,
    carregando,
    salvando,
    erro,
    erroStatus,
    diaSelecionado,
    slotsDoDia,
    slotSelecionado,
    pacientes,
    pacienteChave,
    agendamentosPaciente,
    solicitacoes,
    solicitacao,
    sugestoes,
    propostas,
    ultimoLote,
    modalSugestoes,
    modalAcao,
    modalDia,
    modoPopup,
    modoAcao,
    agendamentoSelecionado,
    podeEditar,
    podeGerirVagas,
    unidades,
    exames,
    agendamentos,
    slots,
    carregar,
    definirPeriodo,
    aoFiltrar,
    selecionarDia,
    selecionarSlot,
    abrirDia,
    fecharDia,
    marcarNoSlot,
    buscarPacientes,
    selecionarPaciente,
    carregarPaciente,
    buscarSolicitacoes,
    selecionarSolicitacao,
    limparSolicitacao,
    abrirAgendamento,
    abrirSugestoes,
    iniciarAgendamento,
    iniciarRemarcacao,
    iniciarCancelamento,
    usarSugestao,
    agendamentoDaProposta,
    gerarPropostas,
    confirmarProposta,
    moverProposta,
    alterarStatusLote,
    reverterUltimoLote,
    registrarNaoConfirmacao,
    confirmarAcao,
    limparErro,
  };
});
