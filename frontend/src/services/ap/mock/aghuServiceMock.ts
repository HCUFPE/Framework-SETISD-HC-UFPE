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
import { extrairCodigoEamostra, mesmaAmostra, ordenarGrupos } from '../../../helpers/aghu';
import { copia, exigirAghuDisponivel, latencia, normalizarCodigo } from './util';

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
  const cancelados = exames.filter((e) => e.situacaoRecepcao === 'CANCELADA');
  if (cancelados.length === exames.length && cancelados.length > 0) {
    return { tipo: 'CANCELADA', solicitacao: copia(cancelados[0]), cancelamentos: cancelados.map((item) => item.cancelamento) };
  }
  return { tipo: 'RECEBIDA', solicitacao: copia(exames[0]), recebimentos: recebimentos(exames) };
}

/** Classifica a solicitação: com tipos pendentes abre a conferência de todos eles. */
function classificarExames(codigoSolicitacao: string, exames: SolicitacaoAghu[], numeroAmostra: string | null = null): LeituraSolicitacao {
  if (exames.length === 0) return { tipo: 'NAO_ENCONTRADA' };
  let grupoSelecionadoId: string | null = null;
  let examesFiltrados: SolicitacaoAghu[] = [];
  let amostraBipadaSituacao: Extract<LeituraSolicitacao, { tipo: 'PENDENTE' }>['amostraBipadaSituacao'] = null;

  if (numeroAmostra !== null) {
    const dono = exames.find((e) => e.amostras.some((a) => mesmaAmostra(a.numeroAmostra, numeroAmostra)));
    if (dono) {
      if (dono.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO') {
        grupoSelecionadoId = dono.id;
        examesFiltrados = [copia(dono)];
      } else {
        amostraBipadaSituacao = {
          grupoId: dono.id,
          tipoExame: dono.tipoExameSugerido,
          situacaoRecepcao: dono.situacaoRecepcao,
          casoNumero: dono.casoNumero,
          ihqCodigo: dono.ihqCodigo,
          devolucaoId: dono.devolucaoId,
          cancelamento: dono.cancelamento,
        };
      }
    }
  }

  const pendentes = exames.filter((e) => e.situacaoRecepcao === 'AGUARDANDO_RECEBIMENTO');
  if (pendentes.length > 0) {
    return {
      tipo: 'PENDENTE',
      codigoSolicitacao,
      exames: copia(pendentes),
      ...(numeroAmostra !== null
        ? { amostraBipada: numeroAmostra, grupoSelecionadoId, examesFiltrados, amostraBipadaSituacao }
        : {}),
    };
  }
  const semPendentes = classificarSemPendentes(exames);
  if (numeroAmostra !== null && (semPendentes.tipo === 'RECEBIDA' || semPendentes.tipo === 'DEVOLVIDA')) {
    return { ...semPendentes, amostraBipada: numeroAmostra };
  }
  return semPendentes;
}

/**
 * Classifica o código lido para a recepção. Aceita o código da solicitação ("1479377"), o código
 * com a amostra ("1479377-2"), o código de barras contínuo de 10 dígitos do AGHU ("7712301001")
 * ou a chave do grupo ("1479377:HP"). Não verifica a disponibilidade do AGHU.
 */
export function classificarSolicitacao(codigoLido: string): LeituraSolicitacao {
  const { codigoSolicitacao, numeroAmostra } = extrairCodigoEamostra(codigoLido);
  const exames = examesDaSolicitacao(codigoSolicitacao);
  return classificarExames(codigoSolicitacao, exames, numeroAmostra);
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

  async cancelarExame(solicitacaoId: string, motivo: string): Promise<SolicitacaoAghu> {
    await latencia();
    const exame = db.solicitacoes.find((item) => item.id === normalizarCodigo(solicitacaoId));
    if (!exame) throw new Error(`Exame ${solicitacaoId} não encontrado.`);
    if (exame.situacaoRecepcao !== 'AGUARDANDO_RECEBIMENTO') throw new Error('O exame não está aguardando recebimento.');
    if (!motivo.trim()) throw new Error('Informe o motivo do cancelamento.');
    exame.situacaoRecepcao = 'CANCELADA';
    exame.cancelamento = {
      motivo: motivo.trim(),
      canceladoPor: { login: 'mock', nome: 'Usuário de desenvolvimento' },
      canceladoEm: new Date().toISOString(),
    };
    return copia(exame);
  },
};
