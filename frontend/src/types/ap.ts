/**
 * Tipos de domínio do Sistema de Anatomia Patológica (AP).
 *
 * Os nomes de entidades, campos e códigos seguem `docs/especificacao/04-modelo-dados.md`,
 * convertidos para camelCase. Datas são strings ISO 8601.
 */

// ---------------------------------------------------------------------------
// Domínios controlados
// ---------------------------------------------------------------------------

/** Tipos de exame (tabela `tipo_exame`). IHQ é complementar: nunca vira caso próprio. */
export type TipoExame = 'HP' | 'CG' | 'CCV' | 'CO' | 'IHQ';

/** Tipos que originam um `caso_ap`. */
export type TipoCasoPrincipal = Exclude<TipoExame, 'IHQ'>;

/** Etapas do fluxo (tabela `etapa`). */
export type EtapaCodigo =
  | 'RECEPCAO'
  | 'MACROSCOPIA'
  | 'CONGELACAO'
  | 'PROCESSAMENTO'
  | 'IHQ'
  | 'TRIAGEM_CITO'
  | 'MICROSCOPIA'
  | 'APROVACAO'
  | 'ARQUIVO'
  | 'EXTERNO';

/** Status operacionais do caso (`caso_ap.status`). */
export type StatusCaso =
  | 'RECEBIDO'
  | 'EM_MACROSCOPIA'
  | 'EM_CONGELACAO'
  | 'EM_PROCESSAMENTO'
  | 'EM_IHQ'
  | 'IHQ_AGUARDANDO_EXTERNO'
  | 'EM_MICROSCOPIA'
  | 'AGUARDANDO_APROVACAO'
  | 'LAUDO_CONCLUIDO'
  | 'EM_ARQUIVAMENTO'
  | 'ARQUIVADO'
  | 'DEVOLVIDO'
  | 'CANCELADO';

/** Origem do atendimento/material (`solicitacao_aghu.origem`). */
export type OrigemAtendimento = 'AMBULATORIO' | 'INTERNACAO' | 'BLOCO_CIRURGICO' | 'EXTERNO';

/** Situação local da solicitação AGHU diante da recepção do SAP. */
export type SituacaoRecepcaoSolicitacao = 'AGUARDANDO_RECEBIMENTO' | 'RECEBIDA' | 'DEVOLVIDA';

/** Resultado da conferência (`conferencia_recebimento.resultado`). */
export type ResultadoConferencia = 'ACEITA' | 'REJEITADA' | 'PENDENTE';

/** Situação da execução de uma etapa (`caso_etapa.status`). */
export type StatusEtapaCaso = 'PENDENTE' | 'EM_ANDAMENTO' | 'CONCLUIDA' | 'CONCLUIDA_EXTERNAMENTE' | 'DISPENSADA';

/** Tipos de item material (`item_material.tipo_item`). */
export type TipoItemMaterial = 'AMOSTRA' | 'FRAGMENTO' | 'BLOCO' | 'CELL_BLOCK' | 'LAMINA';

/** Origem do item material (`item_material.origem`). */
export type OrigemItemMaterial = 'ROTINA' | 'COMPLEMENTAR' | 'EXTERNA' | 'CONGELACAO';

/** Status do item material (`item_material.status`). */
export type StatusItemMaterial =
  | 'DISPONIVEL'
  | 'EM_PROCESSAMENTO'
  | 'EM_USO'
  | 'ARQUIVADO'
  | 'EMPRESTADO'
  | 'DESCARTADO_CONFORME_REGRA';

/** Catálogo de tipos de não conformidade (`tipo_nao_conformidade.codigo`). */
export type TipoNaoConformidadeCodigo =
  | 'SEM_ETIQUETA_AGHU'
  | 'IDENTIFICACAO_DIVERGENTE'
  | 'QUANTIDADE_DIVERGENTE'
  | 'MATERIAL_INADEQUADO'
  | 'RECIPIENTE_DANIFICADO'
  | 'FIXACAO_INADEQUADA'
  | 'REQUISICAO_INCOMPLETA'
  | 'OUTRO';

/** Status da não conformidade (`nao_conformidade.status`). */
export type StatusNaoConformidade = 'ABERTA' | 'EM_TRATAMENTO' | 'RESOLVIDA' | 'CANCELADA';

/** Situação da devolução (`devolucao.status`). */
export type SituacaoDevolucao = 'AGUARDANDO_NOVA_AMOSTRA' | 'NOVA_AMOSTRA_RECEBIDA' | 'ENCERRADA';

/** Status da IHQ (`exame_ihq.status`). */
export type StatusExameIhq =
  | 'SOLICITADA'
  | 'EM_EXECUCAO_INTERNA'
  | 'AGUARDANDO_EXTERNO'
  | 'RESULTADO_RECEBIDO'
  | 'RESULTADO_REGISTRADO'
  | 'RETORNADA_MICROSCOPIA';

/** Categorias da trilha de auditoria (`audit_logs`). */
export type CategoriaAuditoria = 'SEGURANCA' | 'NEGOCIO_CLINICO' | 'CONFIGURACAO';

/** Tipos de impressão registrados no histórico. */
export type TipoImpressao = 'ETIQUETAS' | 'FICHA_TRABALHO';

// ---------------------------------------------------------------------------
// Entidades
// ---------------------------------------------------------------------------

/** Usuário responsável por uma ação (vem sempre da sessão, nunca digitado). */
export interface Responsavel {
  login: string;
  nome: string;
}

/** Solicitação AGHU com os dados do paciente e do item/material (somente leitura no SAP). */
export interface SolicitacaoAghu {
  codigoSolicitacao: string;
  prontuario: string;
  nomePaciente: string;
  /** Data de nascimento (AAAA-MM-DD). */
  dataNascimento: string;
  sexo: 'Feminino' | 'Masculino';
  origem: OrigemAtendimento;
  unidade: string;
  especialidade: string;
  nomeSolicitante: string;
  dataSolicitacao: string;
  siglaExame: string;
  nomeExame: string;
  /** Tipo de exame identificado a partir do exame do AGHU. */
  tipoExameSugerido: TipoExame;
  descricaoMaterial: string;
  informacoesClinicas: string;
  statusAghuDescricao: string;
  situacaoRecepcao: SituacaoRecepcaoSolicitacao;
  /** Caso criado a partir da solicitação (casos principais). */
  casoNumero?: string;
  /** IHQ registrada a partir da solicitação e o caso de origem. */
  ihqCodigo?: string;
  ihqCasoNumero?: string;
  /** Devolução que encerrou a solicitação na recepção. */
  devolucaoId?: number;
}

/** Itens da conferência física da amostra. */
export interface ItensConferencia {
  identificacaoConfere: boolean;
  materialConfere: boolean;
  quantidadeConfere: boolean;
  recipienteAdequado: boolean;
}

/** Conferência de recebimento (`conferencia_recebimento`). */
export interface ConferenciaRecebimento extends ItensConferencia {
  id: number;
  solicitacaoCodigo: string;
  casoNumero?: string;
  resultado: ResultadoConferencia;
  observacao?: string;
  conferidoPor: Responsavel;
  conferidoEm: string;
}

/** Item da árvore de materiais (`item_material`). */
export interface ItemMaterial {
  /** Código único do item (`codigo_item`), usado no código de barras. */
  codigo: string;
  tipoItem: TipoItemMaterial;
  rotulo: string;
  descricao?: string;
  origem: OrigemItemMaterial;
  status: StatusItemMaterial;
  criadoPor: Responsavel;
  criadoEm: string;
  filhos: ItemMaterial[];
}

/** Passagem do caso por uma etapa (`caso_etapa`). */
export interface CasoEtapa {
  etapa: EtapaCodigo;
  sequencia: number;
  status: StatusEtapaCaso;
  iniciadaEm?: string;
  concluidaEm?: string;
  responsavelInicio?: Responsavel;
  responsavelFim?: Responsavel;
  observacao?: string;
}

/** Par rótulo/valor exibido nas abas somente leitura das etapas. */
export interface CampoRegistro {
  rotulo: string;
  valor: string;
}

/** Registro técnico/diagnóstico de uma etapa posterior à recepção (somente leitura neste fluxo). */
export interface RegistroEtapa {
  etapa: EtapaCodigo;
  titulo: string;
  campos: CampoRegistro[];
  texto?: string;
  responsavel: Responsavel;
  registradoEm: string;
}

/** Evento imutável da linha do tempo do caso (`historico_caso`). */
export interface HistoricoCaso {
  id: number;
  evento: string;
  titulo: string;
  descricao?: string;
  setor: string;
  usuario: Responsavel;
  ocorridoEm: string;
}

/** IHQ vinculada ao caso de origem (`exame_ihq`). */
export interface ExameIhq {
  codigoInternoIhq: string;
  status: StatusExameIhq;
  solicitacaoAghuCodigo: string;
  recebidaEm: string;
  registradaPor: Responsavel;
  anticorpos: string[];
  laboratorioExterno?: string;
  resultadoTecnico?: string;
  observacao?: string;
}

/** Não conformidade (`nao_conformidade`). */
export interface NaoConformidade {
  id: number;
  casoNumero?: string;
  solicitacaoCodigo?: string;
  tipo: TipoNaoConformidadeCodigo;
  descricao: string;
  cmce?: string;
  setor: string;
  /** Etapa em que foi identificada, como exibida ao usuário (ex.: "Recepção (conferência)"). */
  etapa: string;
  etapaCodigo: EtapaCodigo;
  unidadeOrigem: string;
  registradoPor: Responsavel;
  registradoEm: string;
  status: StatusNaoConformidade;
}

/** Devolução do material à unidade de origem (`devolucao`). */
export interface Devolucao {
  id: number;
  naoConformidadeId: number;
  casoNumero?: string;
  solicitacaoCodigo?: string;
  unidadeOrigem: string;
  devolvidoPor: Responsavel;
  recebidoPorNome: string;
  novaAmostraSolicitada: boolean;
  situacao: SituacaoDevolucao;
  devolvidaEm: string;
}

/** Cancelamento administrativo do caso (`cancelamento`). */
export interface Cancelamento {
  motivo: string;
  canceladoPor: Responsavel;
  canceladoEm: string;
}

/** Caso de anatomia patológica (`caso_ap`) com suas relações para exibição. */
export interface CasoAp {
  numeroInterno: string;
  tipoExame: TipoCasoPrincipal;
  /** Cópia da solicitação AGHU que originou o caso. */
  solicitacao: SolicitacaoAghu;
  status: StatusCaso;
  /** Etapa atual; `null` quando o fluxo terminou (arquivado). */
  etapaAtual: EtapaCodigo | null;
  etapaAtualDesde: string;
  dataEntradaSap: string;
  responsavelEntrada: Responsavel;
  urgente: boolean;
  motivoUrgencia?: string;
  procedimento: string;
  quantidade: number;
  observacoes?: string;
  conferencia?: ConferenciaRecebimento;
  etapas: CasoEtapa[];
  registros: RegistroEtapa[];
  materiais: ItemMaterial[];
  ihqs: ExameIhq[];
  naoConformidades: NaoConformidade[];
  devolucoes: Devolucao[];
  cancelamento?: Cancelamento;
  historico: HistoricoCaso[];
  plantaoAcionadoEm?: string;
}

/** Registro da trilha de auditoria (espelha `audit_logs` / `registrar_auditoria()`). */
export interface AuditLog {
  id: number;
  usuario: Responsavel;
  categoria: CategoriaAuditoria;
  acao: string;
  recurso: string;
  dadosAnteriores: Record<string, unknown> | null;
  dadosNovos: Record<string, unknown> | null;
  ocorridoEm: string;
}

/** Devolução com a não conformidade que a originou, para a tela de rejeições e devoluções. */
export interface DevolucaoDetalhada extends Devolucao {
  naoConformidade: NaoConformidade;
  /** `true` quando a devolução ocorreu na recepção, antes de existir caso. */
  rejeicaoNaRecepcao: boolean;
}

// ---------------------------------------------------------------------------
// Entradas das operações
// ---------------------------------------------------------------------------

/** Confirmação da entrada de um caso principal. */
export interface ConfirmarEntradaInput {
  solicitacaoCodigo: string;
  conferencia: ItensConferencia;
  tipoExame: TipoCasoPrincipal;
  quantidade: number;
  urgente: boolean;
  motivoUrgencia?: string;
  procedimento: string;
  observacoes?: string;
}

/** Confirmação de uma IHQ vinculada a um caso existente. */
export interface VincularIhqInput {
  solicitacaoCodigo: string;
  conferencia: ItensConferencia;
  casoOrigemNumero: string;
  /** Confirmação explícita quando o prontuário do caso difere do da solicitação. */
  divergenciaConfirmada: boolean;
  observacoes?: string;
}

/** Onde a não conformidade foi identificada. */
export type ContextoNaoConformidade =
  | { tipo: 'SEM_ETIQUETA' }
  | { tipo: 'SOLICITACAO'; solicitacaoCodigo: string; conferencia: ItensConferencia }
  | { tipo: 'CASO'; casoNumero: string };

/** Registro de não conformidade com a devolução obrigatória. */
export interface RegistrarNaoConformidadeInput {
  contexto: ContextoNaoConformidade;
  tipo: TipoNaoConformidadeCodigo;
  descricao: string;
  cmce?: string;
  /** Exigida quando não há solicitação nem caso. */
  unidadeOrigem?: string;
  recebidoPorNome: string;
  novaAmostraSolicitada: boolean;
}

// ---------------------------------------------------------------------------
// Resultados das operações
// ---------------------------------------------------------------------------

/** Resultado da leitura de uma solicitação na recepção. */
export type LeituraSolicitacao =
  | { tipo: 'PENDENTE'; solicitacao: SolicitacaoAghu }
  | { tipo: 'RECEBIDA'; solicitacao: SolicitacaoAghu; casoNumero: string }
  | { tipo: 'DEVOLVIDA'; solicitacao: SolicitacaoAghu; devolvidaEm: string; tipoNaoConformidade: TipoNaoConformidadeCodigo }
  | { tipo: 'NAO_ENCONTRADA' };

/** Resultado da leitura global de código (F2). */
export type ResolucaoCodigo =
  | LeituraSolicitacao
  | { tipo: 'CASO'; casoNumero: string; aba?: 'materiais' | 'ihq'; itemCodigo?: string };

/** Resultado da confirmação na recepção. */
export type ResultadoRecepcao =
  | { tipo: 'CASO'; caso: CasoAp }
  | { tipo: 'IHQ'; caso: CasoAp; ihq: ExameIhq };

/** Caso elegível como origem de uma IHQ. */
export interface CasoElegivelIhq {
  numeroInterno: string;
  nomePaciente: string;
  prontuario: string;
  descricaoMaterial: string;
  status: StatusCaso;
  elegivel: boolean;
  motivoInelegivel?: string;
}
