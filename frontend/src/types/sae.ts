/** Contratos TypeScript compartilhados entre mocks, stores, views e a futura API. */

export type Perfil = 'AREA_GESTORA' | 'OPERADOR' | 'CHEFIA' | 'COORDENACAO' | 'ADMIN_TI';

export const PERFIS: Perfil[] = ['OPERADOR', 'CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'];

export const ROTULOS_PERFIL: Record<Perfil, string> = {
  AREA_GESTORA: 'Área Gestora',
  OPERADOR: 'Operador da Central',
  CHEFIA: 'Chefia da Central',
  COORDENACAO: 'Gestão / Coordenação',
  ADMIN_TI: 'Administrador TI',
};

export type Prioridade = 'ALTA' | 'MEDIA' | 'BAIXA';

export type StatusSolicitacao =
  | 'RECEBIDA'
  | 'EM_CONFERENCIA'
  | 'PENDENTE_CORRECAO'
  | 'AGUARDANDO_CONTATO'
  | 'AGENDADA'
  | 'CANCELADA';

export const ROTULOS_STATUS: Record<StatusSolicitacao, string> = {
  RECEBIDA: 'Recebida',
  EM_CONFERENCIA: 'Em conferência',
  PENDENTE_CORRECAO: 'Pendente de correção',
  AGUARDANDO_CONTATO: 'Aguardando contato',
  AGENDADA: 'Agendada',
  CANCELADA: 'Cancelada',
};

export type ResultadoContato = 'ACEITE' | 'RECUSA' | 'SEM_RESPOSTA';
export type CategoriaAuditoria = 'SEGURANCA' | 'NEGOCIO_CLINICO' | 'CONFIGURACAO';

export interface Alerta {
  id: string;
  campo: string;
  mensagem: string;
  severidade: 'ERRO' | 'AVISO';
}

export interface Divergencia {
  id: string;
  campo: string;
  valorFormulario: string;
  valorAghux: string;
  tratada: boolean;
  justificativa?: string;
}

export interface CampoComparacao {
  campo: string;
  formulario: string;
  aghux: string;
}

export interface Contato {
  id: string;
  realizadoEm: string;
  canal: string;
  resultado: ResultadoContato;
  operador: string;
  observacao: string;
}

export interface EventoHistorico {
  id: string;
  em: string;
  acao: string;
  autor: string;
  categoria: CategoriaAuditoria;
  detalhes: string;
}

/** Registro de agendamento embutido na solicitação (fluxo legado da fila). */
export interface AgendamentoRegistro {
  dataHora: string;
  unidade: string;
  confirmadoPor: string;
  criadoEm: string;
}

export interface ItemExame {
  codigoExame: string;
  nomeExame: string;
}

/** Registro bruto do export CSV do AGHUX, após agrupamento por solicitação. */
export interface SolicitacaoAghux {
  codigoSolicitacao: string;
  prontuario: string;
  nome: string;
  telefone: string;
  cidade: string;
  estado: string;
  dataSolicitacao: string;
  unidadeSolicitante: string;
  tipoExame: string;
  solicitante: { codigo: string; nome: string };
  itens: ItemExame[];
}

export interface FonteAghux {
  fonte: string;
  referenciaEm: string;
  totalRegistros: number;
  totalSolicitacoes: number;
  solicitacoes: SolicitacaoAghux[];
}

export interface Solicitacao {
  id: string;
  protocolo: string;
  codigoSolicitacaoAghux: string;
  prontuario: string;
  pacienteNome: string;
  telefone: string;
  cidade: string;
  estado: string;
  exame: string;
  itensExame: ItemExame[];
  tipoExame: string;
  setorSolicitante: string;
  solicitanteCodigo: string;
  solicitanteNome: string;
  status: StatusSolicitacao;
  pontuacao: number;
  prioridade: Prioridade;
  recebidaEm: string;
  prazoValidacaoEm: string;
  atributos: Record<string, number>;
  /** Critérios sem origem no export AGHUX; exibidos como simulados na interface. */
  atributosSimulados: string[];
  comparacoes: CampoComparacao[];
  alertas: Alerta[];
  divergencias: Divergencia[];
  contatos: Contato[];
  historico: EventoHistorico[];
  agendamento: AgendamentoRegistro | null;
}

/** Vaga disponível na agenda (contrato de /api/agendamentos/calendario). */
export interface AgendaSlot {
  id: string;
  unidade: string;
  codigoExame: string;
  nomeExame: string;
  inicio: string;
  fim: string;
  capacidade: number;
  ocupadas: number;
  livres: number;
  status: 'DISPONIVEL' | 'LOTADO' | 'ENCERRADO';
}

/** Agendamento efetivado, com rastreabilidade completa. */
export interface Agendamento {
  id: string;
  solicitacaoId: string;
  protocolo: string;
  pacienteChave: string;
  pacienteNome: string;
  prontuario: string;
  unidade: string;
  exame: string;
  slotId: string;
  dataHora: string;
  status: 'ATIVO' | 'CANCELADO' | 'CONCLUIDO';
  confirmadoPor: string;
  criadoEm: string;
  justificativa: string | null;
}

/** Horário sugerido automaticamente para uma solicitação (top 3). */
export interface SugestaoAgendamento {
  slot: AgendaSlot;
  pontuacao: number;
  motivos: string[];
  distanciaKm: number | null;
  distanciaOrigem: 'OSM' | 'MOCK' | 'INDISPONIVEL';
}

/** Resposta de GET /api/agendamentos/calendario. */
export interface CalendarioAgendamentos {
  de: string;
  ate: string;
  slots: AgendaSlot[];
  agendamentos: Agendamento[];
}

/** Paciente encontrado na busca de agendamentos. */
export interface PacienteAgendamentos {
  pacienteChave: string;
  pacienteNome: string;
  prontuario: string;
  agendamentosAtivos: number;
}

/** Resultado paginado da fila (contrato de GET /api/fila). */
export interface ResultadoFila {
  itens: Solicitacao[];
  total: number;
  pagina: number;
  porPagina: number;
  totalPaginas: number;
}

export interface CriterioPriorizacao {
  id: string;
  chave: string;
  nome: string;
  descricao: string;
  peso: number;
  ordem: number;
  ativo: boolean;
}

export interface VersaoCriterios {
  numero: number;
  criadoEm: string;
  autor: string;
  justificativa: string;
  criterios: CriterioPriorizacao[];
}

export interface UsuarioEquipe {
  id: string;
  login: string;
  nome: string;
  email: string;
  lotacao: string;
  perfil: Perfil;
  ativo: boolean;
  criadoEm: string;
}

export interface AdUser {
  exists: boolean;
  username: string;
  displayName: string;
  email: string;
  department: string;
}

export interface Serie {
  rotulo: string;
  valor: number;
}

export interface Gargalo {
  etapa: string;
  unidadeSolicitante: string;
  horas: number;
  quantidade: number;
}

export interface Indicadores {
  pendentes: number;
  tempoMedioValidacao: number;
  agendados: number;
  taxaErro: number;
  tempoMedioAgendamento: number;
  gargalos: Gargalo[];
  porTipo: Serie[];
  porPrioridade: Serie[];
  evolucao: Serie[];
}

export interface Relatorio {
  id: string;
  nome: string;
  descricao: string;
}

export interface RelatorioLinha {
  id: number;
  [coluna: string]: string | number;
}

export interface ResultadoRelatorio {
  colunas: string[];
  linhas: RelatorioLinha[];
}

export interface FiltroFila {
  busca: string;
  status: string;
  tipoExame: string;
  periodo: string;
  pagina: number;
  porPagina: number;
}

export interface FiltroIndicadores {
  periodo: string;
  tipoExame: string;
}

/** Situação do processamento de uma resposta do Microsoft Forms. */
export type StatusFormsEvento = 'PENDENTE' | 'PROCESSADA' | 'DUPLICADA' | 'ERRO';

/** Evento de integração Forms → AGHUX, conforme contrato da Fase 4. */
export interface FormsEvento {
  responseId: string;
  formId: string;
  status: StatusFormsEvento;
  tentativas: number;
  ultimoErro: string | null;
  recebidoEm: string;
  processadoEm: string | null;
  solicitacaoId: string | null;
  divergencias: number;
  alertas: number;
}
