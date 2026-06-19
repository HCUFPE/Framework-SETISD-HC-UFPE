import { createRouter, createWebHistory, NavigationGuardNext } from 'vue-router';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/auth';
import Dashboard from '../views/dashboard.vue';
import Login from '../views/auth/login.vue';
import Register from '../views/auth/register.vue';
import ForgotPassword from '../views/auth/forgotPassword.vue';
import Escaneamento from '../views/scanning.vue';
import Recepcao from '../views/frontDesk.vue';
import Macroscopia from '../views/macroscopy.vue';
import Microscopia from '../views/microscopy.vue';
import ProcessamentoTecnico from '../views/technicalProcessing.vue';
import NotFound from '../views/notFound.vue';

const routes = [
  { 
    path: '/', 
    name: 'Dashboard', 
    component: Dashboard,
    meta: { title: 'Dashboard' }
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: Login, 
    meta: { layout: 'LoginLayout', public: true, title: 'Login' } 
  },
  { 
    path: '/cadastro', 
    name: 'Register', 
    component: Register, 
    meta: { layout: 'LoginLayout', public: true, title: 'Criar conta' } 
  },
  { 
    path: '/esqueci-senha', 
    name: 'ForgotPassword', 
    component: ForgotPassword, 
    meta: { layout: 'LoginLayout', public: true, title: 'Recuperar senha' } 
  },
  { 
    path: '/escaneamento', 
    name: 'Escaneamento', 
    component: Escaneamento,
    meta: { title: 'Escaneamento' }
  },
  { 
    path: '/recepcao', 
    name: 'Recepcao', 
    component: Recepcao, 
    meta: { sector: 'recepcao', title: 'Recepção' } 
  },
  { 
    path: '/macroscopia', 
    name: 'Macroscopia', 
    component: Macroscopia, 
    meta: { sector: 'macroscopia', title: 'Macroscopia' } 
  },
  { 
    path: '/microscopia', 
    name: 'Microscopia', 
    component: Microscopia, 
    meta: { sector: 'microscopia', title: 'Microscopia' } 
  },
  { 
    path: '/processamento-tecnico', 
    name: 'ProcessamentoTecnico', 
    component: ProcessamentoTecnico, 
    meta: { sector: 'processamento_tecnico', title: 'Processamento Técnico' } 
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: { public: true, title: 'Página não encontrada' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'bg-lab-active-link',
  linkExactActiveClass: 'bg-lab-active-link',
});

router.beforeEach((to, _from, next: NavigationGuardNext) => {
  const authStore = useAuthStore();
  const toast = useToast();

  if (!to.meta.public && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } });
    return;
  }

  if (to.meta.sector && authStore.user?.setor !== to.meta.sector) {
    toast.error('Você não tem acesso a este setor.');
    next({ name: 'Dashboard' });
    return;
  }

  next();
});

export default router;