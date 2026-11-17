/**
 * Utilitários para dados vindos do AGHU (ver `data/dicionario_dados.md`).
 */
import type { AmostraAghu, SolicitacaoAghu, TipoExame } from '../types/ap';

/** Caracteres invisíveis encontrados em valores do AGHU (ex.: U+200B no fim de unidades). */
const INVISIVEIS = /[​-‍﻿]/g;

/** Remove caracteres invisíveis e espaços nas pontas. Mantém a grafia interna do AGHU. */
export function limparTextoAghu(valor: string | null | undefined): string {
  return (valor ?? '').replace(INVISIVEIS, '').trim();
}

/** Chave do grupo de um tipo de exame dentro da solicitação: `<código>:<TIPO>`. */
export function chaveExame(codigoSolicitacao: string, tipoExame: TipoExame): string {
  return `${codigoSolicitacao.trim()}:${tipoExame}`;
}

/** Valores distintos, na ordem em que aparecem, unidos por ", ". */
export function distintos(valores: string[]): string {
  return [...new Set(valores.map((v) => v.trim()).filter(Boolean))].join(', ');
}

/** Preenche sigla e nome do grupo a partir das amostras (siglas/nomes distintos). */
export function resumirExamesDoGrupo<T extends Pick<SolicitacaoAghu, 'amostras' | 'siglaExame' | 'nomeExame'>>(grupo: T): T {
  return {
    ...grupo,
    siglaExame: distintos(grupo.amostras.map((a) => a.siglaExame)),
    nomeExame: distintos(grupo.amostras.map((a) => a.nomeExame)),
  };
}

/** Uma solicitação com seus grupos (tipos de exame), para a fila e a conferência. */
export interface SolicitacaoAgrupada {
  codigoSolicitacao: string;
  /** Grupos em ordem: Congelação primeiro, depois principais, IHQ por último. */
  exames: SolicitacaoAghu[];
}

/** Ordem dos tipos na solicitação: Congelação primeiro, IHQ por último. */
const ORDEM_TIPO: Record<TipoExame, number> = { CO: 0, HP: 1, CG: 2, CCV: 3, IHQ: 4 };

/** Ordena os grupos de uma solicitação (CO primeiro, IHQ por último). */
export function ordenarGrupos(grupos: SolicitacaoAghu[]): SolicitacaoAghu[] {
  return [...grupos].sort((a, b) => ORDEM_TIPO[a.tipoExameSugerido] - ORDEM_TIPO[b.tipoExameSugerido]);
}

/** Agrupa grupos de tipos de exame pela solicitação do AGHU, mantendo a ordem de chegada. */
export function agruparPorSolicitacao(grupos: SolicitacaoAghu[]): SolicitacaoAgrupada[] {
  const mapa = new Map<string, SolicitacaoAghu[]>();
  for (const g of grupos) mapa.set(g.codigoSolicitacao, [...(mapa.get(g.codigoSolicitacao) ?? []), g]);
  return [...mapa.entries()].map(([codigoSolicitacao, exames]) => ({ codigoSolicitacao, exames: ordenarGrupos(exames) }));
}

/** Amostras de vários grupos, em ordem de número. */
export function amostrasDosGrupos(grupos: SolicitacaoAghu[]): (AmostraAghu & { tipoExame: TipoExame })[] {
  const todas = grupos.flatMap((g) => g.amostras.map((a) => ({ ...a, tipoExame: g.tipoExameSugerido })));
  return todas.sort((a, b) => Number(a.numeroAmostra) - Number(b.numeroAmostra) || a.numeroAmostra.localeCompare(b.numeroAmostra));
}

/** Ordena amostras pelo número (numérico quando possível). */
export function ordenarAmostras(amostras: AmostraAghu[]): AmostraAghu[] {
  return [...amostras].sort((a, b) => Number(a.numeroAmostra) - Number(b.numeroAmostra) || a.numeroAmostra.localeCompare(b.numeroAmostra));
}

/** Resumo das descrições das amostras do exame (para listas e cabeçalhos). */
export function resumoMaterial(solicitacao: Pick<SolicitacaoAghu, 'amostras'>): string {
  const descricoes = solicitacao.amostras.map((a) => a.descricaoMaterial.trim()).filter(Boolean);
  if (descricoes.length === 0) return 'Material não informado';
  return [...new Set(descricoes)].join(' · ');
}

/** "1 amostra" / "N amostras". */
export function rotuloQuantidadeAmostras(quantidade: number): string {
  return `${quantidade} ${quantidade === 1 ? 'amostra' : 'amostras'}`;
}

/** "1 solicitação" / "N solicitações". */
export function rotuloQuantidadeSolicitacoes(quantidade: number): string {
  return `${quantidade} ${quantidade === 1 ? 'solicitação' : 'solicitações'}`;
}

/** "amostra 2" / "amostras 2, 3". */
export function rotuloNumerosAmostras(amostras: Pick<AmostraAghu, 'numeroAmostra'>[]): string {
  const numeros = amostras.map((a) => a.numeroAmostra).join(', ');
  return `${amostras.length === 1 ? 'amostra' : 'amostras'} ${numeros}`;
}
