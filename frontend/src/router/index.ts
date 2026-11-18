import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Configuracoes from '../views/Configuracoes.vue';

import Exemplos from '../views/Exemplos.vue';
import Pacientes from '../views/Pacientes.vue';
// Temporária: vitrine das mudanças do change evolve-base-components.
import NovidadesComponentes from '../views/NovidadesComponentes.vue';

// Fluxo de recepção (Sistema AP)
import RecepcaoAmostras from '../views/ap/RecepcaoAmostras.vue';
import ConsultaCasos from '../views/ap/ConsultaCasos.vue';
import DetalheCaso from '../views/ap/DetalheCaso.vue';
import RejeicoesDevolucoes from '../views/ap/RejeicoesDevolucoes.vue';

declare module 'vue-router' {
  interface RouteMeta {
    layout?: string;
    requiresAuth?: boolean;
    requiresPermission?: string;
    /** Item do menu lateral destacado nesta rota. */
    menu?: string;
  }
}

const routes = [
  {
    path: '/',
    name: 'Início',
    component: Home,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'LoginLayout' },
  },
  {
    path: '/componentes',
    name: 'Componentes',
    component: Exemplos,
  },
  {
    path: '/novidades-componentes',
    name: 'Novidades dos Componentes',
    component: NovidadesComponentes,
  },
  {
    path: '/exemplo',
    name: 'Exemplo',
    component: Pacientes,
    meta: { requiresAuth: true, requiresPermission: 'casos:consultar' },
  },
  {
    path: '/configuracoes',
    name: 'Configuracoes',
    component: Configuracoes,
    meta: { requiresAuth: true, requiresPermission: 'usuarios:gerenciar' },
  },
  {
    path: '/recepcao',
    name: 'Recepção de amostras',
    component: RecepcaoAmostras,
    meta: { requiresAuth: true, requiresPermission: 'recepcao:receber', menu: 'recepcao' },
  },
  {
    path: '/casos',
    name: 'Consulta de casos',
    component: ConsultaCasos,
    meta: { requiresAuth: true, requiresPermission: 'casos:consultar', menu: 'consulta' },
  },
  {
    // O número interno contém barra (ex.: /casos/HP-0003/26).
    path: '/casos/:numero(.*)',
    name: 'Detalhe do caso',
    component: DetalheCaso,
    props: true,
    meta: { requiresAuth: true, requiresPermission: 'casos:consultar', menu: 'consulta' },
  },
  {
    path: '/rejeicoes-devolucoes',
    name: 'Rejeições e devoluções',
    component: RejeicoesDevolucoes,
    meta: { requiresAuth: true, requiresPermission: 'devolucoes:consultar', menu: 'devolucoes' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'bg-paper-active-link',
  linkExactActiveClass: 'bg-paper-active-link',
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  await authStore.initializeAuth();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'Login' };
  } else if (to.meta.requiresPermission && !authStore.hasPermission(to.meta.requiresPermission)) {
    return { name: 'Início' };
  }
  return true;
});

export default router;
