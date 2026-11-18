import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../services/api';
import { carregarSolicitacoesDoBackend } from '../services/ap/http/cargaSolicitacoes';

interface User {
  username: string;
  groups: string[];
  profiles: string[];
  permissions: string[];
  auth_provider?: string;
  displayName?: string[];
  email?: string[];
  givenName?: string[];
  userPrincipalName?: string[];
  title?: string[];
  department?: string[];
  employeeNumber?: string[];
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('accessToken') || null);
  const user = ref<User | null>(null);

  const isAuthenticated = computed(() => !!accessToken.value);
  // O administrador mock não representa autoridade para administrar contas institucionais.
  const isAdmin = computed(() => user.value?.auth_provider !== 'mock' &&
    (user.value?.profiles?.includes('COORDENACAO_ADMINISTRADOR') || false));
  const mockUsers = ref<{ username: string; displayName: string; profiles: string[] }[]>([]);
  const mockEnabled = ref(false);
  let initialization: Promise<void> | null = null;

  function hasPermission(permission: string): boolean {
    return user.value?.permissions?.includes(permission) || false;
  }

  async function loadAuthOptions() {
    const { data } = await api.get('/api/auth/options');
    mockEnabled.value = data.mock_enabled;
    mockUsers.value = data.users;
  }

  function setToken(token: string) {
    accessToken.value = token;
    localStorage.setItem('accessToken', token);
  }

  function clearToken() {
    accessToken.value = null;
    localStorage.removeItem('accessToken');
    user.value = null;
  }

  function setUser(userData: User | null) {
    user.value = userData;
  }

  async function fetchUser() {
    if (!accessToken.value) {
      setUser(null);
      return;
    }
    try {
      const { data } = await api.get('/api/users/me');
      setUser(data);
    } catch (error) {
      console.error("Failed to fetch user info:", error);
      clearToken(); // Clear token if user info fetch fails
    }
  }

  async function login(username: string, password: string, rememberMe: boolean) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    if (rememberMe) {
      params.append('remember_me', 'true');
    }

    const { data } = await api.post('/api/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    setToken(data.access_token);
    await fetchUser(); // Fetch user info immediately after login
    // Modo híbrido: carrega as solicitações AGHU do backend antes de a recepção listar pendentes
    if (accessToken.value) await carregarSolicitacoesDoBackend();
  }

  async function logout(router?: any) {
    try {
      await api.post('/api/logout');
    } catch (error) {
      console.error("Logout failed, but clearing token anyway.", error);
    } finally {
      clearToken();
      if (router) {
        router.push({ name: 'Login' });
      }
    }
  }

  async function initializeAuth() {
    if (!initialization) {
      initialization = (async () => {
        if (accessToken.value) {
          await fetchUser();
        } else {
          try {
            const { data } = await api.post('/api/token/refresh');
            if (data.access_token) {
              setToken(data.access_token);
              await fetchUser();
            }
          } catch {
            // Sessão ausente: o usuário seguirá para a tela de login.
          }
        }
      })();
    }
    await initialization;
    // Página recarregada já autenticada: (re)carrega as solicitações AGHU do backend
    if (accessToken.value) await carregarSolicitacoesDoBackend();
  }

  return {
    accessToken, 
    user, 
    isAuthenticated, 
    isAdmin, 
    mockUsers,
    mockEnabled,
    hasPermission,
    loadAuthOptions,
    login, 
    logout,
    setToken,
    clearToken,
    fetchUser,
    initializeAuth
  };
});
