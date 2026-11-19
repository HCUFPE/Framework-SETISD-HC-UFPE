import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../services/api';

interface User {
  username: string;
  groups: string[];
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

  const isAdmin = computed(() => {
    const ADMIN_GROUP = "GLO-SEC-HCPE-SETISD"; 
    return user.value?.groups?.includes(ADMIN_GROUP) || false;
  });

  // Regra para validar se o utilizador tem permissão de Recepção e Triagem
  const isRecepcao = computed(() => {
    const RECEPCAO_GROUP = "GLO-SEC-HCPE-RECEPCAO";
    return user.value?.groups?.includes(RECEPCAO_GROUP) || user.value?.groups?.includes("RECEPCAO") || false;
  });

  // Regra para validar se o utilizador tem permissão de Patologista
  const isPatologista = computed(() => {
    const PATOLOGISTA_GROUP = "GLO-SEC-HCPE-PATOLOGISTA";
    return user.value?.groups?.includes(PATOLOGISTA_GROUP) || user.value?.groups?.includes("PATOLOGISTA") || false;
  });

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
      clearToken();
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
    await fetchUser();
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
        console.log("No valid refresh token found.");
      }
    }
  }

  return { 
    accessToken, 
    user, 
    isAuthenticated, 
    isAdmin, 
    isRecepcao,
    isPatologista,
    login, 
    logout,
    setToken,
    clearToken,
    fetchUser,
    initializeAuth
  };
});