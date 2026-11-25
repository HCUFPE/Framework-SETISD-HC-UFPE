import { defineStore } from 'pinia';
import { ref } from 'vue';
import { listarEventosIntegracao, reprocessarEventoIntegracao } from '../services/sae';
import type { FormsEvento, StatusFormsEvento } from '../types/sae';

/** Histórico de eventos da integração Microsoft Forms → AGHUX. */
export const useIntegracoesStore = defineStore('integracoes', () => {
  const eventos = ref<FormsEvento[]>([]);
  const carregando = ref(false);
  const reprocessandoId = ref('');
  const erro = ref('');
  const mensagem = ref('');

  async function listar(limit = 50): Promise<void> {
    carregando.value = true;
    erro.value = '';
    mensagem.value = '';
    try {
      eventos.value = await listarEventosIntegracao(limit);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível carregar os eventos de integração.';
    } finally {
      carregando.value = false;
    }
  }

  async function reprocessar(responseId: string): Promise<StatusFormsEvento | null> {
    erro.value = '';
    mensagem.value = '';
    reprocessandoId.value = responseId;
    try {
      const atualizado = await reprocessarEventoIntegracao(responseId);
      const indice = eventos.value.findIndex((evento) => evento.responseId === atualizado.responseId);
      if (indice >= 0) {
        eventos.value.splice(indice, 1, atualizado);
      } else {
        eventos.value.unshift(atualizado);
      }
      mensagem.value = `Evento ${responseId} reprocessado. Status atual: ${atualizado.status}.`;
      return atualizado.status;
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível reprocessar o evento.';
      return null;
    } finally {
      reprocessandoId.value = '';
    }
  }

  return {
    eventos,
    carregando,
    reprocessandoId,
    erro,
    mensagem,
    listar,
    reprocessar,
  };
});
