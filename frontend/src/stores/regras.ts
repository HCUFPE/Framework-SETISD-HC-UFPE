import { defineStore } from 'pinia';
import { ref, type Ref } from 'vue';
import api from '../services/api';
import { executar } from '../services/requisicao';
import type { IIncompatibilidadeExame, IRegraExame, IRegraPrioridade } from '../types/exames';

/**
 * Regras configuráveis (/api/regras/*) — consumida pela TASK-015.
 * Suposição (TASK-006 ainda não existe no backend; ver openspec/changes/add-frontend-fila-exames/design.md):
 * GET lista, POST cria, PUT /{id} atualiza e DELETE /{id} faz soft delete, tudo em camelCase.
 */
interface RegrasPorRecurso {
  prioridades: IRegraPrioridade;
  exames: IRegraExame;
  incompatibilidades: IIncompatibilidadeExame;
}

/** Segmento da URL /api/regras/{recurso}. */
export type RecursoRegras = keyof RegrasPorRecurso;

export const useRegrasStore = defineStore('regras', () => {
  const prioridades = ref<IRegraPrioridade[]>([]);
  const regrasExames = ref<IRegraExame[]>([]);
  const incompatibilidades = ref<IIncompatibilidadeExame[]>([]);
  const carregando = ref(false);
  const erro = ref<string | null>(null);

  const listas: { [K in RecursoRegras]: Ref<RegrasPorRecurso[K][]> } = {
    prioridades,
    exames: regrasExames,
    incompatibilidades,
  };

  /** Lista as regras do recurso. */
  async function carregar<K extends RecursoRegras>(recurso: K) {
    return executar(carregando, erro, async () => {
      const { data } = await api.get<RegrasPorRecurso[K][]>(`/api/regras/${recurso}`);
      listas[recurso].value = data;
      return data;
    });
  }

  /** Cria uma regra e a acrescenta à lista local. */
  async function criar<K extends RecursoRegras>(recurso: K, dados: Omit<RegrasPorRecurso[K], 'id'>) {
    return executar(carregando, erro, async () => {
      const { data } = await api.post<RegrasPorRecurso[K]>(`/api/regras/${recurso}`, dados);
      listas[recurso].value = [...listas[recurso].value, data];
      return data;
    });
  }

  /** Atualiza uma regra e substitui a versão local. */
  async function atualizar<K extends RecursoRegras>(
    recurso: K,
    id: number,
    dados: Omit<RegrasPorRecurso[K], 'id'>,
  ) {
    return executar(carregando, erro, async () => {
      const { data } = await api.put<RegrasPorRecurso[K]>(`/api/regras/${recurso}/${id}`, dados);
      listas[recurso].value = listas[recurso].value.map((regra) => (regra.id === id ? data : regra));
      return data;
    });
  }

  /** Exclusão lógica no backend; some da lista local. */
  async function remover(recurso: RecursoRegras, id: number) {
    return executar(carregando, erro, async () => {
      await api.delete(`/api/regras/${recurso}/${id}`);
      const lista: Ref<{ id: number }[]> = listas[recurso];
      lista.value = lista.value.filter((regra) => regra.id !== id);
      return true;
    });
  }

  return {
    prioridades,
    regrasExames,
    incompatibilidades,
    carregando,
    erro,
    carregar,
    criar,
    atualizar,
    remover,
  };
});
