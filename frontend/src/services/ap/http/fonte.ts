/**
 * Fonte das solicitações AGHU exibidas na recepção, lida de `VITE_AP_FONTE_SOLICITACOES`.
 *
 * Módulo sem dependências, para poder ser usado pelo "banco" do mock sem ciclo de imports.
 */
export type FonteSolicitacoes = 'api' | 'mock';

/** Fonte configurada em `VITE_AP_FONTE_SOLICITACOES` (padrão: mock). */
export function fonteSolicitacoes(): FonteSolicitacoes {
  return (import.meta.env.VITE_AP_FONTE_SOLICITACOES ?? '').trim().toLowerCase() === 'api' ? 'api' : 'mock';
}
