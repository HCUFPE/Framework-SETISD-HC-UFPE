/**
 * Conversões de data/hora entre a interface, os mocks e a API.
 *
 * Os mocks trabalham com ISO local sem fuso (ex.: `2026-11-25T08:00:00.000`).
 * A API real devolve ISO em UTC (ex.: `2026-11-25T11:00:00+00:00`) e espera
 * instantes com offset. Centralizar a conversão evita que o calendário e a
 * gestão de vagas mostrem horários diferentes para a mesma vaga.
 */
import { USAR_MOCKS } from '../config/mocks';

function dois(valor: number): string {
  return String(valor).padStart(2, '0');
}

/** Dia no fuso local do usuário (ou o dia literal já usado pelos mocks). */
export function diaLocal(iso: string): string {
  if (!iso) return '';
  if (USAR_MOCKS) return iso.slice(0, 10);
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso.slice(0, 10);
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
}

/** Valor para um input `datetime-local`, sempre na hora local do usuário. */
export function paraInputLocal(iso: string): string {
  if (!iso) return '';
  if (USAR_MOCKS) return iso.slice(0, 16);
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso.slice(0, 16);
  return `${diaLocal(iso)}T${dois(data.getHours())}:${dois(data.getMinutes())}`;
}

/**
 * Normaliza o valor de um `datetime-local` para a camada de serviço.
 * Nos mocks mantém o ISO local; na API real converte para UTC com offset.
 */
export function paraApiIso(valor: string): string {
  if (!valor) return valor;
  if (USAR_MOCKS) return valor.length === 16 ? `${valor}:00.000` : valor;
  const data = new Date(valor);
  return Number.isNaN(data.getTime()) ? valor : data.toISOString();
}
