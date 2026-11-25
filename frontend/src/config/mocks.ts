/**
 * Fonte única da flag de mocks do frontend.
 * `VITE_USE_MOCKS=false` direciona os serviços para a API real documentada
 * em docs/especificacao/05-interfaces.md.
 */
export const USAR_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false';
