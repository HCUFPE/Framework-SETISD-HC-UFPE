import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useResponsavel } from '../composables/useResponsavel';
import { naoConformidadeService } from '../services/ap';
import type { DevolucaoDetalhada, RegistrarNaoConformidadeInput, SituacaoDevolucao } from '../types/ap';

/**
 * Não conformidades com devolução e o acompanhamento das rejeições e devoluções.
 */
export const useDevolucoesStore = defineStore('devolucoes', () => {
  const responsavel = useResponsavel();

  const devolucoes = ref<DevolucaoDetalhada[]>([]);
  const carregando = ref(false);

  async function carregar(): Promise<void> {
    carregando.value = true;
    try {
      devolucoes.value = await naoConformidadeService.listarDevolucoes();
    } finally {
      carregando.value = false;
    }
  }

  /** Registra a não conformidade com a devolução obrigatória. */
  async function registrar(input: RegistrarNaoConformidadeInput): Promise<DevolucaoDetalhada> {
    const devolucao = await naoConformidadeService.registrar(input, responsavel.value);
    devolucoes.value = [devolucao, ...devolucoes.value];
    return devolucao;
  }

  /** Atualiza a situação de uma devolução na lista. */
  async function atualizarSituacao(id: number, situacao: SituacaoDevolucao): Promise<DevolucaoDetalhada> {
    const atualizada = await naoConformidadeService.atualizarSituacao(id, situacao, responsavel.value);
    devolucoes.value = devolucoes.value.map((d) => (d.id === id ? atualizada : d));
    return atualizada;
  }

  return { devolucoes, carregando, carregar, registrar, atualizarSituacao };
});
