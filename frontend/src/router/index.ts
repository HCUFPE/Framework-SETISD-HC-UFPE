import { createRouter, createWebHistory, NavigationGuardNext } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { USAR_MOCKS } from '../config/mocks';
import type { Perfil } from '../types/sae';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Configuracoes from '../views/Configuracoes.vue';
import Exemplos from '../views/Exemplos.vue';
import Pacientes from '../views/Pacientes.vue';
import FilaMarcacao from '../views/FilaMarcacao.vue';
import Agendamentos from '../views/Agendamentos.vue';
import PainelGestao from '../views/PainelGestao.vue';
import Relatorios from '../views/Relatorios.vue';
import CriteriosPriorizacao from '../views/CriteriosPriorizacao.vue';
import Equipe from '../views/Equipe.vue';
import Integracoes from '../views/Integracoes.vue';
import AcessoNegado from '../views/AcessoNegado.vue';

const perfisOperacao: Perfil[] = ['OPERADOR', 'CHEFIA', 'AREA_GESTORA'];
const perfisGestao: Perfil[] = ['CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'];
const perfisAdmin: Perfil[] = ['AREA_GESTORA', 'ADMIN_TI'];

/** Grupo corporativo do framework que também autoriza o acesso (login mock admin/admin). */
export const GRUPO_ADMIN_SEGURANCA = 'GLO-SEC-HCPE-SETISD';
type PapelAcesso = Perfil | typeof GRUPO_ADMIN_SEGURANCA;

export const papeisAgendamentos: PapelAcesso[] = [
  'OPERADOR', 'CHEFIA', 'AREA_GESTORA', 'ADMIN_TI', 'COORDENACAO', GRUPO_ADMIN_SEGURANCA,
];

/** Avalia perfis locais e grupos do AD usando a mesma regra do guard de rotas. */
export function possuiPapel(authStore: ReturnType<typeof useAuthStore>, papeis: PapelAcesso[]): boolean {
  return papeis.some((papel) => papel === GRUPO_ADMIN_SEGURANCA
    ? (authStore.user?.groups ?? []).includes(GRUPO_ADMIN_SEGURANCA)
    : authStore.temPerfil(papel));
}

const routes = [
  {
    path: '/',
    name: 'Início',
    component: Home,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'LoginLayout' },
  },
  {
    path: '/acesso-negado',
    name: 'AcessoNegado',
    component: AcessoNegado,
    meta: { requiresAuth: true },
  },
  {
    path: '/fila',
    name: 'Fila de Marcação',
    component: FilaMarcacao,
    meta: { requiresAuth: true, roles: perfisOperacao },
  },
  {
    path: '/agendamentos',
    name: 'Agendamentos',
    component: Agendamentos,
    meta: { requiresAuth: true, roles: papeisAgendamentos },
  },
  {
    path: '/painel',
    name: 'Painel de Gestão',
    component: PainelGestao,
    meta: { requiresAuth: true, roles: perfisGestao },
  },
  {
    path: '/relatorios',
    name: 'Relatórios',
    component: Relatorios,
    meta: { requiresAuth: true, roles: perfisGestao },
  },
  {
    path: '/criterios',
    name: 'Critérios de Priorização',
    component: CriteriosPriorizacao,
    meta: { requiresAuth: true, roles: ['AREA_GESTORA' as Perfil] },
  },
  {
    path: '/equipe',
    name: 'Equipe e Perfis',
    component: Equipe,
    meta: { requiresAuth: true, roles: perfisAdmin },
  },
  {
    path: '/integracoes',
    name: 'integracoes',
    component: Integracoes,
    meta: { requiresAuth: true, roles: ['AREA_GESTORA' as Perfil, 'ADMIN_TI' as Perfil] },
  },
  {
    path: '/componentes',
    name: 'Componentes',
    component: Exemplos,
    meta: { requiresAuth: true },
  },
  {
    path: '/exemplo',
    name: 'Exemplo',
    component: Pacientes,
    meta: { requiresAuth: true },
  },
  {
    path: '/configuracoes',
    name: 'Configuracoes',
    component: Configuracoes,
    meta: { requiresAuth: true },
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

  if (to.meta.requiresAuth && !authStore.isAuthenticated && !USAR_MOCKS) {
    next({ name: 'Login' });
    return;
  }

  const papeis = to.meta.roles as PapelAcesso[] | undefined;
  if (papeis && papeis.length > 0 && !possuiPapel(authStore, papeis)) {
    next({ name: 'AcessoNegado' });
    return;
  }

  next();
});

export default router;
