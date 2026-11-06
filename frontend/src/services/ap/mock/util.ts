/**
 * Utilitários compartilhados pelas implementações mock dos serviços do Sistema AP.
 */
import { db, proximoId } from '../../../mocks/ap/db';
import type { AuditLog, CasoAp, HistoricoCaso, ItemMaterial, Responsavel } from '../../../types/ap';
import { ServiceError } from '../types';

/** Latência simulada das chamadas, em milissegundos. */
const LATENCIA_MS = 300;

/** Aguarda a latência simulada. */
export function latencia(ms = LATENCIA_MS): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Cópia profunda: o chamador nunca recebe referências do "banco". */
export function copia<T>(valor: T): T {
  return structuredClone(valor);
}

/** Normaliza um código lido ou digitado. */
export function normalizarCodigo(codigo: string): string {
  return codigo.trim().toUpperCase();
}

/** Data/hora atual em ISO. */
export function agoraIso(): string {
  return new Date().toISOString();
}

/** Garante que o AGHU está disponível. */
export function exigirAghuDisponivel(): void {
  if (!db.aghuDisponivel) {
    throw new ServiceError(503, 'AGHU indisponível no momento. A recepção de novas amostras está bloqueada.');
  }
}

/** Busca o caso no "banco" (referência interna, não copiar para fora sem `montarCaso`). */
export function casoInterno(numeroInterno: string): CasoAp | undefined {
  const alvo = normalizarCodigo(numeroInterno);
  return db.casos.find((c) => c.numeroInterno === alvo);
}

/** Compõe o caso com conferência, não conformidades e devoluções e devolve uma cópia. */
export function montarCaso(caso: CasoAp): CasoAp {
  const composto: CasoAp = {
    ...caso,
    conferencia: db.conferencias.find((c) => c.casoNumero === caso.numeroInterno && c.resultado === 'ACEITA'),
    naoConformidades: db.naoConformidades.filter((nc) => nc.casoNumero === caso.numeroInterno),
    devolucoes: db.devolucoes.filter((d) => d.casoNumero === caso.numeroInterno),
  };
  return copia(composto);
}

/** Acrescenta um evento imutável ao histórico do caso. */
export function registrarHistorico(
  caso: CasoAp,
  usuario: Responsavel,
  setor: string,
  evento: string,
  titulo: string,
  descricao?: string,
): HistoricoCaso {
  const registro: HistoricoCaso = {
    id: proximoId('historico'),
    evento,
    titulo,
    descricao,
    setor,
    usuario,
    ocorridoEm: agoraIso(),
  };
  caso.historico.push(registro);
  return registro;
}

/** Registra auditoria de negócio clínico com estado anterior e novo (espelha `registrar_auditoria()`). */
export function registrarAuditoria(
  usuario: Responsavel,
  acao: string,
  recurso: string,
  dadosAnteriores: Record<string, unknown> | null,
  dadosNovos: Record<string, unknown> | null,
): AuditLog {
  const log: AuditLog = {
    id: proximoId('auditoria'),
    usuario,
    categoria: 'NEGOCIO_CLINICO',
    acao,
    recurso,
    dadosAnteriores,
    dadosNovos,
    ocorridoEm: agoraIso(),
  };
  db.auditoria.push(log);
  return log;
}

/** Percorre a árvore de materiais procurando o item pelo código. */
export function encontrarItem(itens: ItemMaterial[], codigo: string): ItemMaterial | undefined {
  for (const item of itens) {
    if (item.codigo === codigo) return item;
    const filho = encontrarItem(item.filhos, codigo);
    if (filho) return filho;
  }
  return undefined;
}

/** Ano corrente com 2 dígitos. */
export function anoCurto(data = new Date()): string {
  return String(data.getFullYear()).slice(-2);
}

/** Próximo número de uma sequência `<PREFIXO>-<NNNN>/<AA>` a partir dos códigos existentes. */
export function proximoNumero(prefixo: string, existentes: string[], ano = anoCurto()): string {
  const padrao = new RegExp(`^${prefixo}-(\\d{4})/${ano}$`);
  const maior = existentes.reduce((max, codigo) => {
    const m = padrao.exec(codigo);
    return m ? Math.max(max, Number(m[1])) : max;
  }, 0);
  return `${prefixo}-${String(maior + 1).padStart(4, '0')}/${ano}`;
}
