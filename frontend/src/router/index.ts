import { createRouter, createWebHistory, NavigationGuardNext } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Admin from '../views/Admin.vue';

import Exemplos from '../views/Exemplos.vue';
import Pacientes from '../views/Pacientes.vue';
import Solicitacoes from '../views/Solicitacoes.vue';
import Altas from '../views/Altas.vue';
import Alertas from '../views/Alertas.vue';
import Indicadores from '../views/Indicadores.vue';
import Historico from '../views/Historico.vue';

const routes = [
  {
    path: '/',
    name: 'Leitos',
    component: Home,
    meta: { title: 'Gestao de Leitos da UTI' },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'LoginLayout' },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true },
  },

  {
    path: '/exemplos',
    name: 'Exemplos',
    component: Exemplos,
  },
  {
    path: '/pacientes',
    name: 'Pacientes',
    component: Pacientes,
    meta: { requiresAuth: true },
  },
  {
    path: '/solicitacoes',
    name: 'Solicitacoes',
    component: Solicitacoes,
    meta: { title: 'Solicitacoes de Vaga' },
  },
  {
    path: '/altas',
    name: 'Altas',
    component: Altas,
    meta: { title: 'Solicitacoes de Alta' },
  },
  {
    path: '/alertas',
    name: 'Alertas',
    component: Alertas,
    meta: { title: 'Alertas do Sistema' },
  },
  {
    path: '/indicadores',
    name: 'Indicadores',
    component: Indicadores,
    meta: { title: 'Indicadores Operacionais' },
  },
  {
    path: '/historico',
    name: 'Historico',
    component: Historico,
    meta: { title: 'Historico de Acoes' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'bg-paper-active-link',
  linkExactActiveClass: 'bg-paper-active-link',
});

router.beforeEach((to, _from, next: NavigationGuardNext) => {
  const authStore = useAuthStore();
  const isLoginRoute = to.name === 'Login';

  if (!authStore.isAuthenticated && !isLoginRoute) {
    next({ name: 'Login', query: { redirect: to.fullPath } });
    return;
  }

  if (authStore.isAuthenticated && isLoginRoute) {
    next({ name: 'Leitos' });
    return;
  }

  next();
});

export default router;
