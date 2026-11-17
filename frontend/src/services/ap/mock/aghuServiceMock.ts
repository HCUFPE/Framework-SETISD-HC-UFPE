/**
 * Implementação mock da consulta de solicitações do AGHU.
 *
 * A conferência é feita por solicitação. Dentro dela, cada tipo de exame (grupo código + tipo) é
 * recebido ou devolvido como uma unidade; tipos diferentes podem ser recebidos em momentos diferentes.
 */
import { db } from '../../../mocks/ap/db';
import type { LeituraSolicitacao, RecebimentoExame, SolicitacaoAghu } from '../../../types/ap';
import type { AghuService } from '../types';
import { aguardarCargaSolicitacoes } from '../http/cargaSolicitacoes';
import { ordenarGrupos } from '../../../helpers/aghu';
import { copia, exigirAghuDisponivel, latencia, normalizarCodigo } from './util';

/** Separador do código lido com o número da amostra (ex.: "1479377-2"). */
const SEPARADOR_AMOSTRA = '-';

/** Grupos de tipos de exame (todas as situações) de uma solicitação do AGHU. */
export function examesDaSolicitacao(codigoSolicitacao: string): SolicitacaoAghu[] {
  return ordenarGrupos(db.solicitacoes.filter((s) => s.codigoSolicitacao === codigoSolicitacao));
}

/** Exame (referência interna) pela chave de recebimento. */
export function exameInterno(id: string): SolicitacaoAghu | undefined {
  return db.solicitacoes.find((s) => s.id === id);
}

/** Exames já recebidos e os casos/IHQs que geraram. */
function recebimentos(exames: SolicitacaoAghu[]): RecebimentoExame[] {
  return exames
    .filter((e) => e.situacaoRecepcao === 'RECEBIDA')
    .map((e) => ({
      siglaExame: e.siglaExame,
      nomeExame: e.nomeExame,
      casoNumero: e.casoNumero ?? e.ihqCasoNumero ?? '',
      ihqCodigo: e.ihqCodigo,
    }));
}

/** Classifica exames sem nenhum pendente: devolvidos ou já recebidos. */
function classificarSemPendentes(exames: SolicitacaoAghu[]): LeituraSolicitacao {
  const devolvido = exames.find((e) => e.situacaoRecepcao === 'DEVOLVIDA');
  if (devolvido) {
    const devolucao = db.devolucoes.find((d) => d.id === devolvido.devolucaoId);
    const naoConformidade = db.naoConformidades.find((nc) => nc.id === devolucao?.naoConformidadeId);
    return {
      tipo: 'DEVOLVIDA',
      solicitacao: copia(devolvido),
      devolvidaEm: devolucao?.devolvidaEm ?? '',
      tipoNaoConformidade: naoConformidade?.tipo ?? 'OUTROS',
    };
  }
  return { tipo: 'RECEBIDA', solicitacao: copia(exames[0]), recebimentos: recebimentos(exames) };
}

/** Classifica a solicitação: com tipos pendentes abre a conferência de todos eles. */
function classificarExames(codigoSolicitacao: string, exames: SolicitacaoAghu[]): LeituraSolicitacao {
  if (exames.length === 0) return { tipo: 'NAO_ENCONTRADA' };
  const pendentes = exames.filter((e) => e.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO');
  if (pendentes.length > 0) return { tipo: 'PENDENTE', codigoSolicitacao, exames: copia(pendentes) };
  return classificarSemPendentes(exames);
}

/**
 * Classifica o código lido para a recepção. Aceita o código da solicitação ("1479377"), o código
 * com a amostra ("1479377-2") ou a chave do grupo ("1479377:HP"): todos abrem a solicitação inteira.
 * Não verifica a disponibilidade do AGHU.
 */
export function classificarSolicitacao(codigoLido: string): LeituraSolicitacao {
  const alvo = normalizarCodigo(codigoLido);

  const porChave = exameInterno(alvo);
  if (porChave) return classificarExames(porChave.codigoSolicitacao, examesDaSolicitacao(porChave.codigoSolicitacao));

  const exames = examesDaSolicitacao(alvo);
  if (exames.length > 0) return classificarExames(alvo, exames);

  const posicao = alvo.lastIndexOf(SEPARADOR_AMOSTRA);
  if (posicao > 0) {
    const codigo = alvo.slice(0, posicao).trim();
    const numero = alvo.slice(posicao + 1).trim();
    const daSolicitacao = examesDaSolicitacao(codigo);
    if (daSolicitacao.some((e) => e.amostras.some((a) => a.numeroAmostra === numero))) return classificarExames(codigo, daSolicitacao);
  }
  return { tipo: 'NAO_ENCONTRADA' };
}

/** Exames pendentes, Congelação primeiro e depois do mais antigo para o mais novo. */
function pendentes(): SolicitacaoAghu[] {
  return db.solicitacoes.filter((s) => s.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO');
}

export const aghuServiceMock: AghuService = {
  async listarPendentes(): Promise<SolicitacaoAghu[]> {
    await aguardarCargaSolicitacoes();
    await latencia();
    exigirAghuDisponivel();
    return copia(pendentes().sort((a, b) => a.dataSolicitacao.localeCompare(b.dataSolicitacao)));
  },

  /** Quantidade de solicitações (não de tipos de exame) com algo aguardando recebimento. */
  async contarPendentes(): Promise<number> {
    await aguardarCargaSolicitacoes();
    await latencia(50);
    return new Set(pendentes().map((s) => s.codigoSolicitacao)).size;
  },

  async lerSolicitacao(codigo: string): Promise<LeituraSolicitacao> {
    await aguardarCargaSolicitacoes();
    await latencia();
    exigirAghuDisponivel();
    return classificarSolicitacao(codigo);
  },

  async listarExamesDaSolicitacao(codigoSolicitacao: string): Promise<SolicitacaoAghu[]> {
    await aguardarCargaSolicitacoes();
    await latencia(50);
    return copia(examesDaSolicitacao(normalizarCodigo(codigoSolicitacao)));
  },
};
