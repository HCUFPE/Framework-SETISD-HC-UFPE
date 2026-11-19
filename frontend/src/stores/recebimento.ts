import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import api from '../services/api';

export interface ExameRegistrado {
  numero_interno: string | null;
  tipo: string;
  status: 'RECEBIDO' | 'DEVOLVIDO';
  urgente: boolean | null;
  recebido_por: string;
  recebido_em: string;
}

export interface FalhaRecebimento {
  tipo: string;
  amostras: number[];
  codigo_http: number;
  detail: string;
}

export interface ConferenciaGravada {
  conferido_por: string;
  conferido_em: string;
}

export interface NaoConformidadeGravada {
  motivo: string;
  observacao: string;
  numero_cmce: string | null;
  medico_solicitante: string | null;
  resolvida: boolean;
  resolvida_por: string | null;
  resolvida_em: string | null;
  registrado_por: string;
  registrado_em: string;
}

export interface ExameDetalhado extends ExameRegistrado {
  quantidade_pecas: number | null;
  procedimento: string | null;
  referencia_hp: string | null;
  amostras: {
    numero_amostra: number;
    sigla_exame: string;
    descricao_material: string | null;
    descricao_informada: string | null;
    recebida: boolean;
    conferencia: ConferenciaGravada | null;
  }[];
  nao_conformidades: NaoConformidadeGravada[];
}

export interface AmostraSolicitacao {
  numero_amostra: number;
  bancada: string;
  codigo_lab: string;
  sigla_exame: string;
  nome_exame: string;
  descricao_material: string | null;
  exige_descricao: boolean;
  cod_status_item: string;
  status_item_exame: string;
  recebivel: boolean;
  motivo_bloqueio: string | null;
  recebida: boolean;
  material_informado: string | null;
  conferencia: ConferenciaGravada | null;
}

export interface Solicitacao {
  codigo: string;
  situacao: SituacaoSolicitacao;
  urgente: boolean;
  numero_amostra_lida: number | null;
  data_solicitacao: string | null;
  paciente: {
    nome: string;
    prontuario: string | null;
    data_nascimento: string | null;
    idade: number | null;
  };
  origem: string;
  especialidade: string | null;
  convenio: string | null;
  unidade: string | null;
  informacoes_clinica: string | null;
  amostras: AmostraSolicitacao[];
  exames: ExameDetalhado[];
}

export type SituacaoSolicitacao = 'AGUARDANDO' | 'PARCIAL' | 'RECEBIDA' | 'DEVOLVIDA' | 'BLOQUEADA';

export const SITUACOES: Record<SituacaoSolicitacao, { rotulo: string; classe: string }> = {
  AGUARDANDO: { rotulo: 'Aguardando recebimento', classe: 'bg-blue-100 text-blue-800' },
  PARCIAL: { rotulo: 'Recebida em parte', classe: 'bg-yellow-100 text-yellow-800' },
  RECEBIDA: { rotulo: 'Recebida', classe: 'bg-green-100 text-green-800' },
  DEVOLVIDA: { rotulo: 'Devolvida à origem', classe: 'bg-orange-100 text-orange-800' },
  BLOQUEADA: { rotulo: 'Sem amostra recebível', classe: 'bg-gray-200 text-gray-700' },
};

export interface LinhaDaLista {
  codigo: string;
  data_solicitacao: string | null;
  paciente: { nome: string; prontuario: string | null; idade: number | null };
  urgente: boolean;
  origem: string;
  especialidade: string | null;
  unidade: string | null;
  bancadas: string[];
  total_amostras: number;
  amostras_recebiveis: number;
  numeros_internos: string[];
  situacao: SituacaoSolicitacao;
}

/** Colunas da lista que o backend sabe ordenar e filtrar (as que vêm do AGHU). */
export type ColunaDaLista = 'codigo' | 'data' | 'paciente' | 'prontuario' | 'origem' | 'clinica';
export type DirecaoDaOrdenacao = 'asc' | 'desc';

export interface OrdenacaoDaLista {
  coluna: ColunaDaLista;
  direcao: DirecaoDaOrdenacao;
}

export interface FiltrosDaLista {
  codigo: string;
  data: string;
  paciente: string;
  prontuario: string;
  origem: string;
  clinica: string;
  bancada: string;
}

const filtrosVazios = (): FiltrosDaLista => ({
  codigo: '',
  data: '',
  paciente: '',
  prontuario: '',
  origem: '',
  clinica: '',
  bancada: '',
});

export interface PaginaDaLista {
  pagina: number;
  por_pagina: number;
  total: number;
  total_paginas: number;
  solicitacoes: LinhaDaLista[];
}

export interface LinhaConferencia extends AmostraSolicitacao {
  receber: boolean;
  descricao_informada: string;
}

export interface ItemDeLista {
  id: number;
  descricao: string;
}

export interface DadosNaoConformidade {
  motivo_id: number;
  observacao: string;
  numero_cmce: string | null;
  medico_solicitante: string | null;
}

export type ResultadoOperacao =
  | { tipo: 'recebimento'; codigo: string; exames: ExameRegistrado[]; falhas: FalhaRecebimento[] }
  | { tipo: 'devolucao'; codigo: string; motivo: string };

const BANCADA_HP = 'HP';
const BANCADA_IHQ = 'IHQ';
const POR_PAGINA = 10;
const TOTAL_ITENS_CHECKLIST = 3;
const PADRAO_REFERENCIA_HP = /^HP-\d{4}\/[1-9]\d*$/;

/** Extrai a mensagem do campo `detail` das respostas de erro da API. */
export function mensagemDeErro(erro: any, padrao: string): string {
  const detalhe = erro?.response?.data?.detail;
  return typeof detalhe === 'string' ? detalhe : padrao;
}

export type TipoErroBusca = 'nao_encontrada' | 'indisponivel' | 'outro';

/**
 * Separa a etiqueta inexistente (404) das falhas técnicas, para a tela não tratar uma queda do
 * AGHU ou da rede como se a etiqueta não existisse.
 */
export function classificarErroDaBusca(erro: any): { tipo: TipoErroBusca; mensagem: string } {
  const status: number | undefined = erro?.response?.status;
  if (status === 404) {
    const detalhe = mensagemDeErro(erro, 'Etiqueta não encontrada.');
    return {
      tipo: 'nao_encontrada',
      mensagem: `${detalhe} Confira se a etiqueta foi lida corretamente.`,
    };
  }
  if (!erro?.response) {
    return {
      tipo: 'indisponivel',
      mensagem: 'Sem comunicação com o servidor. Verifique a conexão e tente novamente.',
    };
  }
  if (status !== undefined && status >= 500) {
    const detalhe = mensagemDeErro(erro, 'Não foi possível consultar o AGHU agora.');
    return {
      tipo: 'indisponivel',
      mensagem: `${detalhe} Isso não significa que a etiqueta não existe. Tente novamente.`,
    };
  }
  return { tipo: 'outro', mensagem: mensagemDeErro(erro, 'Não foi possível buscar a solicitação.') };
}

/** Cria a linha da tabela. O checklist é do recebimento e fica fora da linha. */
function criarLinha(amostra: AmostraSolicitacao): LinhaConferencia {
  return {
    ...amostra,
    receber: amostra.recebivel,
    descricao_informada: '',
  };
}

export const useRecebimentoStore = defineStore('recebimento', () => {
  const solicitacao = ref<Solicitacao | null>(null);
  const linhas = ref<LinhaConferencia[]>([]);
  const motivos = ref<ItemDeLista[]>([]);
  const procedimentosHp = ref<ItemDeLista[]>([]);
  const resultado = ref<ResultadoOperacao | null>(null);
  const carregando = ref(false);
  const gravando = ref(false);

  const lista = ref<PaginaDaLista | null>(null);
  const carregandoLista = ref(false);
  const filtrosDaLista = ref<FiltrosDaLista>(filtrosVazios());
  const ordenacaoDaLista = ref<OrdenacaoDaLista | null>(null);
  const filtrosAtivos = computed(() =>
    Object.values(filtrosDaLista.value).some((valor) => valor.trim() !== ''),
  );
  let ultimaConsultaDaLista = 0;

  // Checklist único do recebimento. Começa desmarcado para exigir a conferência.
  const siglaConfere = ref(false);
  const descricaoConfere = ref(false);
  const recipientesConfere = ref(false);

  // Dados que a recepção acrescenta. Começam vazios para exigir o preenchimento (RNF009).
  const quantidadePecas = ref<number | null>(null);
  const urgente = ref<boolean | null>(null);
  const procedimentoId = ref<number | null>(null);
  const referenciaHp = ref('');

  const marcadas = computed(() => linhas.value.filter((linha) => linha.receber));
  const recebeHp = computed(() => marcadas.value.some((linha) => linha.bancada === BANCADA_HP));
  const recebeIhq = computed(() => marcadas.value.some((linha) => linha.bancada === BANCADA_IHQ));

  const dadosHpCompletos = computed(
    () =>
      !recebeHp.value ||
      (Number.isInteger(quantidadePecas.value) &&
        (quantidadePecas.value as number) >= 1 &&
        urgente.value !== null &&
        procedimentoId.value !== null),
  );

  const referenciaHpValida = computed(() => {
    const valor = referenciaHp.value.trim();
    return !recebeIhq.value || !valor || PADRAO_REFERENCIA_HP.test(valor);
  });

  const recebiveis = computed(() => linhas.value.filter((linha) => linha.recebivel));

  const itensConferidos = computed(
    () => [siglaConfere.value, descricaoConfere.value, recipientesConfere.value].filter(Boolean).length,
  );

  const materiaisCompletos = computed(() =>
    marcadas.value.every(
      (linha) => !linha.exige_descricao || linha.descricao_informada.trim().length > 0,
    ),
  );

  const checklistCompleto = computed(
    () => marcadas.value.length > 0 && itensConferidos.value === TOTAL_ITENS_CHECKLIST,
  );

  /** Uma amostra marcada depois da confirmação não foi conferida, então o checklist recomeça. */
  function limparChecklist() {
    siglaConfere.value = false;
    descricaoConfere.value = false;
    recipientesConfere.value = false;
  }

  watch(
    () => marcadas.value.map((linha) => linha.numero_amostra),
    (atuais, anteriores) => {
      if (solicitacao.value && atuais.some((numero) => !anteriores.includes(numero))) {
        limparChecklist();
      }
    },
  );

  const podeConcluir = computed(
    () =>
      checklistCompleto.value &&
      materiaisCompletos.value &&
      dadosHpCompletos.value &&
      referenciaHpValida.value,
  );

  const podeDevolver = computed(() => {
    if (!solicitacao.value) return false;
    const recebidos = solicitacao.value.exames
      .filter((exame) => exame.status === 'RECEBIDO')
      .map((exame) => exame.tipo);
    return linhas.value.some((linha) => !recebidos.includes(linha.bancada));
  });

  /** Limpa a conferência em andamento, mantendo o último resultado em destaque. */
  function limparConferencia() {
    solicitacao.value = null;
    linhas.value = [];
    limparChecklist();
    quantidadePecas.value = null;
    urgente.value = null;
    procedimentoId.value = null;
    referenciaHp.value = '';
  }

  /**
   * Busca a solicitação pelo código lido ou digitado.
   * Ler outro frasco da solicitação aberta só destaca a amostra e mantém o que já foi preenchido.
   */
  async function buscar(codigo: string) {
    carregando.value = true;
    try {
      const { data } = await api.get<Solicitacao>(
        `/api/recebimento/solicitacoes/${encodeURIComponent(codigo)}`,
      );
      const mesmaSolicitacao = solicitacao.value?.codigo === data.codigo;
      if (!mesmaSolicitacao) {
        limparConferencia();
        linhas.value = data.amostras.map(criarLinha);
      }
      solicitacao.value = data;
      resultado.value = null;
    } finally {
      carregando.value = false;
    }
  }

    /**
   * Carrega uma página da lista inicial, com os filtros e a ordenação atuais, que o backend
   * aplica antes de paginar. Se o usuário trocar de página, vale a última consulta.
   */
  async function carregarLista(pagina: number = lista.value?.pagina ?? 1) {
    const consulta = ++ultimaConsultaDaLista;
    carregandoLista.value = true;
    try {
      const params: Record<string, string | number | boolean> = {
        pagina,
        por_pagina: POR_PAGINA,
        somente_recebiveis: false,
      };
      for (const [coluna, valor] of Object.entries(filtrosDaLista.value)) {
        const texto = valor.trim();
        if (texto) params[`filtro_${coluna}`] = texto;
      }
      if (ordenacaoDaLista.value) {
        params.ordenar_por = ordenacaoDaLista.value.coluna;
        params.direcao = ordenacaoDaLista.value.direcao;
      }
      const { data } = await api.get<PaginaDaLista>('/api/recebimento/solicitacoes', { params });
      if (consulta === ultimaConsultaDaLista) lista.value = data;
    } finally {
      if (consulta === ultimaConsultaDaLista) carregandoLista.value = false;
    }
  }

  /**
   * Alterna a ordenação da coluna: crescente, decrescente e, no terceiro clique, volta à ordem
   * padrão (urgências primeiro e depois as mais recentes). Recarrega a partir da página 1.
   */
  async function alternarOrdenacao(coluna: ColunaDaLista) {
    const atual = ordenacaoDaLista.value;
    if (!atual || atual.coluna !== coluna) {
      ordenacaoDaLista.value = { coluna, direcao: 'asc' };
    } else if (atual.direcao === 'asc') {
      ordenacaoDaLista.value = { coluna, direcao: 'desc' };
    } else {
      ordenacaoDaLista.value = null;
    }
    await carregarLista(1);
  }

  /** Remove todos os filtros e a ordenação e volta à lista padrão. */
  async function limparFiltrosDaLista() {
    filtrosDaLista.value = filtrosVazios();
    ordenacaoDaLista.value = null;
    await carregarLista(1);
  }

  /** Carrega as listas controladas de motivos e de procedimentos de HP. */
  async function carregarListas() {
    const [respostaMotivos, respostaProcedimentos] = await Promise.all([
      api.get<ItemDeLista[]>('/api/recebimento/motivos-nao-conformidade'),
      api.get<ItemDeLista[]>('/api/recebimento/procedimentos-hp'),
    ]);
    motivos.value = respostaMotivos.data;
    procedimentosHp.value = respostaProcedimentos.data;
  }

  /**
   * Conclui o recebimento das amostras marcadas e guarda os números gerados.
   * Cada bancada é gravada separadamente: se alguma falhar, as demais continuam gravadas e as
   * falhas voltam na lista retornada, com a solicitação reaberta para mostrar o que falta.
   */
  async function concluirRecebimento(): Promise<FalhaRecebimento[]> {
    if (!solicitacao.value) return [];
    gravando.value = true;
    try {
      const codigoRecebido = solicitacao.value.codigo;
      const amostras = linhas.value
        .filter((linha) => linha.recebivel)
        .map((linha) => ({
          numero_amostra: linha.numero_amostra,
          receber: linha.receber,
          descricao_informada: linha.exige_descricao ? linha.descricao_informada.trim() : null,
        }));
      const { data } = await api.post(
        `/api/recebimento/solicitacoes/${encodeURIComponent(codigoRecebido)}/recebimentos`,
        {
          amostras,
          sigla_confere: siglaConfere.value,
          descricao_confere: descricaoConfere.value,
          recipientes_confere: recipientesConfere.value,
          dados_hp: recebeHp.value
            ? {
                quantidade_pecas: quantidadePecas.value,
                urgente: urgente.value,
                procedimento_id: procedimentoId.value,
              }
            : null,
          referencia_hp: recebeIhq.value ? referenciaHp.value.trim() || null : null,
        },
      );
      const falhas: FalhaRecebimento[] = data.falhas ?? [];
      limparConferencia();
      if (falhas.length) {
        // Reabre a solicitação para mostrar o que foi recebido e o que ainda pode ser recebido.
        try {
          await buscar(codigoRecebido);
        } catch {
          // O resultado abaixo já informa o que foi gravado e o que falhou.
        }
      }
      resultado.value = { tipo: 'recebimento', codigo: data.codigo, exames: data.exames, falhas };
      return falhas;
    } finally {
      gravando.value = false;
    }
  }

  /** Registra a não conformidade e a devolução da solicitação à origem. */
  async function registrarNaoConformidade(dados: DadosNaoConformidade) {
    if (!solicitacao.value) return;
    gravando.value = true;
    try {
      const { data } = await api.post(
        `/api/recebimento/solicitacoes/${encodeURIComponent(solicitacao.value.codigo)}/nao-conformidades`,
        dados,
      );
      resultado.value = { tipo: 'devolucao', codigo: data.codigo, motivo: data.motivo };
      limparConferencia();
    } finally {
      gravando.value = false;
    }
  }

  return {
    solicitacao,
    linhas,
    motivos,
    procedimentosHp,
    resultado,
    carregando,
    gravando,
    lista,
    carregandoLista,
    filtrosDaLista,
    ordenacaoDaLista,
    filtrosAtivos,
    carregarLista,
    alternarOrdenacao,
    limparFiltrosDaLista,
    quantidadePecas,
    urgente,
    procedimentoId,
    referenciaHp,
    recebeHp,
    recebeIhq,
    referenciaHpValida,
    marcadas,
    recebiveis,
    siglaConfere,
    descricaoConfere,
    recipientesConfere,
    itensConferidos,
    TOTAL_ITENS_CHECKLIST,
    podeConcluir,
    podeDevolver,
    limparConferencia,
    buscar,
    carregarListas,
    concluirRecebimento,
    registrarNaoConformidade,
  };
});
