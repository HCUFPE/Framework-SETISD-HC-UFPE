/**
 * Contratos TypeScript da Fila de Exames (TASK-012).
 * Seção 4 de docs/especificacao/05-interfaces.md + detalhe de src/schemas/fila.py.
 * Respostas da fila em camelCase; query params e a busca no AGHU em snake_case.
 */

export type StatusHigienizacao =
  | 'VALIDA'
  | 'DUPLICADA'
  | 'DIVERGENCIA_EXAME'
  | 'NAO_ENCONTRADA'
  | 'JA_REALIZADA';

export type StatusOperacional =
  | 'NA_FILA'
  | 'AGUARDANDO_CONFIRMACAO_24H'
  | 'CONFIRMADO_AGENDADO_AGHU'
  | 'SEM_RESPOSTA_24H'
  | 'CANCELADO';

export type TipoAlerta =
  | 'INCOMPATIBILIDADE'
  | 'JANELA_RETORNO'
  | 'ANTECEDENCIA_PREPARO'
  | 'JEJUM_CLINICO'
  | 'IDADE_MAMOGRAFIA'
  | 'PRAZO_24H_VENCIDO'
  | 'DUPLICIDADE';

export type SeveridadeAlerta = 'ALTA' | 'MEDIA' | 'INFO';

export type RegiaoGeografica = 'CAPITAL' | 'RMR' | 'INTERIOR' | 'NAO_INFORMADO';

export interface IAlertaExame {
  tipo: TipoAlerta;
  severidade: SeveridadeAlerta;
  mensagem: string;
}

/** Datas-hora (contatoIniciadoEm, prazoConfirmacaoEm, dataAgendadaAghu) chegam em UTC sem "Z". */
export interface IItemFila {
  id: number;
  codigoSolicitacao: string;
  codigoExame: string | null;
  nomeExame: string | null;
  prontuario: string | null;
  nomePaciente: string;
  telefoneContato: string | null;
  municipio: string | null;
  regiaoGeografica: RegiaoGeografica;
  utilizaTfd: boolean;
  unidadeSolicitante: string | null;
  dataSolicitacao: string | null;
  dataRetornoMedico: string | null;
  statusHigienizacao: StatusHigienizacao;
  statusOperacional: StatusOperacional;
  scorePrioridade: number;
  motivosPrioridade: string[];
  alertas: IAlertaExame[];
  contatoIniciadoEm: string | null;
  prazoConfirmacaoEm: string | null;
  dataAgendadaAghu: string | null;
  preparoOrientado: boolean;
}

/** Outro exame do mesmo prontuário (``OutroExame``). */
export interface IOutroExame {
  codigoSolicitacao: string | null;
  codigoExame: string | null;
  nomeExame: string | null;
  origem: 'FILA' | 'AGHU';
  dataAgendada: string | null;
  statusOperacional: StatusOperacional | null;
}

/** Resposta de GET /api/exames/fila/{id} e dos PATCH de status/vínculo (``ItemFilaDetalhe``). */
export interface IItemFilaDetalhe extends IItemFila {
  outrosExames: IOutroExame[];
  orientacoesPreparo: string | null;
}

/** Corpo de PATCH /api/exames/fila/{id}/status. dataAgendadaAghu em ISO 8601 com fuso. */
export interface IAtualizarStatusRequest {
  statusOperacional: StatusOperacional;
  dataAgendadaAghu?: string;
  preparoOrientado?: boolean;
  observacoes?: string;
}

/** Corpo de PATCH /api/exames/fila/{id}/vincular-solicitacao. */
export interface IVincularSolicitacaoRequest {
  codigoSolicitacao: string;
  codigoExame: string;
}

/** Query params de GET /api/exames/fila (snake_case). */
export interface IFiltrosFila {
  codigo_exame?: string;
  unidade?: string;
  status_operacional?: StatusOperacional;
  status_higienizacao?: StatusHigienizacao;
  municipio?: string;
  regiao?: RegiaoGeografica;
  apenas_tfd?: boolean;
  apenas_24h_vencidos?: boolean;
  busca?: string;
}

/** Query params de GET /api/exames/aghu/buscar (snake_case). */
export interface IBuscaAghuParams {
  prontuario?: string;
  codigo_solicitacao?: string;
  nome?: string;
}

/** Linha devolvida por GET /api/exames/aghu/buscar (provider AGHU, snake_case). */
export interface ISolicitacaoAghu {
  prontuario: string | null;
  nome: string | null;
  telefone: string | null;
  cidade: string | null;
  estado: string | null;
  codigo_solicitacao: string;
  data_solicitacao: string | null;
  unidade_solicitante: string | null;
  codigo_exame: string;
  nome_exame: string | null;
}

/** Espelha fila_controller.TRANSICOES_PERMITIDAS (fluxo validado em 06/11); o backend valida de novo. */
export const TRANSICOES_PERMITIDAS: Record<StatusOperacional, StatusOperacional[]> = {
  NA_FILA: ['AGUARDANDO_CONFIRMACAO_24H', 'CANCELADO'],
  AGUARDANDO_CONFIRMACAO_24H: ['CONFIRMADO_AGENDADO_AGHU', 'SEM_RESPOSTA_24H', 'CANCELADO'],
  SEM_RESPOSTA_24H: ['NA_FILA', 'CANCELADO'],
  CONFIRMADO_AGENDADO_AGHU: [],
  CANCELADO: [],
};

/** Espelha fila_controller.HIGIENIZACAO_VINCULAVEL (busca ativa / vínculo). */
export const HIGIENIZACAO_VINCULAVEL: StatusHigienizacao[] = ['NAO_ENCONTRADA', 'DIVERGENCIA_EXAME'];

export interface IRegraPrioridade {
  id: number;
  codigo: string;
  nome: string;
  tipoCriterio: 'CLINICA' | 'GRUPO_CLINICO' | 'VULNERAVEL' | 'AFINIDADE_EXAME' | 'RETORNO_PROXIMO';
  valorMatch: string;
  peso: number;
  ativo: boolean;
}

export interface IRegraExame {
  id: number;
  codigoExame: string;
  nomeExame: string;
  unidadeExecutora: string | null;
  antecedenciaMinimaDias: number;
  janelaRetornoMaxHoras: number | null;
  exigeJejum: boolean;
  priorizarManhaDiabetico: boolean;
  idadeMinimaAlerta: number | null;
  orientacoesPreparo: string | null;
  ativo: boolean;
}

export interface IIncompatibilidadeExame {
  id: number;
  codigoExameOrigem: string;
  codigoExameConflitante: string;
  tipoConflito: 'MESMO_DIA' | 'PREPARO' | 'INTERVALO_MINIMO';
  intervaloMinimoDias: number;
  motivo: string;
  ativo: boolean;
}

export interface IKpiDashboard {
  totalNaFila: number;
  aguardando24h: number;
  prazo24hVencidos: number;
  confirmadosAgendados: number;
  duplicidadesBarradas: number;
  divergenciasDetectadas: number;
  tempoMedioEsperaDias: number;
  filaPorExame: Array<{ exame: string; quantidade: number }>;
  filaPorRegiao: Array<{ regiao: string; quantidade: number }>;
}

/** Query params de GET /api/dashboard/kpis (ISO 8601; sem offset = UTC). */
export interface IFiltrosKpi {
  data_inicio?: string;
  data_fim?: string;
  codigo_exame?: string;
}
