import { computed, type ComputedRef } from 'vue';
import { useAuthStore } from '../stores/auth';
import type { Responsavel } from '../types/ap';

/**
 * Usuário autenticado como responsável pelas ações (nunca digitado pelo usuário).
 */
export function useResponsavel(): ComputedRef<Responsavel> {
  const authStore = useAuthStore();
  return computed(() => {
    const usuario = authStore.user;
    const login = usuario?.username ?? 'desconhecido';
    const nome = usuario?.displayName?.[0] || usuario?.givenName?.[0] || login;
    return { login, nome };
  });
}
