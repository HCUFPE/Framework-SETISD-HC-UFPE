import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import api from '../services/api';
import { USAR_MOCKS } from '../config/mocks';
import { usuarioMock } from '../mocks/fixtures';
import { usePerfilStore } from './perfil';
import type { Perfil } from '../types/sae';

export interface User {
  username: string;
  groups: string[];
  displayName?: string[];
  email?: string[];
  givenName?: string[];
  userPrincipalName?: string[];
  title?: string[];
  department?: string[];
  employeeNumber?: string[];
  perfis?: Perfil[];
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('accessToken') || null);
  const user = ref<User | null>(null);
  const perfilStore = usePerfilStore();

  const isAuthenticated = computed(() => !!accessToken.value);
  const perfilAtivo = computed<Perfil>(() => perfilStore.atual);
  const isAdmin = computed(() => {
    const ADMIN_GROUP = 'GLO-SEC-HCPE-SETISD';
    return (
      user.value?.perfis?.includes('ADMIN_TI') === true ||
      user.value?.groups?.includes(ADMIN_GROUP) === true
    );
  });

  function temPerfil(...perfis: Perfil[]): boolean {
    if (perfis.length === 0) return true;
    if (USAR_MOCKS) return perfis.includes(perfilAtivo.value);
    return !!user.value?.perfis?.some((perfil) => perfis.includes(perfil));
  }

  function setToken(token: string): void {
    accessToken.value = token;
    localStorage.setItem('accessToken', token);
  }

  function clearToken(): void {
    accessToken.value = null;
    localStorage.removeItem('accessToken');
    user.value = null;
  }

  function setUser(userData: User | null): void {
    user.value = userData;
  }

  async function fetchUser(): Promise<void> {
    if (USAR_MOCKS) {
      setUser(usuarioMock());
      return;
    }
    if (!accessToken.value) {
      setUser(null);
      return;
    }
    try {
      const { data } = await api.get<User>('/api/users/me');
      setUser(data);
    } catch (error) {
      console.error('Falha ao carregar usuário:', error);
      clearToken();
    }
  }

  async function login(username: string, password: string, rememberMe: boolean): Promise<void> {
    if (USAR_MOCKS) {
      setToken('mock-access-token');
      await fetchUser();
      return;
    }
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    if (rememberMe) {
      params.append('remember_me', 'true');
    }
    const { data } = await api.post('/api/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    setToken(data.access_token);
    await fetchUser();
  }

  async function logout(router?: any): Promise<void> {
    if (!USAR_MOCKS) {
      try {
        await api.post('/api/logout');
      } catch (error) {
        console.error('Falha ao encerrar sessão, limpando credenciais locais.', error);
      }
    }
    clearToken();
    if (router) {
      router.push({ name: 'Login' });
    }
  }

  async function initializeAuth(): Promise<void> {
    if (USAR_MOCKS) {
      if (!accessToken.value) setToken('mock-access-token');
      await fetchUser();
      return;
    }
    if (accessToken.value) {
      await fetchUser();
    } else {
      try {
        const { data } = await api.post('/api/token/refresh');
        if (data.access_token) {
          setToken(data.access_token);
          await fetchUser();
        }
      } catch (error) {
        console.log('Nenhum refresh token válido encontrado.');
      }
    }
  }

  return {
    accessToken,
    user,
    isAuthenticated,
    isAdmin,
    perfilAtivo,
    temPerfil,
    setToken,
    clearToken,
    setUser,
    fetchUser,
    login,
    logout,
    initializeAuth,
  };
});
