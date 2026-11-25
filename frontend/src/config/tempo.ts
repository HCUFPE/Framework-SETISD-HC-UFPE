import dadosAghux from '../mocks/dadosAghux.json';
import { USAR_MOCKS } from './mocks';
import type { FonteAghux } from '../types/sae';

/** Data de referência do export AGHUX: usada como "agora" enquanto os mocks estão ativos. */
export const REFERENCIA_EM = (dadosAghux as FonteAghux).referenciaEm;

/** Formata um instante em ISO local (sem fuso), preservando a hora do export. */
export function paraIsoLocal(milissegundos: number): string {
  const data = new Date(milissegundos);
  const dois = (valor: number): string => String(valor).padStart(2, '0');
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}T${dois(data.getHours())}:${dois(data.getMinutes())}:${dois(data.getSeconds())}.${String(data.getMilliseconds()).padStart(3, '0')}`;
}

/** Timestamp atual da simulação (ou do sistema, quando ligado à API real). */
export function agora(): number {
  return USAR_MOCKS ? new Date(REFERENCIA_EM).getTime() : Date.now();
}

/** Timestamp ISO local atual da simulação. */
export function agoraIso(): string {
  return paraIsoLocal(agora());
}

/** Soma horas a um timestamp ISO mantendo a representação local. */
export function somarHoras(iso: string, horas: number): string {
  return paraIsoLocal(new Date(iso).getTime() + horas * 3_600_000);
}

/** Horas decorridas entre um timestamp e a referência configurada. */
export function horasDesdeReferencia(iso: string): number {
  return Math.max(0, Math.round((agora() - new Date(iso).getTime()) / 3_600_000));
}
