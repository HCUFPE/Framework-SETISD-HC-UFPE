/**
 * Constantes de domínio do Sistema AP: fluxos, rótulos e catálogos.
 * Códigos conforme `docs/especificacao/04-modelo-dados.md`.
 */
import type { BadgeVariant } from '../components/Badge.vue';
import type {
  CodStatusItemAghu,
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

// ---------------------------------------------------------------------------
// Domínios do AGHU — fonte: data/dicionario_dados.md (não inventar valores)
// ---------------------------------------------------------------------------

/** Origens do AGHU (`origem`), com o texto exibido pelo AGHU. */
export const ORIGENS: Record<OrigemAtendimento, string> = {
  AMBULATORIO: 'Ambulatório',
  INTERNACAO: 'Internação',
  CIRURGIA: 'Cirurgia',
  EXTERNO: 'Paciente Externo',
};

/** Status do item no AGHU (`cod_status_item` ↔ `status_item_exame`). */
export const STATUS_ITEM_AGHU: Record<CodStatusItemAghu, { rotulo: string; variante: BadgeVariant }> = {
  LI: { rotulo: 'LIBERADO', variante: 'success' },
  AC: { rotulo: 'A COLETAR', variante: 'warning' },
  EX: { rotulo: 'EXECUTANDO', variante: 'info' },
  AE: { rotulo: 'AREA EXECUTORA', variante: 'info' },
  CA: { rotulo: 'CANCELADO', variante: 'danger' },
  CO: { rotulo: 'COLETADO', variante: 'info' },
  EC: { rotulo: 'EM COLETA', variante: 'warning' },
  PE: { rotulo: 'PENDENTE', variante: 'warning' },
};

/** Rótulo e variante do status do item no AGHU, com fallback para código fora do catálogo. */
export function statusItemAghu(codigo: string, descricao?: string): { rotulo: string; variante: BadgeVariant; catalogado: boolean } {
  const conhecido = STATUS_ITEM_AGHU[codigo as CodStatusItemAghu];
  if (conhecido) return { ...conhecido, catalogado: true };
  const texto = (descricao || codigo || '').trim();
  return { rotulo: texto ? `${texto} (status não catalogado)` : 'Não informado', variante: 'default', catalogado: false };
}

/** Exames de AP no AGHU (`sigla_exame` → `nome_exame`, tipo do SAP e `codigo_lab`). */
export const EXAMES_AGHU: Record<string, { nome: string; tipo: TipoExame; codigoLab: string }> = {
  APECR: { nome: 'ANATOMOPATOLÓGICO - PEÇA CIRÚRGICA', tipo: 'HP', codigoLab: '207' },
  CCVM: { nome: 'EXAME CITOPATOLÓGICO CÉRVICO-VAGINAL/MICROFLORA', tipo: 'CCV', codigoLab: '139' },
  HPDER: { nome: 'HISTOPATOLOGICO DERMATOLOGIA', tipo: 'HP', codigoLab: '207' },
  IMUHI: { nome: 'IMUNO-HISTOQUÍMICA', tipo: 'IHQ', codigoLab: '209' },
  MBIOP: { nome: 'ANATOMOPATOLÓGICO - MAMA', tipo: 'HP', codigoLab: '207' },
  MPCIR: { nome: 'ANATOMOPATOLÓGICO - MAMA', tipo: 'HP', codigoLab: '207' },
  CITOP: { nome: 'CITOPATOLÓGICO', tipo: 'CG', codigoLab: '203' },
  CONGE: { nome: 'AP- EXAME TRANSOPERATÓRIO DE CONGELAÇÃO (PATOLOGIA)', tipo: 'CO', codigoLab: '205' },
  CITO: { nome: 'CITOLOGIA ONCÓTICA', tipo: 'CCV', codigoLab: '207' },
  COUT2: { nome: 'ANATOMOPATOLÓGICO - COLO UTERINO', tipo: 'HP', codigoLab: '207' },
  COLUT: { nome: 'ANATOMOPATOLÓGICO - COLO UTERINO', tipo: 'HP', codigoLab: '207' },
  CPMAM: { nome: 'CITOPATOLOGICO DE MAMA', tipo: 'CG', codigoLab: '203' },
};

/** Unidades do AGHU (`unidade`), já sem caracteres invisíveis. Grafias mantidas como no AGHU. */
export const UNIDADES_AGHU: string[] = [
  '10º NORTE',
  '10º SUL',
  '11º NORTE',
  '11º SUL',
  '4º NORTE',
  '5º NORTE',
  '6º SUL',
  '7 º SUL',
  '7º NORTE',
  '8º NORTE',
  '8º SUL',
  '9º  SUL',
  '9º NORTE',
  'ACUPUNTURA (AMBULATÓRIO)',
  'ALERGIA E IMUNOLOGIA (AMBULATÓRIO)',
  'ANESTESIOLOGIA (AMBULATÓRIO)',
  'BLOCO CIRURGICO',
  'BLOCO DERMATO',
  'BRONCOSCOPIA',
  'CARDIOLOGIA (AMBULATÓRIO)',
  'CENTRO OBSTETRICO',
  'CIRURGIA BARIATRICA',
  'CIRURGIA DE CABECA E PESCOCO',
  'CIRURGIA GERAL (AMBULATÓRIO)',
  'CIRURGIA PEDIÁTRICA (AMBULATÓRIO)',
  'CIRURGIA PLÁSTICA (AMBULATÓRIO)',
  'CIRURGIA TORÁCICA (AMBULATÓRIO)',
  'CIRURGIA VASCULAR (AMBULATÓRIO)',
  'CLINICA DA DOR (AMBULATÓRIO)',
  'CLÍNICA MÉDICA (AMBULATÓRIO)',
  'DERMATOLOGIA (AMBULATÓRIO)',
  'ENDOCRINOLOGIA (AMBULATÓRIO)',
  'ENDOSCOPIA',
  'ENFERMAGEM',
  'ESPAÇO TRANS (AMBULATÓRIO)',
  'GASTROENTEROLOGIA (AMBULATÓRIO)',
  'GERIATRIA (AMBULATORIO)',
  'GINECOLOGIA (AMBULATÓRIO)',
  'HEMATOLOGIA (AMBULATÓRIO)',
  'HEMODIALISE',
  'HEMODINAMICA - PDT',
  'HOSPITAL - DIA',
  'INFECTOLOGIA (AMBULATÓRIO)',
  'NEFROLOGIA (AMBULATÓRIO)',
  'NEUROLOGIA (AMBULATÓRIO)',
  'NUCLEO DE TELESSAUDE',
  'NUTRIÇÃO',
  'NÚCLEO DO SERVIDOR (AMBULATÓRIO)',
  'OBSTETRÍCIA (AMBULATÓRIO)',
  'OFTALMO GERAL',
  'OFTALMOLOGIA (AMBULATÓRIO)',
  'ONCOLOGIA (AMBULATÓRIO)',
  'ORTOPEDIA (AMBULATÓRIO)',
  'OTORRINOLARINGOLOGIA (AMBULATÓRIO)',
  'PEDIATRIA (AMBULATÓRIO)',
  'PNEUMOLOGIA (AMBULATÓRIO)',
  'PROCTOLOGIA (AMBULATORIO)',
  'PSIQUIATRIA (AMBULATÓRIO)',
  'PUERICULTURA (AMBULATÓRIO)',
  'REUMATOLOGIA (AMBULATÓRIO)',
  'SAUDE OCUPACIONAL E SEGURANCA DO TRABALHO',
  'TRANSPLANTE (AMBULATÓRIO)',
  'UAC: EXAMES EXTERNOS',
  'UAC: SOROLOGIA',
  'UAP: CITOLOGIA CÉRVICO-VAGINAL',
  'UAP: CITOLOGIA GERAL',
  'UAP: CONGELAÇÃO',
  'UAP: HISTOPATOLÓGICO',
  'UAP: IMUNOHISTOQUÍMICA',
  'UCI CANGURU',
  'UCI NEONATAL',
  'UDI: ULTRASSONOGRAFIA',
  'URGENCIA E EMERGENCIA',
  'UROLOGIA (AMBULATÓRIO)',
  'UTI ADULTO',
  'UTI NEONATAL',
];

/** Texto exibido quando um dado não veio do AGHU. */
export const NAO_INFORMADO = 'Não informado';

/** Rótulo da origem do atendimento, tolerante a origem nula ou desconhecida. */
export function rotuloOrigem(origem: OrigemAtendimento | null | undefined): string {
  return (origem && ORIGENS[origem]) || 'Não informada';
}

/** Catálogo de tipos de não conformidade, na ordem do formulário em papel do setor. */
export const TIPOS_NAO_CONFORMIDADE: Record<TipoNaoConformidadeCodigo, string> = {
  SEM_SOLICITACAO_OU_ETIQUETA: 'Amostra sem solicitação ou sem etiqueta do AGHU',
  EXAME_NAO_CORRESPONDE_MATERIAL: 'Solicitação do exame não corresponde ao tipo de material enviado',
  FALTA_DESCRICAO_FRASCO: 'Falta descrição do material no frasco',
  IDENTIFICACAO_ILEGIVEL: 'Etiqueta, identificação do paciente na peça ou requisição ilegível',
  NUMERACAO_FRASCOS_DIVERGENTE: 'Numeração dos frascos não corresponde à numeração do AGHU',
  QUANTIDADE_FRASCOS_DIVERGENTE: 'Quantidade de frascos não confere com o descrito no AGHU',
  LATERALIDADE_DIVERGENTE: 'Lateralidade divergente ou não informada',
  FALTA_CARIMBO_ASSINATURA: 'Falta carimbo e/ou assinatura do médico responsável',
  ACONDICIONAMENTO_INADEQUADO: 'Acondicionamento inadequado ou sem fixador',
  SOLICITACOES_DUPLICADAS: 'Várias solicitações do mesmo exame em códigos diferentes',
  PECAS_NAO_DESCRITAS: 'Não descreveu as peças no campo informações clínicas',
  SISCAN_INCORRETO: 'Formulário do Siscan não preenchido corretamente',
  SEM_AGENDAMENTO_CMCE: 'Sem agendamento no sistema CMCE (SES-PE)',
  OUTROS: 'Outros',
};

/** Ordem de exibição do catálogo de não conformidades. */
export const ORDEM_TIPOS_NAO_CONFORMIDADE = Object.keys(TIPOS_NAO_CONFORMIDADE) as TipoNaoConformidadeCodigo[];

/** Solução sugerida para tipos de não conformidade que a têm no formulário do setor. */
export const SOLUCOES_NAO_CONFORMIDADE: Partial<Record<TipoNaoConformidadeCodigo, string>> = {
  SOLICITACOES_DUPLICADAS: 'Unir os diversos materiais em única solicitação.',
};

/** Texto do tipo de uma não conformidade, com o texto informado quando é "Outros". */
export function rotuloNaoConformidade(nc: { tipo: TipoNaoConformidadeCodigo; descricao?: string }): string {
  if (nc.tipo === 'OUTROS' && nc.descricao?.trim()) return `Outros: ${nc.descricao.trim()}`;
  return TIPOS_NAO_CONFORMIDADE[nc.tipo] ?? nc.tipo;
}

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

/**
 * Espera (dias) a partir da qual um exame pendente é destacado como atrasado.
 * Em dias porque o AGHU não fornece a hora da solicitação.
 */
export const DIAS_ALERTA_PENDENTE = 1;

