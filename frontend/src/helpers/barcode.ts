/**
 * Gerador de código de barras Code 128 (subconjunto B), sem dependências externas.
 *
 * Retorna as larguras dos módulos (barras e espaços alternados, começando por barra), incluindo
 * a zona de silêncio. O desenho em SVG fica em `components/ap/Barcode.vue`.
 */

/** Padrões de largura (barra/espaço alternados) dos símbolos 0–106 do Code 128. */
const PADROES: string[] = [
  '212222', '222122', '222221', '121223', '121322', '131222', '122213', '122312', '132212', '221213',
  '221312', '231212', '112232', '122132', '122231', '113222', '123122', '123221', '223211', '221132',
  '221231', '213212', '223112', '312131', '311222', '321122', '321221', '312212', '322112', '322211',
  '212123', '212321', '232121', '111323', '131123', '131321', '112313', '132113', '132311', '211313',
  '231113', '231311', '112133', '112331', '132131', '113123', '113321', '133121', '313121', '211331',
  '231131', '213113', '213311', '213131', '311123', '311321', '331121', '312113', '312311', '332111',
  '314111', '221411', '431111', '111224', '111422', '121124', '121421', '141122', '141221', '112214',
  '112412', '122114', '122411', '142112', '142211', '241211', '221114', '413111', '241112', '134111',
  '111242', '121142', '121241', '114212', '124112', '124211', '411212', '421112', '421211', '212141',
  '214121', '412121', '111143', '111341', '131141', '114113', '114311', '411113', '411311', '113141',
  '114131', '311141', '411131', '211412', '211214', '211232', '2331112',
];

const START_B = 104;
const STOP = 106;
/** Largura da zona de silêncio em módulos (mínimo da norma: 10). */
export const ZONA_SILENCIO = 10;

/** Valores dos símbolos (início B, dados, verificador, parada) para o texto informado. */
export function simbolosCode128B(texto: string): number[] {
  const valores = Array.from(texto).map((caractere) => {
    const codigo = caractere.charCodeAt(0);
    if (codigo < 32 || codigo > 126) {
      throw new Error(`Caractere não suportado no Code 128-B: "${caractere}"`);
    }
    return codigo - 32;
  });
  const soma = valores.reduce((acc, valor, i) => acc + valor * (i + 1), START_B);
  return [START_B, ...valores, soma % 103, STOP];
}

/** Larguras dos módulos, começando e terminando com zona de silêncio (espaços). */
export function modulosCode128B(texto: string): number[] {
  const larguras = simbolosCode128B(texto).flatMap((simbolo) => Array.from(PADROES[simbolo], Number));
  return [ZONA_SILENCIO, ...larguras, ZONA_SILENCIO];
}

/** Retângulos das barras (x e largura em módulos) e a largura total do código. */
export function barrasCode128B(texto: string): { barras: { x: number; largura: number }[]; total: number } {
  const modulos = modulosCode128B(texto);
  const barras: { x: number; largura: number }[] = [];
  let x = 0;
  modulos.forEach((largura, i) => {
    // Índice 0 é a zona de silêncio (espaço); a partir daí alternam barra (ímpar) e espaço (par).
    if (i % 2 === 1) barras.push({ x, largura });
    x += largura;
  });
  return { barras, total: x };
}
