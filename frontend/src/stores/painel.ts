import { defineStore } from 'pinia';
import { ref } from 'vue';
import { listarIndicadores } from '../services/sae';
import type { FiltroIndicadores, Indicadores } from '../types/sae';

export const usePainelStore = defineStore('painel', () => {
  const indicadores = ref<Indicadores | null>(null);
  const filtros = ref<FiltroIndicadores>({ periodo: '168', tipoExame: '' });
  const carregando = ref(false);
  const erro = ref('');

  async function carregar(): Promise<void> {
    carregando.value = true;
    erro.value = '';
    try {
      indicadores.value = await listarIndicadores(filtros.value);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível carregar os indicadores.';
    } finally {
      carregando.value = false;
    }
  }

  return { indicadores, filtros, carregando, erro, carregar };
});
