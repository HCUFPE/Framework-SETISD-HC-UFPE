/**
 * Implementação mock da consulta de solicitações do AGHU.
 */
import { db } from '../../../mocks/ap/db';
import type { LeituraSolicitacao, SolicitacaoAghu } from '../../../types/ap';
import type { AghuService } from '../types';
import { copia, exigirAghuDisponivel, latencia, normalizarCodigo } from './util';

/**
 * Classifica uma solicitação para a recepção (pendente, recebida, devolvida ou inexistente).
 * Não verifica a disponibilidade do AGHU.
 */
export function classificarSolicitacao(codigo: string): LeituraSolicitacao {
  const alvo = normalizarCodigo(codigo);
  const solicitacao = db.solicitacoes.find((s) => s.codigoSolicitacao === alvo);
  if (!solicitacao) return { tipo: 'NAO_ENCONTRADA' };

  if (solicitacao.situacaoRecepcao === 'RECEBIDA') {
    return {
      tipo: 'RECEBIDA',
      solicitacao: copia(solicitacao),
      casoNumero: solicitacao.casoNumero ?? solicitacao.ihqCasoNumero ?? '',
    };
  }

  if (solicitacao.situacaoRecepcao === 'DEVOLVIDA') {
    const devolucao = db.devolucoes.find((d) => d.id === solicitacao.devolucaoId);
    const naoConformidade = db.naoConformidades.find((nc) => nc.id === devolucao?.naoConformidadeId);
    return {
      tipo: 'DEVOLVIDA',
      solicitacao: copia(solicitacao),
      devolvidaEm: devolucao?.devolvidaEm ?? '',
      tipoNaoConformidade: naoConformidade?.tipo ?? 'OUTRO',
    };
  }

  return { tipo: 'PENDENTE', solicitacao: copia(solicitacao) };
}

export const aghuServiceMock: AghuService = {
  async listarPendentes(): Promise<SolicitacaoAghu[]> {
    await latencia();
    exigirAghuDisponivel();
    const pendentes = db.solicitacoes
      .filter((s) => s.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO')
      .sort((a, b) => a.dataSolicitacao.localeCompare(b.dataSolicitacao));
    return copia(pendentes);
  },

  async contarPendentes(): Promise<number> {
    await latencia(50);
    return db.solicitacoes.filter((s) => s.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO').length;
  },

  async lerSolicitacao(codigo: string): Promise<LeituraSolicitacao> {
    await latencia();
    exigirAghuDisponivel();
    return classificarSolicitacao(codigo);
  },
};
