/**
 * Implementação mock de não conformidades, devoluções e do acompanhamento das devoluções.
 *
 * Regra (RF020/RF021): toda não conformidade gera devolução.
 */
import {
  ETAPAS,
  SETOR_RECEPCAO,
  SITUACOES_DEVOLUCAO,
  SITUACOES_DEVOLUCAO_FINAIS,
  STATUS_CASO,
  TIPOS_NAO_CONFORMIDADE,
  casoEstaAtivo,
} from '../../../constants/ap';
import { db, proximoId } from '../../../mocks/ap/db';
import type {
  Devolucao,
  DevolucaoDetalhada,
  EtapaCodigo,
  NaoConformidade,
  RegistrarNaoConformidadeInput,
  Responsavel,
  SituacaoDevolucao,
} from '../../../types/ap';
import { ServiceError, type NaoConformidadeService } from '../types';
import { agoraIso, casoInterno, copia, latencia, normalizarCodigo, registrarAuditoria, registrarHistorico } from './util';

/** Junta a devolução à sua não conformidade. */
function detalhar(devolucao: Devolucao): DevolucaoDetalhada {
  const naoConformidade = db.naoConformidades.find((nc) => nc.id === devolucao.naoConformidadeId);
  if (!naoConformidade) throw new ServiceError(500, `Não conformidade da devolução ${devolucao.id} não encontrada.`);
  return copia({ ...devolucao, naoConformidade, rejeicaoNaRecepcao: !devolucao.casoNumero });
}

export const naoConformidadeServiceMock: NaoConformidadeService = {
  async registrar(input: RegistrarNaoConformidadeInput, usuario: Responsavel): Promise<DevolucaoDetalhada> {
    await latencia();
    const descricao = input.descricao.trim();
    if (!descricao) throw new ServiceError(400, 'Descreva o que foi encontrado.');

    const agora = agoraIso();
    let casoNumero: string | undefined;
    let solicitacaoCodigo: string | undefined;
    let unidadeOrigem: string;
    let etapa: string;
    let etapaCodigo: EtapaCodigo = 'RECEPCAO';
    const contexto = input.contexto;

    if (contexto.tipo === 'SEM_ETIQUETA') {
      unidadeOrigem = input.unidadeOrigem?.trim() ?? '';
      if (!unidadeOrigem) throw new ServiceError(400, 'Selecione a unidade de origem.');
      etapa = 'Recepção (leitura)';
    } else if (contexto.tipo === 'SOLICITACAO') {
      const solicitacao = db.solicitacoes.find((s) => s.codigoSolicitacao === normalizarCodigo(contexto.solicitacaoCodigo));
      if (!solicitacao) throw new ServiceError(404, `Solicitação ${contexto.solicitacaoCodigo} não encontrada.`);
      if (solicitacao.situacaoRecepcao !== 'AGUARDANDO_RECEBIMENTO') {
        throw new ServiceError(409, `A solicitação ${solicitacao.codigoSolicitacao} não está aguardando recebimento.`);
      }
      solicitacaoCodigo = solicitacao.codigoSolicitacao;
      unidadeOrigem = solicitacao.unidade;
      etapa = 'Recepção (conferência)';
      db.conferencias.push({
        id: proximoId('conferencia'),
        solicitacaoCodigo,
        resultado: 'REJEITADA',
        ...contexto.conferencia,
        observacao: `${TIPOS_NAO_CONFORMIDADE[input.tipo]} — ${descricao}`,
        conferidoPor: usuario,
        conferidoEm: agora,
      });
    } else {
      const caso = casoInterno(contexto.casoNumero);
      if (!caso) throw new ServiceError(404, `Caso ${contexto.casoNumero} não encontrado.`);
      if (!casoEstaAtivo(caso.status)) {
        throw new ServiceError(409, `O caso ${caso.numeroInterno} está "${STATUS_CASO[caso.status].rotulo}" e não aceita não conformidade.`);
      }
      casoNumero = caso.numeroInterno;
      solicitacaoCodigo = caso.solicitacao.codigoSolicitacao;
      unidadeOrigem = caso.solicitacao.unidade;
      etapaCodigo = caso.etapaAtual ?? 'RECEPCAO';
      etapa = ETAPAS[etapaCodigo];
    }

    const naoConformidade: NaoConformidade = {
      id: proximoId('naoConformidade'),
      casoNumero,
      solicitacaoCodigo,
      tipo: input.tipo,
      descricao,
      setor: SETOR_RECEPCAO,
      etapa,
      etapaCodigo,
      unidadeOrigem,
      registradoPor: usuario,
      registradoEm: agora,
      status: input.novaAmostraSolicitada ? 'ABERTA' : 'RESOLVIDA',
    };
    const devolucao: Devolucao = {
      id: proximoId('devolucao'),
      naoConformidadeId: naoConformidade.id,
      casoNumero,
      solicitacaoCodigo,
      unidadeOrigem,
      devolvidoPor: usuario,
      novaAmostraSolicitada: input.novaAmostraSolicitada,
      situacao: input.novaAmostraSolicitada ? 'AGUARDANDO_NOVA_AMOSTRA' : 'ENCERRADA',
      devolvidaEm: agora,
    };
    db.naoConformidades.push(naoConformidade);
    db.devolucoes.push(devolucao);

    // Efeitos
    if (contexto.tipo === 'SOLICITACAO') {
      const solicitacao = db.solicitacoes.find((s) => s.codigoSolicitacao === solicitacaoCodigo);
      if (solicitacao) {
        solicitacao.situacaoRecepcao = 'DEVOLVIDA';
        solicitacao.devolucaoId = devolucao.id;
      }
    }
    let statusAnterior: string | null = null;
    if (casoNumero) {
      const caso = casoInterno(casoNumero)!;
      statusAnterior = caso.status;
      caso.status = 'DEVOLVIDO';
      registrarHistorico(
        caso,
        usuario,
        SETOR_RECEPCAO,
        'NAO_CONFORMIDADE',
        'Não conformidade registrada',
        `${TIPOS_NAO_CONFORMIDADE[input.tipo]} — ${descricao} (identificada em ${etapa}).`,
      );
      registrarHistorico(
        caso,
        usuario,
        SETOR_RECEPCAO,
        'DEVOLUCAO',
        'Material devolvido à origem',
        `Devolvido à unidade ${unidadeOrigem}. Nova amostra solicitada: ${input.novaAmostraSolicitada ? 'Sim' : 'Não'}.`,
      );
    }

    registrarAuditoria(
      usuario,
      'NAO_CONFORMIDADE_DEVOLUCAO',
      `devolucao:${devolucao.id}`,
      casoNumero ? { caso: casoNumero, status: statusAnterior } : solicitacaoCodigo ? { solicitacao: solicitacaoCodigo, situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO' } : null,
      {
        naoConformidade: naoConformidade.id,
        tipo: input.tipo,
        etapa,
        caso: casoNumero ?? null,
        solicitacao: solicitacaoCodigo ?? null,
        status: casoNumero ? 'DEVOLVIDO' : null,
        situacaoDevolucao: devolucao.situacao,
      },
    );
    return detalhar(devolucao);
  },

  async listarDevolucoes(): Promise<DevolucaoDetalhada[]> {
    await latencia();
    return [...db.devolucoes].sort((a, b) => b.devolvidaEm.localeCompare(a.devolvidaEm)).map(detalhar);
  },

  async atualizarSituacao(devolucaoId: number, situacao: SituacaoDevolucao, usuario: Responsavel): Promise<DevolucaoDetalhada> {
    await latencia(150);
    const devolucao = db.devolucoes.find((d) => d.id === devolucaoId);
    if (!devolucao) throw new ServiceError(404, 'Devolução não encontrada.');
    const anterior = devolucao.situacao;
    if (anterior === situacao) return detalhar(devolucao);

    devolucao.situacao = situacao;
    const naoConformidade = db.naoConformidades.find((nc) => nc.id === devolucao.naoConformidadeId);
    const statusNcAnterior = naoConformidade?.status;
    if (naoConformidade) {
      naoConformidade.status = SITUACOES_DEVOLUCAO_FINAIS.includes(situacao) ? 'RESOLVIDA' : 'ABERTA';
    }
    if (devolucao.casoNumero) {
      const caso = casoInterno(devolucao.casoNumero);
      if (caso) {
        registrarHistorico(
          caso,
          usuario,
          SETOR_RECEPCAO,
          'DEVOLUCAO_ATUALIZADA',
          'Situação da devolução atualizada',
          `${SITUACOES_DEVOLUCAO[anterior].rotulo} → ${SITUACOES_DEVOLUCAO[situacao].rotulo}.`,
        );
      }
    }
    registrarAuditoria(
      usuario,
      'DEVOLUCAO_SITUACAO_ATUALIZADA',
      `devolucao:${devolucao.id}`,
      { situacao: anterior, statusNaoConformidade: statusNcAnterior ?? null },
      { situacao, statusNaoConformidade: naoConformidade?.status ?? null },
    );
    return detalhar(devolucao);
  },
};
