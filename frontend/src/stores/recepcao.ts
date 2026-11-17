import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { useResponsavel } from '../composables/useResponsavel';
import { TIPOS_NAO_CONFORMIDADE } from '../constants/ap';
import { ordenarGrupos } from '../helpers/aghu';
import { formatarData } from '../helpers/formato';
import { ServiceError, aghuService, casoService } from '../services/ap';
import type {
  CasoAp,
  ConfirmarEntradaInput,
  LeituraSolicitacao,
  RecebimentoExame,
  ResultadoRecepcao,
  SolicitacaoAghu,
  VincularIhqInput,
} from '../types/ap';

/** Passos da recepção (índice base 0 do `Stepper`). */
export const PASSOS_RECEPCAO = ['Ler etiqueta AGHU', 'Conferir', 'Etiquetas e ficha'];

/** Mensagem exibida no passo de leitura. */
export interface MensagemLeitura {
  texto: string;
  /** Casos que podem ser abertos a partir da mensagem (solicitação já recebida). */
  recebimentos?: RecebimentoExame[];
  /** Lembrete adicional exibido abaixo da mensagem. */
  dica?: string;
  /** Estilo do alerta (padrão: danger). */
  variante?: 'danger' | 'info';
}

/** Entrada de um tipo de exame principal (HP, CG, CCV, CO) recebido na conferência. */
export interface EntradaCasoConferencia {
  tipo: 'CASO';
  dados: ConfirmarEntradaInput;
}

/** Entrada de um grupo IHQ recebido na conferência. */
export interface EntradaIhqConferencia {
  tipo: 'IHQ';
  /**
   * Vínculo com caso existente; ou, com `usarCasoDaConferencia`, com o caso principal criado
   * nesta mesma conferência (preenchido na confirmação).
   */
  dados: Omit<VincularIhqInput, 'casoOrigemNumero'> & { casoOrigemNumero?: string };
  usarCasoDaConferencia: boolean;
}

export type EntradaConferencia = EntradaCasoConferencia | EntradaIhqConferencia;

/**
 * Estado do assistente de recepção de amostras (3 passos) e das solicitações pendentes.
 *
 * A conferência é por solicitação do AGHU; dentro dela, cada tipo de exame pendente (grupo) é
 * recebido como uma unidade e gera um caso (ou vínculo de IHQ). Tipos podem ficar para depois.
 */
export const useRecepcaoStore = defineStore('recepcao', () => {
  const responsavel = useResponsavel();

  const passo = ref(0);
  /** Grupos de tipo de exame pendentes da solicitação em conferência. */
  const exames = ref<SolicitacaoAghu[]>([]);
  /** Todos os grupos da solicitação em conferência (qualquer situação), recarregados após confirmar. */
  const examesDaSolicitacao = ref<SolicitacaoAghu[]>([]);
  /** Casos e IHQs gerados na confirmação da conferência. */
  const resultados = ref<ResultadoRecepcao[]>([]);
  const mensagemLeitura = ref<MensagemLeitura | null>(null);
  const lendo = ref(false);

  const pendentes = ref<SolicitacaoAghu[]>([]);
  const carregandoPendentes = ref(false);
  const aghuIndisponivel = ref(false);
  const contagemPendentes = ref(0);
  /** Incrementado a cada reinício, para a tela reagir mesmo quando já está no passo 1. */
  const reinicios = ref(0);

  /** Dados de cabeçalho da solicitação em conferência (paciente, origem etc.). */
  const solicitacao = computed<SolicitacaoAghu | null>(() => exames.value[0] ?? examesDaSolicitacao.value[0] ?? null);

  /** Grupos da solicitação que não estão em conferência (já recebidos, devolvidos ou pendentes restantes). */
  const outrosExames = computed(() => {
    const emConferencia = new Set(exames.value.map((e) => e.id));
    return examesDaSolicitacao.value.filter((e) => !emConferencia.has(e.id));
  });

  /**
   * Grupos da solicitação que continuam aguardando recebimento depois da confirmação (tipos
   * deixados para depois). Os grupos são recarregados ao confirmar, já com a nova situação.
   */
  const outrosExamesPendentes = computed(() =>
    passo.value === 2 ? examesDaSolicitacao.value.filter((e) => e.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO') : [],
  );

  /** Carrega todos os grupos da solicitação atual (falha não bloqueia a recepção). */
  async function carregarExamesDaSolicitacao(codigo: string): Promise<void> {
    try {
      examesDaSolicitacao.value = await aghuService.listarExamesDaSolicitacao(codigo);
    } catch (erro) {
      console.error('Falha ao carregar os exames da solicitação.', erro);
    }
  }

  /** Atualiza o contador de solicitações pendentes exibido no menu. */
  async function atualizarContagem(): Promise<void> {
    contagemPendentes.value = await aghuService.contarPendentes();
  }

  /** Carrega os grupos aguardando recebimento, tratando a indisponibilidade do AGHU. */
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

  /** Abre a conferência da solicitação com os grupos pendentes informados. */
  function iniciarConferencia(gruposPendentes: SolicitacaoAghu[]): void {
    exames.value = ordenarGrupos(gruposPendentes);
    examesDaSolicitacao.value = [...exames.value];
    resultados.value = [];
    mensagemLeitura.value = null;
    passo.value = 1;
    const codigo = gruposPendentes[0]?.codigoSolicitacao;
    if (codigo) void carregarExamesDaSolicitacao(codigo);
  }

  /** Mensagem para uma leitura que não pode ser recebida. */
  function mensagemPara(leitura: LeituraSolicitacao, codigo: string): MensagemLeitura | null {
    switch (leitura.tipo) {
      case 'RECEBIDA':
        return {
          texto: `A solicitação ${leitura.solicitacao.codigoSolicitacao} já foi recebida.`,
          recebimentos: leitura.recebimentos,
        };
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
      if (leitura.tipo === 'PENDENTE') iniciarConferencia(leitura.exames);
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

  /**
   * Confirma a conferência: cria um caso por tipo principal recebido e, depois, vincula as IHQs
   * (ao caso existente escolhido ou ao caso principal criado nesta conferência).
   *
   * Se alguma entrada falhar depois de outras já confirmadas, mostra o resultado das confirmadas
   * e repassa o erro para a tela avisar o usuário.
   */
  async function confirmarConferencia(entradas: EntradaConferencia[]): Promise<void> {
    if (entradas.length === 0) throw new ServiceError(400, 'Selecione ao menos um tipo de exame para receber.');
    const confirmados: ResultadoRecepcao[] = [];
    const principais = entradas.filter((e): e is EntradaCasoConferencia => e.tipo === 'CASO');
    const ihqs = entradas.filter((e): e is EntradaIhqConferencia => e.tipo === 'IHQ');
    const ordem: CasoAp['tipoExame'][] = ['CO', 'HP', 'CG', 'CCV'];
    principais.sort((a, b) => ordem.indexOf(a.dados.tipoExame) - ordem.indexOf(b.dados.tipoExame));

    try {
      for (const entrada of principais) {
        const caso = await casoService.confirmarEntrada(entrada.dados, responsavel.value);
        confirmados.push({ tipo: 'CASO', caso });
      }
      for (const entrada of ihqs) {
        let casoOrigemNumero = entrada.dados.casoOrigemNumero;
        if (entrada.usarCasoDaConferencia) {
          const casos = confirmados.filter((r) => r.tipo === 'CASO').map((r) => r.caso);
          casoOrigemNumero = (casos.find((c) => c.tipoExame === 'HP') ?? casos.find((c) => c.tipoExame !== 'CO') ?? casos[0])?.numeroInterno;
        }
        if (!casoOrigemNumero) throw new ServiceError(400, 'Selecione o caso de origem da IHQ.');
        const { caso, ihq } = await casoService.vincularIhq({ ...entrada.dados, casoOrigemNumero }, responsavel.value);
        confirmados.push({ tipo: 'IHQ', caso, ihq });
      }
    } finally {
      if (confirmados.length > 0) {
        resultados.value = confirmados;
        passo.value = 2;
        const codigo = solicitacao.value?.codigoSolicitacao;
        await Promise.all([atualizarContagem(), codigo ? carregarExamesDaSolicitacao(codigo) : Promise.resolve()]);
      }
    }
  }

  /** Registra o acionamento da equipe de plantão (congelação) para um caso da conferência. */
  async function registrarPlantao(numeroInterno: string): Promise<void> {
    const caso = await casoService.registrarAcionamentoPlantao(numeroInterno, responsavel.value);
    resultados.value = resultados.value.map((r) =>
      r.tipo === 'CASO' && r.caso.numeroInterno === numeroInterno ? { tipo: 'CASO', caso } : r,
    );
  }

  /** Volta ao passo 1 descartando o recebimento em andamento. */
  function reiniciar(): void {
    passo.value = 0;
    exames.value = [];
    examesDaSolicitacao.value = [];
    resultados.value = [];
    mensagemLeitura.value = null;
    reinicios.value += 1;
  }

  return {
    passo,
    exames,
    examesDaSolicitacao,
    solicitacao,
    outrosExames,
    outrosExamesPendentes,
    resultados,
    mensagemLeitura,
    lendo,
    pendentes,
    carregandoPendentes,
    aghuIndisponivel,
    contagemPendentes,
    reinicios,
    atualizarContagem,
    carregarPendentes,
    iniciarConferencia,
    lerCodigo,
    confirmarConferencia,
    registrarPlantao,
    reiniciar,
  };
});
