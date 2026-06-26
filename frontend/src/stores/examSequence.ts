import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getSemestreAtual, type Semestre } from '../utils/examCode';

export const useExamSequenceStore = defineStore('examSequence', () => {
  const ano = ref(new Date().getFullYear());
  const semestre = ref<Semestre>(getSemestreAtual());
  const counter = ref(0);

  /**
   * Gera o próximo número sequencial pra um caso NOVO (não derivado).
   * Reinicia automaticamente em 0001 quando o ano ou o semestre muda.
   */
  function nextSequencial(): { sequencial: number; ano: number; semestre: Semestre } {
    const anoAtual = new Date().getFullYear();
    const semestreAtual = getSemestreAtual();

    if (anoAtual !== ano.value || semestreAtual !== semestre.value) {
      ano.value = anoAtual;
      semestre.value = semestreAtual;
      counter.value = 0;
    }

    counter.value++;
    return { sequencial: counter.value, ano: ano.value, semestre: semestre.value };
  }

  return { nextSequencial };
});