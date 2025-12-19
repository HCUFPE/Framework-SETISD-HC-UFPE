import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../services/api';

// Tipagem correta para suportar tanto MockAuth quanto Active Directory
interface User {
  username: string;
  groups: string[];

  // Campos opcionais vindos do AD
  givenName?: string[];
  userPrincipalName?: string[];
  title?: string[];
  department?: string[];
  employeeNumber?: string[];
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('accessToken') || null);
  let initialUser: User | null = null;
  try {
    const storedUser = localStorage.getItem('user');
    initialUser = storedUser ? JSON.parse(storedUser) : null;
  } catch (error) {
    console.warn("Could not parse stored user", error);
  }
  const user = ref<User | null>(initialUser);

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
    localStorage.removeItem('user');
    user.value = null;
  }

  function setUser(userData: User | null) {
    user.value = userData;
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData));
    } else {
      localStorage.removeItem('user');
    }
  }

  async function fetchUser() {
    if (!accessToken.value) {
      setUser(null);
      return;
    }
    if (accessToken.value.startsWith('mock-token-')) {
      // Skip remote fetch when using mock auth so the session survives refresh
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

    try {
      const { data } = await api.post('/api/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      setToken(data.access_token);
      await fetchUser();
    } catch (error) {
      console.warn("Using mock login (fallback). Replace with real API response when available.", error);
      const mockToken = `mock-token-${Date.now()}`;
      setToken(mockToken);
      setUser({
        username,
        groups: [],
        givenName: [username.split('@')[0] || 'Usuario'],
        userPrincipalName: [username],
        title: ['Profissional de Saude'],
        department: ['UTI'],
        employeeNumber: ['000000'],
      });
    }
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
      } catch {
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
