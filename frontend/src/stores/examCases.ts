import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ExamCaseDetail } from '../types/exam';

export const useExamCasesStore = defineStore('examCases', () => {
  const cases = ref<Record<string, ExamCaseDetail>>({});

  function upsertCase(codigoLocal: string, data: Partial<ExamCaseDetail>) {
    cases.value[codigoLocal] = {
      ...(cases.value[codigoLocal] as ExamCaseDetail),
      ...data,
      codigoLocal,
    };
  }

  function getCase(codigoLocal: string): ExamCaseDetail | null {
    return cases.value[codigoLocal] ?? null;
  }

  function findByFrasco(frascoId: string): ExamCaseDetail | null {
    return Object.values(cases.value).find(c => c.recepcao?.frascosIds.includes(frascoId)) ?? null;
  }

  return { cases, upsertCase, getCase, findByFrasco };
});