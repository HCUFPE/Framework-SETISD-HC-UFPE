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
export type OrigemAtendimento = 'AMBULATORIO' | 'INTERNACAO' | 'CIRURGIA' | 'EXTERNO';

/** Códigos de status do item no AGHU (`cod_status_item`, ver `data/dicionario_dados.md`). */
export type CodStatusItemAghu = 'LI' | 'AC' | 'EX' | 'AE' | 'CA' | 'CO' | 'EC' | 'PE';

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
  | 'SEM_SOLICITACAO_OU_ETIQUETA'
  | 'EXAME_NAO_CORRESPONDE_MATERIAL'
  | 'FALTA_DESCRICAO_FRASCO'
  | 'IDENTIFICACAO_ILEGIVEL'
  | 'NUMERACAO_FRASCOS_DIVERGENTE'
  | 'QUANTIDADE_FRASCOS_DIVERGENTE'
  | 'LATERALIDADE_DIVERGENTE'
  | 'FALTA_CARIMBO_ASSINATURA'
  | 'ACONDICIONAMENTO_INADEQUADO'
  | 'SOLICITACOES_DUPLICADAS'
  | 'PECAS_NAO_DESCRITAS'
  | 'SISCAN_INCORRETO'
  | 'SEM_AGENDAMENTO_CMCE'
  | 'OUTROS';

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

/** Formatos de impressão física disponíveis no navegador. */
export type TipoImpressao = 'ETIQUETAS' | 'FICHA_TRABALHO';

// ---------------------------------------------------------------------------
// Entidades
// ---------------------------------------------------------------------------

/** Usuário responsável por uma ação (vem sempre da sessão, nunca digitado). */
export interface Responsavel {
  login: string;
  nome: string;
}

/** Amostra de uma solicitação AGHU (uma linha da view do AGHU). */
export interface AmostraAghu {
  /** `numero_amostra`: sequencial da amostra dentro da solicitação. */
  numeroAmostra: string;
  /** `sigla_exame` solicitado para a amostra. */
  siglaExame: string;
  /** `nome_exame` solicitado para a amostra. */
  nomeExame: string;
  /** `descricao_material`: pode vir vazia (exame CITO). */
  descricaoMaterial: string;
  /** `cod_status_item` (ver `STATUS_ITEM_AGHU`). */
  codStatusItem: string;
  /** `status_item_exame` como veio do AGHU. */
  statusItemDescricao: string;
}

/**
 * Grupo de amostras de um mesmo tipo de exame dentro de uma solicitação AGHU.
 *
 * A conferência é feita por solicitação, mas cada tipo de exame (HP, CG, CCV, CO, IHQ) é recebido,
 * devolvido e cancelado como uma unidade: todas as amostras do tipo juntas, gerando um caso (ou
 * um vínculo de IHQ). Tipos diferentes da mesma solicitação podem ser recebidos em momentos
 * diferentes. Somente leitura no SAP.
 */
export interface SolicitacaoAghu {
  /** Chave do grupo: `<codigoSolicitacao>:<tipoExame>` (ex.: "1479377:HP"). */
  id: string;
  /** Código da solicitação no AGHU (repete-se entre os exames da mesma solicitação). */
  codigoSolicitacao: string;
  /** Vazio para Paciente Externo. */
  prontuario: string;
  /** Nome completo do paciente, como veio do AGHU. */
  nomePaciente: string;
  /** Data de nascimento (AAAA-MM-DD). Pode vir vazia. */
  dataNascimento: string;
  /** Nulo quando a origem do AGHU não é reconhecida. */
  origem: OrigemAtendimento | null;
  unidade: string;
  /** Vazia para Paciente Externo. */
  especialidade: string;
  /** Data da solicitação (AAAA-MM-DD, sem hora). */
  dataSolicitacao: string;
  /** Siglas distintas dos exames das amostras do grupo (ex.: "MBIOP, MPCIR"). */
  siglaExame: string;
  /** Nomes distintos dos exames das amostras do grupo. */
  nomeExame: string;
  /** Tipo de exame do SAP identificado a partir das siglas do AGHU (define o grupo). */
  tipoExameSugerido: TipoExame;
  informacoesClinicas: string;
  /** Amostras do exame, em ordem de número. */
  amostras: AmostraAghu[];
  situacaoRecepcao: SituacaoRecepcaoSolicitacao;
  /** Caso criado a partir do exame (casos principais). */
  casoNumero?: string;
  /** IHQ registrada a partir do exame e o caso de origem. */
  ihqCodigo?: string;
  ihqCasoNumero?: string;
  /** Devolução que encerrou o exame na recepção. */
  devolucaoId?: number;
}

/** Conferência de recebimento (`conferencia_recebimento`). */
export interface ConferenciaRecebimento {
  id: number;
  /** Chave do exame conferido (`SolicitacaoAghu.id`). */
  solicitacaoId: string;
  /** Código da solicitação no AGHU. */
  solicitacaoCodigo: string;
  casoNumero?: string;
  /** Números das amostras conferidas. */
  amostras: string[];
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
  /** Número da amostra no AGHU (apenas amostras-raiz recebidas). */
  numeroAmostraAghu?: string;
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
  /** Grupos de exame associados à ocorrência na conferência. */
  solicitacaoIds?: string[];
  tipo: TipoNaoConformidadeCodigo;
  /** Texto informado quando o tipo é "Outros" (vazio nos demais). */
  descricao: string;
  /** Observação opcional. */
  observacao?: string;
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
  /** Grupos de exame associados à devolução quando ela ocorre na conferência. */
  solicitacaoIds?: string[];
  unidadeOrigem: string;
  devolvidoPor: Responsavel;
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
  /** Chave do exame recebido (`SolicitacaoAghu.id`). */
  solicitacaoId: string;
  tipoExame: TipoCasoPrincipal;
  urgente: boolean;
  procedimento: string;
  observacoes?: string;
}

/** Confirmação de uma IHQ vinculada a um caso existente. */
export interface VincularIhqInput {
  /** Chave do exame recebido (`SolicitacaoAghu.id`). */
  solicitacaoId: string;
  casoOrigemNumero: string;
  /** Confirmação explícita quando o prontuário do caso difere do da solicitação. */
  divergenciaConfirmada: boolean;
  observacoes?: string;
}

/** Onde a não conformidade foi identificada. */
export type ContextoNaoConformidade =
  | { tipo: 'SEM_ETIQUETA' }
  /** Conferência: devolve os grupos (tipos de exame) pendentes indicados. */
  | { tipo: 'SOLICITACAO'; solicitacaoIds: string[] }
  | { tipo: 'CASO'; casoNumero: string };

/** Registro de não conformidade com a devolução obrigatória. */
export interface RegistrarNaoConformidadeInput {
  contexto: ContextoNaoConformidade;
  tipo: TipoNaoConformidadeCodigo;
  /** Obrigatória quando o tipo é "Outros". */
  descricao?: string;
  observacao?: string;
  /** Exigida quando não há solicitação nem caso. */
  unidadeOrigem?: string;
  novaAmostraSolicitada: boolean;
}

// ---------------------------------------------------------------------------
// Resultados das operações
// ---------------------------------------------------------------------------

/** Resultado da leitura de uma solicitação na recepção. */
export type LeituraSolicitacao =
  /** A solicitação tem tipos de exame aguardando recebimento: abre a conferência da solicitação. */
  | {
      tipo: 'PENDENTE';
      codigoSolicitacao: string;
      exames: SolicitacaoAghu[];
      /** Número da amostra bipada (quando extraído de código de 10 dígitos ou formato código-amostra). */
      amostraBipada?: string | null;
      /** ID do grupo pendente correspondente à amostra bipada. */
      grupoSelecionadoId?: string | null;
      /** Lista com o grupo pendente correspondente à amostra bipada (ou vazia). */
      examesFiltrados?: SolicitacaoAghu[];
      /** Metadados quando a amostra bipada pertence a grupo já recebido/devolvido. */
      amostraBipadaSituacao?: AmostraBipadaSituacao | null;
    }
  /** Todos os exames da solicitação já foram recebidos. */
  | { tipo: 'RECEBIDA'; solicitacao: SolicitacaoAghu; recebimentos: RecebimentoExame[]; amostraBipada?: string | null }
  | {
      tipo: 'DEVOLVIDA';
      solicitacao: SolicitacaoAghu;
      devolvidaEm: string;
      tipoNaoConformidade: TipoNaoConformidadeCodigo;
      amostraBipada?: string | null;
    }
  | { tipo: 'NAO_ENCONTRADA' };

/** Situação da amostra bipada que pertence a um grupo já tratado (recebido/devolvido). */
export interface AmostraBipadaSituacao {
  grupoId: string;
  tipoExame: TipoExame;
  situacaoRecepcao: SituacaoRecepcaoSolicitacao;
  casoNumero?: string;
  ihqCodigo?: string;
  devolucaoId?: number;
}

/** Exame já recebido e o caso (ou IHQ) que gerou. */
export interface RecebimentoExame {
  siglaExame: string;
  nomeExame: string;
  /** Caso criado, ou caso de origem da IHQ. */
  casoNumero: string;
  ihqCodigo?: string;
}

/** Caso resumido para a lista de resultados da busca global (F2). */
export interface CasoResumoBusca {
  numeroInterno: string;
  tipoExame: TipoCasoPrincipal;
  nomePaciente: string;
  prontuario: string;
  /** Código da solicitação AGHU que originou o caso. */
  codigoSolicitacao: string;
  status: StatusCaso;
}

/** Resultado da busca global de casos: os primeiros itens e o total encontrado. */
export interface ResultadoBuscaCasos {
  itens: CasoResumoBusca[];
  total: number;
}

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
