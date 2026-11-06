/**
 * Formatação de datas, durações e textos para exibição (pt-BR).
 */

const dataHora = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});
const data = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });

/** "dd/mm/aaaa hh:mm" a partir de uma data ISO. */
export function formatarDataHora(iso?: string): string {
  return iso ? dataHora.format(new Date(iso)).replace(',', '') : '—';
}

/** "dd/mm/aaaa" a partir de uma data ISO (ou AAAA-MM-DD). */
export function formatarData(iso?: string): string {
  if (!iso) return '—';
  // Datas sem horário são tratadas como locais para não "voltar" um dia por fuso.
  const valor = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? new Date(`${iso}T12:00:00`) : new Date(iso);
  return data.format(valor);
}

/** Idade em anos completos a partir da data de nascimento (AAAA-MM-DD). */
export function calcularIdade(nascimento: string, referencia = new Date()): number {
  const n = new Date(`${nascimento}T12:00:00`);
  let idade = referencia.getFullYear() - n.getFullYear();
  const aindaNaoFez =
    referencia.getMonth() < n.getMonth() || (referencia.getMonth() === n.getMonth() && referencia.getDate() < n.getDate());
  if (aindaNaoFez) idade -= 1;
  return idade;
}

/** Tempo decorrido legível desde uma data ISO (ex.: "35 min", "5 h", "3 dias"). */
export function tempoDecorrido(iso: string, referencia = new Date()): string {
  const minutos = Math.max(0, Math.floor((referencia.getTime() - new Date(iso).getTime()) / 60_000));
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 48) return `${horas} h`;
  const dias = Math.floor(horas / 24);
  return `${dias} ${dias === 1 ? 'dia' : 'dias'}`;
}

/** Horas decorridas desde uma data ISO. */
export function horasDesde(iso: string, referencia = new Date()): number {
  return (referencia.getTime() - new Date(iso).getTime()) / 3_600_000;
}
