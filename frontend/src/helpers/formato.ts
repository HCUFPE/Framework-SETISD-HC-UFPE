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

/** Texto exibido para datas ausentes ou inválidas. */
const NAO_INFORMADO = 'Não informado';

/** Converte ISO (ou AAAA-MM-DD, tratada como data local) em Date; null se vazia ou inválida. */
function paraData(iso?: string | null): Date | null {
  if (!iso) return null;
  // Datas sem horário são tratadas como locais para não "voltar" um dia por fuso.
  const valor = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? new Date(`${iso}T12:00:00`) : new Date(iso);
  return Number.isNaN(valor.getTime()) ? null : valor;
}

/** "dd/mm/aaaa hh:mm" a partir de uma data ISO. */
export function formatarDataHora(iso?: string | null): string {
  const valor = paraData(iso);
  return valor ? dataHora.format(valor).replace(',', '') : NAO_INFORMADO;
}

/** "dd/mm/aaaa" a partir de uma data ISO (ou AAAA-MM-DD). */
export function formatarData(iso?: string | null): string {
  const valor = paraData(iso);
  return valor ? data.format(valor) : NAO_INFORMADO;
}

/** Idade em anos completos a partir da data de nascimento (AAAA-MM-DD); null se vazia ou inválida. */
export function calcularIdade(nascimento: string | null | undefined, referencia = new Date()): number | null {
  const n = paraData(nascimento);
  if (!n) return null;
  let idade = referencia.getFullYear() - n.getFullYear();
  const aindaNaoFez =
    referencia.getMonth() < n.getMonth() || (referencia.getMonth() === n.getMonth() && referencia.getDate() < n.getDate());
  if (aindaNaoFez) idade -= 1;
  return idade;
}

/** Tempo decorrido legível desde uma data ISO (ex.: "35 min", "5 h", "3 dias"). */
export function tempoDecorrido(iso: string, referencia = new Date()): string {
  const valor = paraData(iso);
  if (!valor) return NAO_INFORMADO;
  const minutos = Math.max(0, Math.floor((referencia.getTime() - valor.getTime()) / 60_000));
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 48) return `${horas} h`;
  const dias = Math.floor(horas / 24);
  return `${dias} ${dias === 1 ? 'dia' : 'dias'}`;
}

/** Horas decorridas desde uma data ISO (0 se vazia ou inválida, para não marcar atraso por engano). */
export function horasDesde(iso: string, referencia = new Date()): number {
  const valor = paraData(iso);
  if (!valor) return 0;
  return (referencia.getTime() - valor.getTime()) / 3_600_000;
}

/**
 * Dias de calendário decorridos desde uma data (AAAA-MM-DD ou ISO), comparando só o dia.
 * 0 para hoje, data futura, vazia ou inválida.
 */
export function diasDesde(iso: string, referencia = new Date()): number {
  const valor = paraData(iso);
  if (!valor) return 0;
  const inicio = Date.UTC(valor.getFullYear(), valor.getMonth(), valor.getDate());
  const fim = Date.UTC(referencia.getFullYear(), referencia.getMonth(), referencia.getDate());
  return Math.max(0, Math.round((fim - inicio) / 86_400_000));
}

/** Espera legível em dias: "hoje", "há 1 dia", "há N dias". */
export function rotuloEsperaDias(iso: string, referencia = new Date()): string {
  const dias = diasDesde(iso, referencia);
  if (dias === 0) return 'hoje';
  return `há ${dias} ${dias === 1 ? 'dia' : 'dias'}`;
}
