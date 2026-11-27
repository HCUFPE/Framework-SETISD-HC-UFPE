import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../services/api';
import { executar } from '../services/requisicao';
import type { IFiltrosKpi, IKpiDashboard } from '../types/exames';

/**
 * KPIs da Central (GET /api/dashboard/kpis) — consumida pela TASK-016.
 * Backend na branch feat/task-011-dashboard-auditoria: exige o grupo administrativo (403 para os demais).
 */
export const useDashboardStore = defineStore('dashboard', () => {
  const kpis = ref<IKpiDashboard | null>(null);
  const carregando = ref(false);
  const erro = ref<string | null>(null);

  /** Carrega os KPIs; período inclusivo em ISO 8601 (sem offset = UTC). */
  async function carregarKpis(filtros: IFiltrosKpi = {}) {
    const params = Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor));
    const resultado = await executar(carregando, erro, async () => {
      kpis.value = (await api.get<IKpiDashboard>('/api/dashboard/kpis', { params })).data;
      return kpis.value;
    });
    if (resultado === null) kpis.value = null;
    return resultado;
  }

  return { kpis, carregando, erro, carregarKpis };
});
