import { defineStore } from 'pinia';
import { ref } from 'vue';
import { PERFIS, type Perfil } from '../types/sae';

const CHAVE_ARMAZENAMENTO = 'saePerfil';

/** Perfil simulado em modo mocks, alternável na interface para conferir cada permissão. */
export const usePerfilStore = defineStore('perfil', () => {
  const salvo = localStorage.getItem(CHAVE_ARMAZENAMENTO) as Perfil | null;
  const atual = ref<Perfil>(salvo && PERFIS.includes(salvo) ? salvo : 'OPERADOR');

  function definir(perfil: Perfil): void {
    atual.value = perfil;
    localStorage.setItem(CHAVE_ARMAZENAMENTO, perfil);
  }

  return { atual, definir };
});
