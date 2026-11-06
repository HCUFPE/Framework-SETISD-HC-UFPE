import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { useResponsavel } from '../composables/useResponsavel';
import { TIPOS_NAO_CONFORMIDADE } from '../constants/ap';
import { formatarData } from '../helpers/formato';
import { ServiceError, aghuService, casoService } from '../services/ap';
import type {
  ConfirmarEntradaInput,
  ItensConferencia,
  LeituraSolicitacao,
  ResultadoRecepcao,
  SolicitacaoAghu,
  VincularIhqInput,
} from '../types/ap';

/** Passos da recepção (índice base 0 do `Stepper`). */
export const PASSOS_RECEPCAO = ['Ler etiqueta AGHU', 'Conferir', 'Completar e confirmar', 'Etiquetas e ficha'];

/** Mensagem exibida no passo de leitura. */
export interface MensagemLeitura {
  texto: string;
  /** Caso que pode ser aberto a partir da mensagem (solicitação já recebida). */
  casoNumero?: string;
  /** Lembrete adicional exibido abaixo da mensagem. */
  dica?: string;
}

const conferenciaVazia = (): ItensConferencia => ({
  identificacaoConfere: false,
  materialConfere: false,
  quantidadeConfere: false,
  recipienteAdequado: false,
});

/**
 * Estado do assistente de recepção de amostras (4 passos) e das solicitações pendentes.
 */
export const useRecepcaoStore = defineStore('recepcao', () => {
  const responsavel = useResponsavel();

  const passo = ref(0);
  const solicitacao = ref<SolicitacaoAghu | null>(null);
  const conferencia = ref<ItensConferencia>(conferenciaVazia());
  const resultado = ref<ResultadoRecepcao | null>(null);
  const mensagemLeitura = ref<MensagemLeitura | null>(null);
  const lendo = ref(false);

  const pendentes = ref<SolicitacaoAghu[]>([]);
  const carregandoPendentes = ref(false);
  const aghuIndisponivel = ref(false);
  const contagemPendentes = ref(0);

  const conferenciaCompleta = computed(() => Object.values(conferencia.value).every(Boolean));

  /** Atualiza o contador de pendentes exibido no menu. */
  async function atualizarContagem(): Promise<void> {
    contagemPendentes.value = await aghuService.contarPendentes();
  }

  /** Carrega as solicitações aguardando recebimento, tratando a indisponibilidade do AGHU. */
  async function carregarPendentes(): Promise<void> {
    carregandoPendentes.value = true;
    try {
      pendentes.value = await aghuService.listarPendentes();
      aghuIndisponivel.value = false;
    } catch (erro) {
      if (erro instanceof ServiceError && erro.status === 503) {
        aghuIndisponivel.value = true;
        pendentes.value = [];
      } else {
        throw erro;
      }
    } finally {
      carregandoPendentes.value = false;
    }
    await atualizarContagem();
  }

  /** Abre a conferência de uma solicitação pendente. */
  function iniciarConferencia(sol: SolicitacaoAghu): void {
    solicitacao.value = sol;
    conferencia.value = conferenciaVazia();
    resultado.value = null;
    mensagemLeitura.value = null;
    passo.value = 1;
  }

  /** Mensagem para uma leitura que não pode ser recebida. */
  function mensagemPara(leitura: LeituraSolicitacao, codigo: string): MensagemLeitura | null {
    switch (leitura.tipo) {
      case 'RECEBIDA': {
        const ihq = leitura.solicitacao.ihqCodigo;
        return {
          texto: ihq
            ? `A solicitação ${leitura.solicitacao.codigoSolicitacao} já foi recebida como ${ihq} (caso ${leitura.casoNumero}).`
            : `A solicitação ${leitura.solicitacao.codigoSolicitacao} já foi recebida como ${leitura.casoNumero}.`,
          casoNumero: leitura.casoNumero,
        };
      }
      case 'DEVOLVIDA':
        return {
          texto: `A solicitação ${leitura.solicitacao.codigoSolicitacao} foi devolvida em ${formatarData(leitura.devolvidaEm)} por não conformidade: ${TIPOS_NAO_CONFORMIDADE[leitura.tipoNaoConformidade]}.`,
          dica: 'Aguarde a nova amostra com uma nova solicitação do AGHU.',
        };
      case 'NAO_ENCONTRADA':
        return {
          texto: `Nenhuma solicitação encontrada para ${codigo}. Confira a etiqueta ou digite o número.`,
          dica: 'Material sem etiqueta do AGHU deve ser devolvido: registre uma não conformidade.',
        };
      default:
        return null;
    }
  }

  /** Lê o número de uma solicitação no passo 1. */
  async function lerCodigo(codigoBruto: string): Promise<LeituraSolicitacao | null> {
    const codigo = codigoBruto.trim().toUpperCase();
    if (!codigo) {
      mensagemLeitura.value = { texto: 'Informe o número da solicitação AGHU.' };
      return null;
    }
    lendo.value = true;
    try {
      const leitura = await aghuService.lerSolicitacao(codigo);
      if (leitura.tipo === 'PENDENTE') iniciarConferencia(leitura.solicitacao);
      else mensagemLeitura.value = mensagemPara(leitura, codigo);
      return leitura;
    } catch (erro) {
      if (erro instanceof ServiceError && erro.status === 503) {
        aghuIndisponivel.value = true;
        mensagemLeitura.value = { texto: erro.detail };
        return null;
      }
      throw erro;
    } finally {
      lendo.value = false;
    }
  }

  /** Avança para "Completar e confirmar" se a conferência estiver completa. */
  function confirmarConferencia(): boolean {
    if (!conferenciaCompleta.value) return false;
    passo.value = 2;
    return true;
  }

  function voltarParaConferencia(): void {
    passo.value = 1;
  }

  /** Confirma a entrada de um caso principal. */
  async function confirmarEntrada(dados: Omit<ConfirmarEntradaInput, 'solicitacaoCodigo' | 'conferencia'>): Promise<void> {
    if (!solicitacao.value) return;
    const caso = await casoService.confirmarEntrada(
      { ...dados, solicitacaoCodigo: solicitacao.value.codigoSolicitacao, conferencia: conferencia.value },
      responsavel.value,
    );
    resultado.value = { tipo: 'CASO', caso };
    passo.value = 3;
    await atualizarContagem();
  }

  /** Vincula a IHQ ao caso de origem. */
  async function vincularIhq(dados: Omit<VincularIhqInput, 'solicitacaoCodigo' | 'conferencia'>): Promise<void> {
    if (!solicitacao.value) return;
    const { caso, ihq } = await casoService.vincularIhq(
      { ...dados, solicitacaoCodigo: solicitacao.value.codigoSolicitacao, conferencia: conferencia.value },
      responsavel.value,
    );
    resultado.value = { tipo: 'IHQ', caso, ihq };
    passo.value = 3;
    await atualizarContagem();
  }

  /** Registra o acionamento da equipe de plantão (congelação). */
  async function registrarPlantao(): Promise<void> {
    if (resultado.value?.tipo !== 'CASO') return;
    const caso = await casoService.registrarAcionamentoPlantao(resultado.value.caso.numeroInterno, responsavel.value);
    resultado.value = { tipo: 'CASO', caso };
  }

  /** Volta ao passo 1 descartando o recebimento em andamento. */
  function reiniciar(): void {
    passo.value = 0;
    solicitacao.value = null;
    conferencia.value = conferenciaVazia();
    resultado.value = null;
    mensagemLeitura.value = null;
  }

  return {
    passo,
    solicitacao,
    conferencia,
    conferenciaCompleta,
    resultado,
    mensagemLeitura,
    lendo,
    pendentes,
    carregandoPendentes,
    aghuIndisponivel,
    contagemPendentes,
    atualizarContagem,
    carregarPendentes,
    iniciarConferencia,
    lerCodigo,
    confirmarConferencia,
    voltarParaConferencia,
    confirmarEntrada,
    vincularIhq,
    registrarPlantao,
    reiniciar,
  };
});
