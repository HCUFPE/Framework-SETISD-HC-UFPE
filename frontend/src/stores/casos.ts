import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useResponsavel } from '../composables/useResponsavel';
import { auditoriaService, casoService } from '../services/ap';
import type { AuditLog, CasoAp, CasoElegivelIhq, ResolucaoCodigo, StatusCaso, TipoCasoPrincipal, TipoImpressao } from '../types/ap';

/** Filtros da Consulta de casos (mantidos ao ir e voltar do detalhe). */
export interface FiltrosConsulta {
  busca: string;
  status: StatusCaso | '';
  tipo: TipoCasoPrincipal | '';
  /** Período de entrada em dias; 0 = qualquer data. */
  periodoDias: number;
  somenteUrgentes: boolean;
}

export const filtrosConsultaVazios = (): FiltrosConsulta => ({
  busca: '',
  status: '',
  tipo: '',
  periodoDias: 0,
  somenteUrgentes: false,
});

/**
 * Casos de anatomia patológica: lista da consulta, caso aberto no detalhe e ações sobre o caso.
 */
export const useCasosStore = defineStore('casos', () => {
  const responsavel = useResponsavel();

  const casos = ref<CasoAp[]>([]);
  const carregando = ref(false);
  const casoAtual = ref<CasoAp | null>(null);
  const carregandoCaso = ref(false);
  const auditoria = ref<AuditLog[]>([]);
  const filtros = ref<FiltrosConsulta>(filtrosConsultaVazios());

  /** Carrega todos os casos para a consulta. */
  async function carregar(): Promise<void> {
    carregando.value = true;
    try {
      casos.value = await casoService.listar();
    } finally {
      carregando.value = false;
    }
  }

  /** Carrega um caso para o detalhe (`null` quando não existe). */
  async function carregarCaso(numeroInterno: string): Promise<CasoAp | null> {
    carregandoCaso.value = true;
    if (casoAtual.value?.numeroInterno !== numeroInterno) casoAtual.value = null;
    try {
      casoAtual.value = await casoService.obter(numeroInterno);
      return casoAtual.value;
    } finally {
      carregandoCaso.value = false;
    }
  }

  /** Recarrega o caso aberto, se houver. */
  async function recarregarCasoAtual(): Promise<void> {
    if (casoAtual.value) casoAtual.value = await casoService.obter(casoAtual.value.numeroInterno);
  }

  async function cancelar(numeroInterno: string, motivo: string): Promise<CasoAp> {
    const caso = await casoService.cancelar(numeroInterno, motivo, responsavel.value);
    if (casoAtual.value?.numeroInterno === numeroInterno) casoAtual.value = caso;
    return caso;
  }

  async function registrarImpressao(numeroInterno: string, tipo: TipoImpressao): Promise<void> {
    await casoService.registrarImpressao(numeroInterno, tipo, responsavel.value);
    if (casoAtual.value?.numeroInterno === numeroInterno) await recarregarCasoAtual();
  }

  function buscarElegiveisIhq(termo: string): Promise<CasoElegivelIhq[]> {
    return casoService.buscarElegiveisIhq(termo);
  }

  function resolverCodigo(codigo: string): Promise<ResolucaoCodigo> {
    return casoService.resolverCodigo(codigo);
  }

  /** Carrega a trilha de auditoria (inspeção e futura integração; não há tela). */
  async function carregarAuditoria(): Promise<AuditLog[]> {
    auditoria.value = await auditoriaService.listar();
    return auditoria.value;
  }

  return {
    casos,
    carregando,
    casoAtual,
    carregandoCaso,
    auditoria,
    filtros,
    carregar,
    carregarCaso,
    recarregarCasoAtual,
    cancelar,
    registrarImpressao,
    buscarElegiveisIhq,
    resolverCodigo,
    carregarAuditoria,
  };
});
