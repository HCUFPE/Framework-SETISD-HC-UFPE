import { horasDesdeReferencia } from '../config/tempo';
import type { Prioridade } from '../types/sae';

/**
 * Classifica a pontuação calculada pelos critérios ativos em uma faixa de prioridade.
 * Limites calibrados para a combinação de pesos dos critérios vigentes.
 */
export function classificarPrioridade(pontuacao: number): Prioridade {
  if (pontuacao >= 60) return 'ALTA';
  if (pontuacao >= 40) return 'MEDIA';
  return 'BAIXA';
}

/** Formata uma data ISO para exibição em pt-BR. */
export function formatarDataHora(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

/** Horas decorridas desde um timestamp ISO, ancoradas na referência dos mocks. */
export function horasDesde(iso: string): number {
  return horasDesdeReferencia(iso);
}

/** Representa uma quantidade de horas em texto curto. */
export function formatarDuracao(horas: number): string {
  if (horas < 1) return '< 1 h';
  if (horas < 24) return `${horas} h`;
  return `${Math.floor(horas / 24)} d ${horas % 24} h`;
}
