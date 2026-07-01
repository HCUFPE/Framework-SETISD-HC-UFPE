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
import Congelamento from '../views/freezing.vue';
import Admin from '../views/admin.vue';
import NotFound from '../views/notFound.vue';

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { title: 'Dashboard' } },
  { path: '/login', name: 'Login', component: Login, meta: { layout: 'LoginLayout', public: true, title: 'Login' } },
  { path: '/cadastro', name: 'Register', component: Register, meta: { layout: 'LoginLayout', public: true, title: 'Criar conta' } },
  { path: '/esqueci-senha', name: 'ForgotPassword', component: ForgotPassword, meta: { layout: 'LoginLayout', public: true, title: 'Recuperar senha' } },
  { path: '/escaneamento', name: 'Escaneamento', component: Escaneamento, meta: { title: 'Escaneamento' } },
  { path: '/recepcao', name: 'Recepcao', component: Recepcao, meta: { title: 'Recepção' } },
  { path: '/macroscopia', name: 'Macroscopia', component: Macroscopia, meta: { title: 'Macroscopia' } },
  { path: '/processamento-tecnico', name: 'ProcessamentoTecnico', component: ProcessamentoTecnico, meta: { title: 'Processamento Técnico' } },
  { path: '/microscopia', name: 'Microscopia', component: Microscopia, meta: { title: 'Microscopia' } },
  { path: '/congelamento', name: 'Congelamento', component: Congelamento, meta: { title: 'Congelamento' } },
  { path: '/admin', name: 'Admin', component: Admin, meta: { requiresAdmin: true, title: 'TI / Administração' } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound, meta: { public: true, title: 'Página não encontrada' } },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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

  if (to.meta.requiresAdmin && authStore.user?.setor !== 'admin') {
    toast.error('Acesso restrito à Administração.');
    next({ name: 'Dashboard' });
    return;
  }

  next();
});

export default router;