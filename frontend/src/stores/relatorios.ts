import { defineStore } from 'pinia';
import { ref } from 'vue';
import { listarRelatorios, obterRelatorio } from '../services/sae';
import type { FiltroIndicadores, Relatorio, ResultadoRelatorio } from '../types/sae';

export const useRelatoriosStore = defineStore('relatorios', () => {
  const relatorios = ref<Relatorio[]>([]);
  const selecionado = ref('volume-por-exame');
  const filtros = ref<FiltroIndicadores>({ periodo: 'todos', tipoExame: '' });
  const resultado = ref<ResultadoRelatorio | null>(null);
  const carregando = ref(false);
  const erro = ref('');

  async function carregarCatalogo(): Promise<void> {
    relatorios.value = await listarRelatorios();
  }

  async function gerar(): Promise<void> {
    carregando.value = true;
    erro.value = '';
    try {
      resultado.value = await obterRelatorio(selecionado.value, filtros.value);
    } catch (e) {
      resultado.value = null;
      erro.value = e instanceof Error ? e.message : 'Não foi possível gerar o relatório.';
    } finally {
      carregando.value = false;
    }
  }

  return { relatorios, selecionado, filtros, resultado, carregando, erro, carregarCatalogo, gerar };
});
