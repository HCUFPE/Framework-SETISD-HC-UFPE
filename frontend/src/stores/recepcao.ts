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
  DadosEtiquetaRecepcao,
  ItemMaterial,
  LeituraSolicitacao,
  RecebimentoExame,
  ResultadoRecepcao,
  SolicitacaoAghu,
  VincularIhqInput,
  AmostraBipadaSituacao,
} from '../types/ap';

/** Passos da recepção (índice base 0 do `Stepper`). */
export const PASSOS_RECEPCAO = ['Ler etiqueta AGHU', 'Conferir', 'Etiquetas e ficha'];

/** Mensagem exibida no passo de leitura. */
export interface MensagemLeitura {
  texto: string;
  /** Casos que podem ser abertos a partir da mensagem (solicitação já recebida). */
  recebimentos?: RecebimentoExame[];
  cancelamentos?: { motivo: string; canceladoPor: { nome: string }; canceladoEm: string }[];
  /** Lembrete adicional exibido abaixo da mensagem. */
  dica?: string;
  /** Estilo do alerta (padrão: danger). */
  variante?: 'danger' | 'info';
}

/** Entrada de um tipo de exame principal (HP, CG, CCV, CO) recebido na conferência. */
export interface EntradaCasoConferencia {
  tipo: 'CASO';
  dados: ConfirmarEntradaInput;
  usarCasoDaConferencia?: boolean;
}

/** Entrada de um grupo IHQ recebido na conferência. */
export interface EntradaIhqConferencia {
  tipo: 'IHQ';
  /** A origem é manual apenas quando a solicitação não possui grupo HP próprio. */
  dados: Omit<VincularIhqInput, 'casoOrigemNumero'> & { casoOrigemNumero?: string };
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
  const examesDaSolicitacaoCarregados = ref(false);
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
  /** Número da amostra bipada, quando extraído da leitura (10 dígitos ou código-amostra). */
  const amostraBipada = ref<string | null>(null);
  /** ID do grupo pendente correspondente à amostra bipada (ou null). */
  const grupoSelecionadoId = ref<string | null>(null);
  /** Metadados quando a amostra bipada pertence a um grupo já recebido/devolvido. */
  const amostraBipadaSituacao = ref<AmostraBipadaSituacao | null>(null);

  /** Projeta a etiqueta da IHQ usando o grupo AGHU recebido, sem copiar a identidade do HP pai. */
  function etiquetaIhq(caso: CasoAp, codigoInternoIhq: string, grupo: SolicitacaoAghu): DadosEtiquetaRecepcao {
    const agora = new Date().toISOString();
    const materiais: ItemMaterial[] = grupo.amostras.map((amostra, indice) => ({
      codigo: indice === 0 ? codigoInternoIhq : `${codigoInternoIhq}-F${indice + 1}`,
      tipoItem: 'AMOSTRA',
      rotulo: `Amostra ${amostra.numeroAmostra}`,
      descricao: amostra.descricaoMaterial,
      numeroAmostraAghu: amostra.numeroAmostra,
      origem: 'COMPLEMENTAR',
      status: 'DISPONIVEL',
      criadoPor: responsavel.value,
      criadoEm: agora,
      filhos: [],
    }));
    return {
      numeroInterno: codigoInternoIhq,
      tipoExame: 'IHQ',
      solicitacao: grupo,
      urgente: caso.urgente,
      dataEntradaSap: agora,
      materiais,
    };
  }

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
    examesDaSolicitacaoCarregados.value = false;
    examesDaSolicitacao.value = [];
    try {
      examesDaSolicitacao.value = await aghuService.listarExamesDaSolicitacao(codigo);
      examesDaSolicitacaoCarregados.value = true;
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
  async function iniciarConferencia(gruposPendentes: SolicitacaoAghu[]): Promise<void> {
    const codigo = gruposPendentes[0]?.codigoSolicitacao;
    if (codigo) await carregarExamesDaSolicitacao(codigo);
    exames.value = ordenarGrupos(gruposPendentes);
    if (!examesDaSolicitacaoCarregados.value) examesDaSolicitacao.value = [...exames.value];
    resultados.value = [];
    mensagemLeitura.value = null;
    amostraBipada.value = null;
    grupoSelecionadoId.value = null;
    amostraBipadaSituacao.value = null;
    passo.value = 1;
  }

  /**
   * Abre a conferência preservando metadados da amostra bipada
   * (já definidos antes da chamada, em `lerCodigo`).
   */
  async function iniciarConferenciaComMetadados(gruposPendentes: SolicitacaoAghu[]): Promise<void> {
    const codigo = gruposPendentes[0]?.codigoSolicitacao;
    if (codigo) await carregarExamesDaSolicitacao(codigo);
    exames.value = ordenarGrupos(gruposPendentes);
    if (!examesDaSolicitacaoCarregados.value) examesDaSolicitacao.value = [...exames.value];
    resultados.value = [];
    mensagemLeitura.value = null;
    passo.value = 1;
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
      case 'CANCELADA':
        return {
          texto: `A solicitação ${leitura.solicitacao.codigoSolicitacao} foi cancelada.`,
          cancelamentos: leitura.cancelamentos.filter((item): item is NonNullable<typeof item> => !!item),
          variante: 'info',
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
      if (leitura.tipo === 'PENDENTE') {
        amostraBipada.value = leitura.amostraBipada ?? null;
        grupoSelecionadoId.value = leitura.grupoSelecionadoId ?? null;
        amostraBipadaSituacao.value = leitura.amostraBipadaSituacao ?? null;
        await iniciarConferenciaComMetadados(leitura.exames);
      } else {
        amostraBipada.value = null;
        grupoSelecionadoId.value = null;
        amostraBipadaSituacao.value = null;
        mensagemLeitura.value = mensagemPara(leitura, codigo);
      }
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
    const ordem: CasoAp['tipoExame'][] = ['CO', 'HP', 'CG', 'CCV', 'REVISAO'];
    principais.sort((a, b) => ordem.indexOf(a.dados.tipoExame) - ordem.indexOf(b.dados.tipoExame));

    try {
      for (const entrada of principais) {
        let dados = entrada.dados;
        if (dados.tipoExame === 'REVISAO' && entrada.usarCasoDaConferencia) {
          const casos = confirmados.filter((r) => r.tipo === 'CASO').map((r) => r.caso);
          const origem = casos.find((c) => c.tipoExame === 'HP')
            ?? casos.find((c) => c.tipoExame !== 'CO' && c.tipoExame !== 'REVISAO')
            ?? casos[0];
          if (!origem) throw new ServiceError(400, 'Receba um caso principal antes de vincular a Revisão.');
          dados = { ...dados, casoOrigemNumero: origem.numeroInterno };
        }
        const caso = await casoService.confirmarEntrada(dados, responsavel.value);
        confirmados.push({ tipo: 'CASO', caso, etiqueta: caso });
      }
      for (const entrada of ihqs) {
        let casoOrigemNumero = entrada.dados.casoOrigemNumero;
        const grupoHp = examesDaSolicitacao.value.find(
          (grupo) => grupo.codigoSolicitacao === entrada.dados.solicitacaoId.split(':', 1)[0] && grupo.tipoExameSugerido === 'HP',
        );
        if (grupoHp) {
          const casos = confirmados.filter((r) => r.tipo === 'CASO').map((r) => r.caso);
          casoOrigemNumero = casos.find((c) => c.tipoExame === 'HP')?.numeroInterno ?? grupoHp.casoNumero;
        }
        if (!casoOrigemNumero) {
          throw new ServiceError(400, grupoHp
            ? 'Receba o HP desta solicitação junto ou antes da IHQ.'
            : 'Selecione o histopatológico associado.');
        }
        const { caso, ihq, solicitacao } = await casoService.vincularIhq({ ...entrada.dados, casoOrigemNumero }, responsavel.value);
        confirmados.push({ tipo: 'IHQ', caso, ihq, etiqueta: etiquetaIhq(caso, ihq.codigoInternoIhq, solicitacao) });
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

  /** Cancela um grupo pendente e atualiza conferência, fila e contagem. */
  async function cancelarExame(solicitacaoId: string, motivo: string): Promise<boolean> {
    const cancelado = await aghuService.cancelarExame(solicitacaoId, motivo);
    exames.value = exames.value.filter((item) => item.id !== cancelado.id);
    examesDaSolicitacao.value = examesDaSolicitacao.value.map((item) => item.id === cancelado.id ? cancelado : item);
    pendentes.value = pendentes.value.filter((item) => item.id !== cancelado.id);
    await Promise.all([atualizarContagem(), carregarPendentes()]);
    if (exames.value.length === 0) {
      reiniciar();
      return true;
    }
    return false;
  }

  /** Registra o acionamento da equipe de plantão (congelação) para um caso da conferência. */
  async function registrarPlantao(numeroInterno: string): Promise<void> {
    const caso = await casoService.registrarAcionamentoPlantao(numeroInterno, responsavel.value);
    resultados.value = resultados.value.map((r) =>
      r.tipo === 'CASO' && r.caso.numeroInterno === numeroInterno ? { tipo: 'CASO', caso, etiqueta: caso } : r,
    );
  }

  /** Volta ao passo 1 descartando o recebimento em andamento. */
  function reiniciar(): void {
    passo.value = 0;
    exames.value = [];
    examesDaSolicitacao.value = [];
    examesDaSolicitacaoCarregados.value = false;
    resultados.value = [];
    mensagemLeitura.value = null;
    amostraBipada.value = null;
    grupoSelecionadoId.value = null;
    amostraBipadaSituacao.value = null;
    reinicios.value += 1;
  }

  return {
    passo,
    exames,
    examesDaSolicitacao,
    examesDaSolicitacaoCarregados,
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
    amostraBipada,
    grupoSelecionadoId,
    amostraBipadaSituacao,
    atualizarContagem,
    carregarPendentes,
    iniciarConferencia,
    lerCodigo,
    confirmarConferencia,
    cancelarExame,
    registrarPlantao,
    reiniciar,
  };
});
