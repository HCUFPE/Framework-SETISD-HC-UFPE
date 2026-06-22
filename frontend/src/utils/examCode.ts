import { EXAM_TYPE_PREFIX, type ExamType } from '../constants/examTypes';

export type Semestre = 1 | 2;

export function getSemestreAtual(data: Date = new Date()): Semestre {
  return data.getMonth() < 6 ? 1 : 2;
}

/**
 * Formata o código no padrão usado pela equipe: PREFIXO-SEQUENCIAL/ANO.SEMESTRE
 * Ex: formatExamCode('HP', 1, 2026, 1) => 'HP-0001/26.1'
 */
export function formatExamCode(tipo: ExamType, sequencial: number, ano: number, semestre: Semestre): string {
  const prefixo = EXAM_TYPE_PREFIX[tipo];
  const anoCurto = String(ano).slice(-2);
  const sequencialFormatado = String(sequencial).padStart(4, '0');
  return `${prefixo}-${sequencialFormatado}/${anoCurto}.${semestre}`;
}

/**
 * Gera o código de um exame DERIVADO de um caso já existente
 * (ex: IHQ pedido a partir de um HP já registrado).
 * Mantém o mesmo sequencial/ano/semestre do caso original — só troca o prefixo.
 */
export function deriveExamCode(sequencial: number, ano: number, semestre: Semestre, novoTipo: ExamType): string {
  return formatExamCode(novoTipo, sequencial, ano, semestre);
}