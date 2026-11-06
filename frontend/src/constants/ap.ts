/**
 * Constantes de domínio do Sistema AP: fluxos, rótulos e catálogos.
 * Códigos conforme `docs/especificacao/04-modelo-dados.md`.
 */
import type { BadgeVariant } from '../components/Badge.vue';
import type {
  EtapaCodigo,
  OrigemAtendimento,
  ResultadoConferencia,
  SituacaoDevolucao,
  StatusCaso,
  StatusExameIhq,
  StatusNaoConformidade,
  TipoCasoPrincipal,
  TipoExame,
  TipoItemMaterial,
  TipoNaoConformidadeCodigo,
} from '../types/ap';

/** Tipos de exame com sigla e nome (tabela `tipo_exame`). */
export const TIPOS_EXAME: Record<TipoExame, { nome: string; principal: boolean }> = {
  HP: { nome: 'Histopatológico', principal: true },
  CG: { nome: 'Citologia geral', principal: true },
  CCV: { nome: 'Citologia cérvico-vaginal', principal: true },
  CO: { nome: 'Congelação', principal: true },
  IHQ: { nome: 'Imuno-histoquímica', principal: false },
};

/** Ordem de exibição dos tipos de exame. */
export const ORDEM_TIPOS_EXAME: TipoExame[] = ['HP', 'CG', 'CCV', 'CO', 'IHQ'];

/** Tipos que originam caso próprio. */
export const TIPOS_CASO_PRINCIPAL: TipoCasoPrincipal[] = ['HP', 'CG', 'CCV', 'CO'];

/** Rótulos das etapas (tabela `etapa`). */
export const ETAPAS: Record<EtapaCodigo, string> = {
  RECEPCAO: 'Recepção',
  MACROSCOPIA: 'Macroscopia',
  CONGELACAO: 'Congelação',
  PROCESSAMENTO: 'Processamento técnico',
  IHQ: 'Imuno-histoquímica',
  TRIAGEM_CITO: 'Triagem citotécnica',
  MICROSCOPIA: 'Microscopia',
  APROVACAO: 'Aprovação',
  ARQUIVO: 'Arquivo',
  EXTERNO: 'Laboratório externo',
};

/** Fluxo padrão de etapas por tipo de caso (equivalente a `config_fluxo_etapa`). */
export const FLUXO_POR_TIPO: Record<TipoCasoPrincipal, EtapaCodigo[]> = {
  HP: ['RECEPCAO', 'MACROSCOPIA', 'PROCESSAMENTO', 'MICROSCOPIA', 'APROVACAO', 'ARQUIVO'],
  CG: ['RECEPCAO', 'PROCESSAMENTO', 'MICROSCOPIA', 'APROVACAO', 'ARQUIVO'],
  CCV: ['RECEPCAO', 'PROCESSAMENTO', 'TRIAGEM_CITO', 'MICROSCOPIA', 'APROVACAO', 'ARQUIVO'],
  CO: ['RECEPCAO', 'CONGELACAO', 'MICROSCOPIA', 'APROVACAO', 'ARQUIVO'],
};

/**
 * Etapas do caso considerando IHQ vinculada: a etapa IHQ entra antes da microscopia.
 */
export function fluxoDoCaso(tipo: TipoCasoPrincipal, possuiIhq: boolean): EtapaCodigo[] {
  const fluxo = [...FLUXO_POR_TIPO[tipo]];
  if (possuiIhq) fluxo.splice(fluxo.indexOf('MICROSCOPIA'), 0, 'IHQ');
  return fluxo;
}

/** Etapa para a qual o caso é encaminhado após a recepção. */
export function etapaAposRecepcao(tipo: TipoCasoPrincipal): EtapaCodigo {
  return FLUXO_POR_TIPO[tipo][1];
}

/** Rótulo e variante de badge de cada status do caso. */
export const STATUS_CASO: Record<StatusCaso, { rotulo: string; variante: BadgeVariant }> = {
  RECEBIDO: { rotulo: 'Recebido', variante: 'info' },
  EM_MACROSCOPIA: { rotulo: 'Em macroscopia', variante: 'info' },
  EM_CONGELACAO: { rotulo: 'Em congelação', variante: 'info' },
  EM_PROCESSAMENTO: { rotulo: 'Em processamento técnico', variante: 'info' },
  EM_IHQ: { rotulo: 'Em IHQ', variante: 'info' },
  IHQ_AGUARDANDO_EXTERNO: { rotulo: 'IHQ externa – aguardando resultado', variante: 'warning' },
  EM_MICROSCOPIA: { rotulo: 'Em microscopia', variante: 'info' },
  AGUARDANDO_APROVACAO: { rotulo: 'Aguardando aprovação', variante: 'warning' },
  LAUDO_CONCLUIDO: { rotulo: 'Laudo concluído', variante: 'success' },
  EM_ARQUIVAMENTO: { rotulo: 'Em arquivamento', variante: 'primary' },
  ARQUIVADO: { rotulo: 'Arquivado', variante: 'success' },
  DEVOLVIDO: { rotulo: 'Devolvido', variante: 'default' },
  CANCELADO: { rotulo: 'Cancelado', variante: 'default' },
};

/** Ordem de exibição dos status nos filtros. */
export const ORDEM_STATUS_CASO = Object.keys(STATUS_CASO) as StatusCaso[];

/** Status em que o caso fica somente leitura, com o texto da faixa de bloqueio. */
export const STATUS_BLOQUEADOS: Partial<Record<StatusCaso, string>> = {
  DEVOLVIDO: 'Caso devolvido por não conformidade — fora das filas ativas. Consulta somente leitura.',
  CANCELADO: 'Caso cancelado — fora das filas ativas. Consulta somente leitura.',
  LAUDO_CONCLUIDO: 'Laudo concluído — o caso não pode mais ser alterado.',
  EM_ARQUIVAMENTO: 'Caso em arquivamento — o laudo já foi concluído e o caso não pode mais ser alterado.',
  ARQUIVADO: 'Caso arquivado — histórico completo disponível. Consulta somente leitura.',
};

/** Indica se o caso aceita alterações (não conformidade, cancelamento). */
export function casoEstaAtivo(status: StatusCaso): boolean {
  return !(status in STATUS_BLOQUEADOS);
}

/** Status que impedem o vínculo de uma IHQ ao caso. */
export const STATUS_INELEGIVEIS_IHQ: StatusCaso[] = ['DEVOLVIDO', 'CANCELADO'];

/** Rótulos da origem do atendimento (A = assistencial interno, E = externo). */
export const ORIGENS: Record<OrigemAtendimento, string> = {
  AMBULATORIO: 'Ambulatório (A)',
  INTERNACAO: 'Internação (A)',
  BLOCO_CIRURGICO: 'Bloco cirúrgico (A)',
  EXTERNO: 'Externo (E)',
};

/** Catálogo padronizado de tipos de não conformidade. */
export const TIPOS_NAO_CONFORMIDADE: Record<TipoNaoConformidadeCodigo, string> = {
  SEM_ETIQUETA_AGHU: 'Sem etiqueta do AGHU',
  IDENTIFICACAO_DIVERGENTE: 'Identificação divergente',
  QUANTIDADE_DIVERGENTE: 'Quantidade divergente',
  MATERIAL_INADEQUADO: 'Material inadequado/insuficiente',
  RECIPIENTE_DANIFICADO: 'Recipiente danificado/vazamento',
  FIXACAO_INADEQUADA: 'Ausência de fixador/fixação inadequada',
  REQUISICAO_INCOMPLETA: 'Requisição incompleta',
  OUTRO: 'Outro',
};

/** Rótulos do status da não conformidade. */
export const STATUS_NAO_CONFORMIDADE: Record<StatusNaoConformidade, string> = {
  ABERTA: 'Aberta',
  EM_TRATAMENTO: 'Em tratamento',
  RESOLVIDA: 'Resolvida',
  CANCELADA: 'Cancelada',
};

/** Rótulos e variantes da situação da devolução. */
export const SITUACOES_DEVOLUCAO: Record<SituacaoDevolucao, { rotulo: string; variante: BadgeVariant }> = {
  AGUARDANDO_NOVA_AMOSTRA: { rotulo: 'Aguardando nova amostra', variante: 'warning' },
  NOVA_AMOSTRA_RECEBIDA: { rotulo: 'Nova amostra recebida', variante: 'success' },
  ENCERRADA: { rotulo: 'Encerrada', variante: 'default' },
};

/** Situações finais: a não conformidade vinculada passa a "Resolvida". */
export const SITUACOES_DEVOLUCAO_FINAIS: SituacaoDevolucao[] = ['NOVA_AMOSTRA_RECEBIDA', 'ENCERRADA'];

/** Rótulos do resultado da conferência. */
export const RESULTADOS_CONFERENCIA: Record<ResultadoConferencia, string> = {
  ACEITA: 'Aceita',
  REJEITADA: 'Rejeitada',
  PENDENTE: 'Pendente',
};

/** Itens da conferência física, na ordem de exibição. */
export const ITENS_CONFERENCIA = [
  { chave: 'identificacaoConfere', rotulo: 'Identificação confere com a requisição' },
  { chave: 'materialConfere', rotulo: 'Material corresponde à descrição' },
  { chave: 'quantidadeConfere', rotulo: 'Quantidade de frascos confere' },
  { chave: 'recipienteAdequado', rotulo: 'Recipiente íntegro e adequado' },
] as const;

/** Rótulos do status da IHQ. */
export const STATUS_EXAME_IHQ: Record<StatusExameIhq, { rotulo: string; variante: BadgeVariant }> = {
  SOLICITADA: { rotulo: 'Solicitada', variante: 'info' },
  EM_EXECUCAO_INTERNA: { rotulo: 'Em execução interna', variante: 'info' },
  AGUARDANDO_EXTERNO: { rotulo: 'Aguardando laboratório externo', variante: 'warning' },
  RESULTADO_RECEBIDO: { rotulo: 'Resultado recebido', variante: 'primary' },
  RESULTADO_REGISTRADO: { rotulo: 'Resultado registrado', variante: 'success' },
  RETORNADA_MICROSCOPIA: { rotulo: 'Retornada à microscopia', variante: 'success' },
};

/** Rótulos dos tipos de item material (singular e plural). */
export const TIPOS_ITEM_MATERIAL: Record<TipoItemMaterial, { singular: string; plural: string }> = {
  AMOSTRA: { singular: 'amostra', plural: 'amostras' },
  FRAGMENTO: { singular: 'fragmento', plural: 'fragmentos' },
  BLOCO: { singular: 'bloco', plural: 'blocos' },
  CELL_BLOCK: { singular: 'cell-block', plural: 'cell-blocks' },
  LAMINA: { singular: 'lâmina', plural: 'lâminas' },
};

/** Lista padronizada de procedimentos. */
export const PROCEDIMENTOS: string[] = [
  'Biópsia endoscópica',
  'Biópsia por agulha grossa',
  'Biópsia incisional',
  'Biópsia excisional',
  'Exérese de lesão cutânea',
  'Ressecção cirúrgica',
  'Histerectomia',
  'Tireoidectomia',
  'Punção aspirativa por agulha fina (PAAF)',
  'Coleta de líquido cavitário',
  'Coleta de citologia cérvico-vaginal',
  'Biópsia intraoperatória',
  'Outro procedimento',
];

/** Unidades de origem para material sem etiqueta do AGHU. */
export const UNIDADES_ORIGEM: string[] = [
  'Ambulatório de Cabeça e Pescoço',
  'Ambulatório de Cirurgia Geral',
  'Ambulatório de Dermatologia',
  'Ambulatório de Gastroenterologia',
  'Ambulatório de Ginecologia',
  'Ambulatório de Urologia',
  'Bloco Cirúrgico Central',
  'Enfermaria de Clínica Médica',
  'Enfermaria de Cirurgia',
  'Enfermaria de Pneumologia',
  'UTI Adulto',
  'Paciente externo (rede municipal)',
];

/** Prazo padrão por etapa, em horas (`prazo_padrao`, escopo ETAPA). */
export const PRAZO_ETAPA_HORAS: Record<EtapaCodigo, number> = {
  RECEPCAO: 24,
  MACROSCOPIA: 48,
  CONGELACAO: 1,
  PROCESSAMENTO: 48,
  IHQ: 120,
  TRIAGEM_CITO: 72,
  MICROSCOPIA: 96,
  APROVACAO: 48,
  ARQUIVO: 72,
  EXTERNO: 240,
};

/** Setor registrado nas ações feitas pela recepção. */
export const SETOR_RECEPCAO = 'Recepção';
