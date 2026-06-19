import axios from 'axios';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/auth';
import { useUiStore } from '../stores/ui';

const api = axios.create({
  baseURL: '/',
  headers: {
    'Content-Type': 'application/json',
  }
});

api.interceptors.request.use(config => {
  const authStore = useAuthStore();
  const uiStore = useUiStore();

  uiStore.startLoading();

  const token = authStore.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

api.interceptors.response.use(
  response => {
    useUiStore().stopLoading();
    return response;
  },
  async error => {
    useUiStore().stopLoading();

    const originalRequest = error.config;
    const authStore = useAuthStore();
    const toast = useToast();

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post('/api/token/refresh');
        authStore.setToken(data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        processQueue(null, data.access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        const router = (await import('../router')).default;
        authStore.logout(router);
        toast.error('Sua sessão expirou. Faça login novamente.');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    const message = error.response?.data?.detail || error.message || 'Ocorreu um erro inesperado.';
    toast.error(message);

    return Promise.reject(error);
  }
);

export default api;