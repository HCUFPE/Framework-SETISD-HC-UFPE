import { defineStore } from 'pinia';
import { ref } from 'vue';
import { listarCriterios, salvarVersaoCriterios } from '../services/sae';
import type { CriterioPriorizacao, VersaoCriterios } from '../types/sae';
import { useAuthStore } from './auth';

export const useCriteriosStore = defineStore('criterios', () => {
  const criterios = ref<CriterioPriorizacao[]>([]);
  const versoes = ref<VersaoCriterios[]>([]);
  const justificativa = ref('');
  const carregando = ref(false);
  const erro = ref('');

  async function carregar(): Promise<void> {
    carregando.value = true;
    erro.value = '';
    try {
      const resposta = await listarCriterios();
      criterios.value = resposta.criterios.sort((a, b) => a.ordem - b.ordem);
      versoes.value = resposta.versoes;
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível carregar os critérios.';
    } finally {
      carregando.value = false;
    }
  }

  async function salvar(): Promise<boolean> {
    carregando.value = true;
    erro.value = '';
    try {
      const autor = useAuthStore().user?.displayName?.[0] ?? 'Área Gestora';
      const resposta = await salvarVersaoCriterios(criterios.value, justificativa.value, autor);
      criterios.value = resposta.criterios.sort((a, b) => a.ordem - b.ordem);
      versoes.value = resposta.versoes;
      justificativa.value = '';
      return true;
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível salvar a nova versão.';
      return false;
    } finally {
      carregando.value = false;
    }
  }

  function adicionar(): void {
    criterios.value.push({
      id: `crit-${crypto.randomUUID()}`,
      chave: `criterio${criterios.value.length + 1}`,
      nome: 'Novo critério',
      descricao: '',
      peso: 10,
      ordem: criterios.value.length + 1,
      ativo: true,
    });
  }

  function remover(id: string): void {
    // Exclusão lógica: critérios inativos deixam de compor a pontuação.
    const criterio = criterios.value.find((item) => item.id === id);
    if (criterio) criterio.ativo = false;
  }

  return { criterios, versoes, justificativa, carregando, erro, carregar, salvar, adicionar, remover };
});
