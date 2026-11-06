import type { RouteLocationRaw } from 'vue-router';

/**
 * Rota do detalhe de um caso com a barra do número interno legível na URL
 * (ex.: `/casos/HP-0003/26`, e não `/casos/HP-0003%2F26`).
 */
export function rotaDoCaso(
  numeroInterno: string,
  opcoes: { aba?: string; item?: string } = {},
): RouteLocationRaw {
  const query: Record<string, string> = {};
  if (opcoes.aba) query.aba = opcoes.aba;
  if (opcoes.item) query.item = opcoes.item;
  return { path: `/casos/${numeroInterno}`, query };
}
