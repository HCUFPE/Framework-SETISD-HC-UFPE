/** Implementações HTTP dos contratos AP existentes; não usa estado mock como fallback. */
import type { AxiosResponse } from 'axios';
import api from '../api';
import type {
  CasoElegivelIhq,
  AuditLog,
  CasoAp,
  ConfirmarEntradaInput,
  DevolucaoDetalhada,
  ExameIhq,
  LeituraSolicitacao,
  RegistrarNaoConformidadeInput,
  ResultadoBuscaCasos,
  Responsavel,
  SituacaoDevolucao,
  SolicitacaoAghu,
  VincularIhqInput,
} from '../../types/ap';
import { ServiceError, type AghuService, type AuditoriaService, type CasoService, type NaoConformidadeService } from './types';

async function requisicao<T>(operacao: () => Promise<AxiosResponse<T>>): Promise<T> {
  try {
    const resposta = await operacao();
    return resposta.data;
  } catch (erro: unknown) {
    if (erro && typeof erro === 'object' && 'isAxiosError' in erro) {
      const axiosErro = erro as {
        response?: { status?: number; data?: { detail?: unknown } };
        message?: string;
      };
      const status = axiosErro.response?.status ?? 503;
      const detail = axiosErro.response?.data?.detail;
      throw new ServiceError(
        status,
        typeof detail === 'string'
          ? detail
          : status === 503
            ? 'Não foi possível conectar ao servidor. Tente novamente.'
            : axiosErro.message ?? 'Não foi possível concluir a operação.',
      );
    }
    throw new ServiceError(503, 'Não foi possível conectar ao servidor. Tente novamente.');
  }
}

/** Argumentos Responsavel mantidos por compatibilidade; nunca são enviados à API. */
export const aghuServiceHttp: AghuService = {
  listarPendentes: () => requisicao(() => api.get('/api/ap/solicitacoes/pendentes')),
  contarPendentes: () => requisicao(() => api.get('/api/ap/solicitacoes/pendentes/contagem')),
  lerSolicitacao: (codigo) => requisicao(() => api.get(`/api/ap/solicitacoes/${encodeURIComponent(codigo)}`)),
};

export const casoServiceHttp: CasoService = {
  listar: () => requisicao(() => api.get('/api/ap/casos')),
  obter: async (numeroInterno) => {
    try {
      return await requisicao(() => api.get(`/api/ap/casos/${encodeURIComponent(numeroInterno)}`));
    } catch (erro) {
      if (erro instanceof ServiceError && erro.status === 404) return null;
      throw erro;
    }
  },
  buscarElegiveisIhq: (termo) => requisicao(() => api.get('/api/ap/casos/elegiveis-ihq', { params: { termo } })),
  confirmarEntrada: (input: ConfirmarEntradaInput, _usuario: Responsavel) =>
    requisicao(() => api.post('/api/ap/recebimentos', input)),
  vincularIhq: (input: VincularIhqInput, _usuario: Responsavel) =>
    requisicao(() => api.post('/api/ap/recebimentos/ihq', input)),
  cancelar: (numeroInterno: string, motivo: string, _usuario: Responsavel) =>
    requisicao(() => api.post('/api/ap/casos/cancelamento', { numeroInterno, motivo })),
  registrarAcionamentoPlantao: (numeroInterno: string, _usuario: Responsavel) =>
    requisicao(() => api.post('/api/ap/casos/acionamentos-plantao', { numeroInterno })),
  buscar: (termo: string, limite: number) =>
    requisicao(() => api.get('/api/ap/casos/busca', { params: { termo, limite } })),
};

export const naoConformidadeServiceHttp: NaoConformidadeService = {
  registrar: (input: RegistrarNaoConformidadeInput, _usuario: Responsavel) =>
    requisicao(() => api.post('/api/ap/nao-conformidades', input)),
  listarDevolucoes: () => requisicao(() => api.get('/api/ap/devolucoes')),
  atualizarSituacao: (devolucaoId: number, situacao: SituacaoDevolucao, _usuario: Responsavel) =>
    requisicao(() => api.patch(`/api/ap/devolucoes/${devolucaoId}/situacao`, { situacao })),
};

export const auditoriaServiceHttp: AuditoriaService = {
  listar: () => requisicao(() => api.get('/api/ap/auditoria')),
};

export type { AuditLog, CasoAp, CasoElegivelIhq, DevolucaoDetalhada, ExameIhq, LeituraSolicitacao, ResultadoBuscaCasos, SolicitacaoAghu };
