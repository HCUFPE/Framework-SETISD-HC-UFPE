import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../services/api';
import { MOCK_USERS } from '../mocks/mockUsers';
import { Sector } from '../constants/sectors';

const USE_MOCK_AUTH = import.meta.env.VITE_USE_MOCK_AUTH === 'true';

interface User {
  username: string;
  groups: string[];
  givenName?: string[];
  userPrincipalName?: string[];
  title?: string[];
  department?: string[];
  employeeNumber?: string[];
  setor?: Sector;
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('accessToken') || null);
  const user = ref<User | null>(null);

  const isAuthenticated = computed(() => !!accessToken.value);
  const isAdmin = computed(() => {
    const ADMIN_GROUP = "GLO-SEC-HCPE-SETISD"; 
    return user.value?.groups?.includes(ADMIN_GROUP) || false;
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
    if (USE_MOCK_AUTH) {
      const mockUser = MOCK_USERS.find(u => u.username === username && u.password === password);
      if (!mockUser) {
        throw new Error('Usuário ou senha inválidos.');
      }
      setToken(`mock-token-${mockUser.username}`);
      setUser({
        username: mockUser.username,
        groups: mockUser.groups,
        givenName: [mockUser.fullName],
        setor: mockUser.setor,
      });
      return;
    }

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
    if (!USE_MOCK_AUTH) {
      try {
        await api.post('/api/logout');
      } catch (error) {
        console.error("Logout failed, but clearing token anyway.", error);
      }
    }
    clearToken();
    if (router) {
      router.push({ name: 'Login' });
    }
  }

  async function initializeAuth() {
    if (USE_MOCK_AUTH && accessToken.value?.startsWith('mock-token-')) {
      const username = accessToken.value.replace('mock-token-', '');
      const mockUser = MOCK_USERS.find(u => u.username === username);
      if (mockUser) {
        setUser({
          username: mockUser.username,
          groups: mockUser.groups,
          givenName: [mockUser.fullName],
          setor: mockUser.setor,
        });
      } else {
        clearToken();
      }
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
        console.log("No valid refresh token found.");
      }
    }
  }

  return { 
    accessToken, 
    user, 
    isAuthenticated, 
    isAdmin, 
    login, 
    logout,
    setToken,
    clearToken,
    fetchUser,
    initializeAuth
  };
});