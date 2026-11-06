/**
 * "Banco" em memória do mock do Sistema AP.
 *
 * Usado apenas pelas implementações mock dos serviços (`services/ap/mock`). Os dados voltam à
 * carga inicial ao recarregar a página.
 */
import { criarCargaInicial, type MockDb } from './seed';

export let db: MockDb = criarCargaInicial(new Date());

/** Recria a carga inicial (útil para demonstrações e verificação manual). */
export function reiniciarDb(): void {
  db = criarCargaInicial(new Date());
}

/** Próximo identificador numérico da sequência informada. */
export function proximoId(sequencia: keyof MockDb['sequencias']): number {
  db.sequencias[sequencia] += 1;
  return db.sequencias[sequencia];
}

/** Simula indisponibilidade (ou retorno) do AGHU. */
export function definirAghuDisponivel(disponivel: boolean): void {
  db.aghuDisponivel = disponivel;
}
