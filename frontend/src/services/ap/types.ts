/**
 * Contratos dos serviços do Sistema AP.
 *
 * As views e stores dependem só destas interfaces. Hoje as implementações são mock
 * (`./mock`); a integração com o backend troca apenas as implementações exportadas em `./index.ts`.
 */
import type {
  AuditLog,
  CasoAp,
  CasoElegivelIhq,
  ConfirmarEntradaInput,
  DevolucaoDetalhada,
  ExameIhq,
  LeituraSolicitacao,
  RegistrarNaoConformidadeInput,
  ResolucaoCodigo,
  Responsavel,
  SituacaoDevolucao,
  SolicitacaoAghu,
  TipoImpressao,
  VincularIhqInput,
} from '../../types/ap';

/**
 * Erro de serviço no mesmo formato das respostas de erro do backend (`{"detail": "..."}`).
 */
export class ServiceError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ServiceError';
    this.status = status;
    this.detail = detail;
  }
}

/** Mensagem amigável a partir de qualquer erro capturado. */
export function mensagemDeErro(erro: unknown, padrao = 'Não foi possível concluir a operação.'): string {
  if (erro instanceof ServiceError) return erro.detail;
  return padrao;
}

/** Consulta de solicitações do AGHU (somente leitura). */
export interface AghuService {
  /** Solicitações aguardando recebimento. Lança 503 se o AGHU estiver indisponível. */
  listarPendentes(): Promise<SolicitacaoAghu[]>;
  /** Quantidade de solicitações aguardando recebimento (para o menu). */
  contarPendentes(): Promise<number>;
  /** Lê uma solicitação pelo número para a recepção. Lança 503 se o AGHU estiver indisponível. */
  lerSolicitacao(codigo: string): Promise<LeituraSolicitacao>;
}

/** Casos de anatomia patológica e ações da recepção sobre eles. */
export interface CasoService {
  listar(): Promise<CasoAp[]>;
  obter(numeroInterno: string): Promise<CasoAp | null>;
  /** Casos que podem receber a IHQ, com a indicação de elegibilidade. */
  buscarElegiveisIhq(termo: string): Promise<CasoElegivelIhq[]>;
  /** Confirma a entrada de um caso principal (HP, CG, CCV, CO). */
  confirmarEntrada(input: ConfirmarEntradaInput, usuario: Responsavel): Promise<CasoAp>;
  /** Vincula uma IHQ recebida a um caso existente, sem criar caso novo. */
  vincularIhq(input: VincularIhqInput, usuario: Responsavel): Promise<{ caso: CasoAp; ihq: ExameIhq }>;
  cancelar(numeroInterno: string, motivo: string, usuario: Responsavel): Promise<CasoAp>;
  registrarImpressao(numeroInterno: string, tipo: TipoImpressao, usuario: Responsavel): Promise<void>;
  registrarAcionamentoPlantao(numeroInterno: string, usuario: Responsavel): Promise<CasoAp>;
  /** Resolve um código lido/digitado (solicitação, caso, item de material ou IHQ). */
  resolverCodigo(codigo: string): Promise<ResolucaoCodigo>;
}

/** Não conformidades com devolução e o acompanhamento das devoluções. */
export interface NaoConformidadeService {
  registrar(input: RegistrarNaoConformidadeInput, usuario: Responsavel): Promise<DevolucaoDetalhada>;
  listarDevolucoes(): Promise<DevolucaoDetalhada[]>;
  atualizarSituacao(devolucaoId: number, situacao: SituacaoDevolucao, usuario: Responsavel): Promise<DevolucaoDetalhada>;
}

/** Consulta da trilha de auditoria (somente leitura). */
export interface AuditoriaService {
  listar(): Promise<AuditLog[]>;
}
