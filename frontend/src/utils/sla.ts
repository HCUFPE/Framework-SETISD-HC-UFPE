export const SLA_DIAS = 20;

export type SlaStatus = 'ok' | 'alerta' | 'atrasado';

/** Quantos dias inteiros se passaram desde a data informada até agora. */
export function diasDesde(data: Date): number {
  const ms = Date.now() - data.getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}

/**
 * Classifica o exame conforme a meta de 20 dias até a liberação:
 * - 'ok': dentro do prazo confortável (menos de 80% do SLA)
 * - 'alerta': já passou de 80% do SLA (>= 16 dias), mas ainda não venceu
 * - 'atrasado': passou dos 20 dias
 */
export function getSlaStatus(dias: number): SlaStatus {
  if (dias >= SLA_DIAS) return 'atrasado';
  if (dias >= SLA_DIAS * 0.8) return 'alerta';
  return 'ok';
}

export function formatTempoTotal(dias: number): string {
  return dias === 0 ? 'hoje' : `${dias}d`;
}