/**
 * Implementação mock dos casos de anatomia patológica e das ações da recepção.
 *
 * As regras de negócio ficam aqui (e não nas views) para migrarem depois para o backend.
 */
import {
  ETAPAS,
  SETOR_RECEPCAO,
  STATUS_CASO,
  STATUS_INELEGIVEIS_IHQ,
  TIPOS_EXAME,
  casoEstaAtivo,
  etapaAposRecepcao,
} from '../../../constants/ap';
import { db, proximoId } from '../../../mocks/ap/db';
import type {
  CasoAp,
  CasoElegivelIhq,
  ConfirmarEntradaInput,
  ExameIhq,
  ItemMaterial,
  ItensConferencia,
  ResolucaoCodigo,
  Responsavel,
  SolicitacaoAghu,
  TipoImpressao,
  VincularIhqInput,
} from '../../../types/ap';
import { ServiceError, type CasoService } from '../types';
import { classificarSolicitacao } from './aghuServiceMock';
import {
  agoraIso,
  casoInterno,
  copia,
  encontrarItem,
  exigirAghuDisponivel,
  latencia,
  montarCaso,
  normalizarCodigo,
  proximoNumero,
  registrarAuditoria,
  registrarHistorico,
} from './util';

/** Solicitação pendente pelo número, ou erro. */
function solicitacaoPendente(codigo: string): SolicitacaoAghu {
  const solicitacao = db.solicitacoes.find((s) => s.codigoSolicitacao === normalizarCodigo(codigo));
  if (!solicitacao) throw new ServiceError(404, `Nenhuma solicitação encontrada para ${codigo}.`);
  if (solicitacao.situacaoRecepcao !== 'AGUARDANDO_RECEBIMENTO') {
    throw new ServiceError(409, `A solicitação ${codigo} não está aguardando recebimento.`);
  }
  return solicitacao;
}

/** Exige os quatro itens da conferência marcados. */
function exigirConferenciaCompleta(conferencia: ItensConferencia): void {
  const completa =
    conferencia.identificacaoConfere &&
    conferencia.materialConfere &&
    conferencia.quantidadeConfere &&
    conferencia.recipienteAdequado;
  if (!completa) {
    throw new ServiceError(422, 'Marque todos os itens da conferência ou registre uma não conformidade.');
  }
}

/** Registra a conferência aceita. */
function registrarConferenciaAceita(
  solicitacaoCodigo: string,
  casoNumero: string,
  conferencia: ItensConferencia,
  usuario: Responsavel,
): void {
  db.conferencias.push({
    id: proximoId('conferencia'),
    solicitacaoCodigo,
    casoNumero,
    resultado: 'ACEITA',
    ...conferencia,
    conferidoPor: usuario,
    conferidoEm: agoraIso(),
  });
}

/** Caso interno ou erro 404. */
function exigirCaso(numeroInterno: string): CasoAp {
  const caso = casoInterno(numeroInterno);
  if (!caso) throw new ServiceError(404, `Caso ${numeroInterno} não encontrado.`);
  return caso;
}

/** Todos os códigos de IHQ já emitidos. */
function codigosIhq(): string[] {
  return db.casos.flatMap((c) => c.ihqs.map((i) => i.codigoInternoIhq));
}

export const casoServiceMock: CasoService = {
  async listar(): Promise<CasoAp[]> {
    await latencia();
    return db.casos.map(montarCaso);
  },

  async obter(numeroInterno: string): Promise<CasoAp | null> {
    await latencia();
    const caso = casoInterno(numeroInterno);
    return caso ? montarCaso(caso) : null;
  },

  async buscarElegiveisIhq(termo: string): Promise<CasoElegivelIhq[]> {
    await latencia(150);
    const alvo = termo.trim().toUpperCase();
    if (alvo.length < 2) return [];
    return db.casos
      .filter(
        (c) =>
          c.numeroInterno.includes(alvo) ||
          c.solicitacao.prontuario.includes(alvo) ||
          c.solicitacao.nomePaciente.includes(alvo),
      )
      .slice(0, 8)
      .map((c) => {
        const inelegivel = STATUS_INELEGIVEIS_IHQ.includes(c.status);
        return {
          numeroInterno: c.numeroInterno,
          nomePaciente: c.solicitacao.nomePaciente,
          prontuario: c.solicitacao.prontuario,
          descricaoMaterial: c.solicitacao.descricaoMaterial,
          status: c.status,
          elegivel: !inelegivel,
          motivoInelegivel: inelegivel
            ? `Caso ${STATUS_CASO[c.status].rotulo.toLowerCase()}: não pode receber IHQ.`
            : undefined,
        };
      });
  },

  async confirmarEntrada(input: ConfirmarEntradaInput, usuario: Responsavel): Promise<CasoAp> {
    await latencia();
    exigirAghuDisponivel();
    const solicitacao = solicitacaoPendente(input.solicitacaoCodigo);
    exigirConferenciaCompleta(input.conferencia);
    if (!Number.isInteger(input.quantidade) || input.quantidade < 1) {
      throw new ServiceError(400, 'Informe a quantidade de peças/frascos (1 ou mais).');
    }
    if (input.urgente && !input.motivoUrgencia?.trim()) {
      throw new ServiceError(400, 'Descreva o motivo da urgência.');
    }
    if (!input.procedimento.trim()) throw new ServiceError(400, 'Selecione o procedimento.');

    const agora = agoraIso();
    const numero = proximoNumero(input.tipoExame, db.casos.map((c) => c.numeroInterno));
    const proximaEtapa = etapaAposRecepcao(input.tipoExame);

    const materiais: ItemMaterial[] = Array.from({ length: input.quantidade }, (_, i) => ({
      codigo: i === 0 ? numero : `${numero}-F${i + 1}`,
      tipoItem: 'AMOSTRA',
      rotulo: `Amostra ${i + 1} · ${solicitacao.descricaoMaterial}`,
      origem: 'ROTINA',
      status: 'DISPONIVEL',
      criadoPor: usuario,
      criadoEm: agora,
      filhos: [],
    }));

    solicitacao.situacaoRecepcao = 'RECEBIDA';
    solicitacao.casoNumero = numero;

    const caso: CasoAp = {
      numeroInterno: numero,
      tipoExame: input.tipoExame,
      solicitacao: copia(solicitacao),
      status: 'RECEBIDO',
      etapaAtual: proximaEtapa,
      etapaAtualDesde: agora,
      dataEntradaSap: agora,
      responsavelEntrada: usuario,
      urgente: input.urgente,
      motivoUrgencia: input.urgente ? input.motivoUrgencia?.trim() : undefined,
      procedimento: input.procedimento,
      quantidade: input.quantidade,
      observacoes: input.observacoes?.trim() || undefined,
      etapas: [
        {
          etapa: 'RECEPCAO',
          sequencia: 1,
          status: 'CONCLUIDA',
          iniciadaEm: agora,
          concluidaEm: agora,
          responsavelInicio: usuario,
          responsavelFim: usuario,
        },
        { etapa: proximaEtapa, sequencia: 2, status: 'PENDENTE' },
      ],
      registros: [],
      materiais,
      ihqs: [],
      naoConformidades: [],
      devolucoes: [],
      historico: [],
    };
    db.casos.push(caso);
    registrarConferenciaAceita(solicitacao.codigoSolicitacao, numero, input.conferencia, usuario);

    registrarHistorico(
      caso,
      usuario,
      SETOR_RECEPCAO,
      'ENTRADA_CONFIRMADA',
      'Entrada confirmada',
      `Nº interno ${numero} gerado a partir da solicitação AGHU ${solicitacao.codigoSolicitacao}. Conferência aceita. Encaminhado para ${ETAPAS[proximaEtapa]}.`,
    );
    if (caso.urgente) {
      registrarHistorico(caso, usuario, SETOR_RECEPCAO, 'URGENCIA_MARCADA', 'Marcado como URGENTE', caso.motivoUrgencia);
    }
    registrarAuditoria(
      usuario,
      'ENTRADA_CONFIRMADA',
      `caso_ap:${numero}`,
      { solicitacao: solicitacao.codigoSolicitacao, situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO' },
      {
        numeroInterno: numero,
        tipoExame: input.tipoExame,
        status: 'RECEBIDO',
        etapaAtual: proximaEtapa,
        urgente: caso.urgente,
        motivoUrgencia: caso.motivoUrgencia ?? null,
        quantidade: input.quantidade,
        procedimento: input.procedimento,
      },
    );
    return montarCaso(caso);
  },

  async vincularIhq(input: VincularIhqInput, usuario: Responsavel) {
    await latencia();
    exigirAghuDisponivel();
    const solicitacao = solicitacaoPendente(input.solicitacaoCodigo);
    exigirConferenciaCompleta(input.conferencia);
    const caso = exigirCaso(input.casoOrigemNumero);
    if (STATUS_INELEGIVEIS_IHQ.includes(caso.status)) {
      throw new ServiceError(422, `O caso ${caso.numeroInterno} está ${STATUS_CASO[caso.status].rotulo.toLowerCase()} e não pode receber IHQ.`);
    }
    const divergente = caso.solicitacao.prontuario !== solicitacao.prontuario;
    if (divergente && !input.divergenciaConfirmada) {
      throw new ServiceError(422, 'O prontuário do caso difere do prontuário da solicitação. Confirme o vínculo para continuar.');
    }

    const agora = agoraIso();
    const ihq: ExameIhq = {
      codigoInternoIhq: proximoNumero('IH', codigosIhq()),
      status: 'SOLICITADA',
      solicitacaoAghuCodigo: solicitacao.codigoSolicitacao,
      recebidaEm: agora,
      registradaPor: usuario,
      anticorpos: [],
      observacao: input.observacoes?.trim() || undefined,
    };
    caso.ihqs.push(ihq);

    solicitacao.situacaoRecepcao = 'RECEBIDA';
    solicitacao.ihqCodigo = ihq.codigoInternoIhq;
    solicitacao.ihqCasoNumero = caso.numeroInterno;
    registrarConferenciaAceita(solicitacao.codigoSolicitacao, caso.numeroInterno, input.conferencia, usuario);

    const avisoDivergencia = divergente
      ? ` Vínculo confirmado apesar do prontuário divergente (solicitação ${solicitacao.prontuario}, caso ${caso.solicitacao.prontuario}).`
      : '';
    registrarHistorico(
      caso,
      usuario,
      SETOR_RECEPCAO,
      'IHQ_VINCULADA',
      `IHQ ${ihq.codigoInternoIhq} vinculada ao caso`,
      `Solicitação AGHU ${solicitacao.codigoSolicitacao} recebida pela recepção.${avisoDivergencia}`,
    );
    registrarAuditoria(
      usuario,
      'IHQ_VINCULADA',
      `exame_ihq:${ihq.codigoInternoIhq}`,
      { solicitacao: solicitacao.codigoSolicitacao, situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO' },
      {
        codigoInternoIhq: ihq.codigoInternoIhq,
        casoOrigem: caso.numeroInterno,
        status: ihq.status,
        prontuarioDivergente: divergente,
      },
    );
    return { caso: montarCaso(caso), ihq: copia(ihq) };
  },

  async cancelar(numeroInterno: string, motivo: string, usuario: Responsavel): Promise<CasoAp> {
    await latencia();
    const caso = exigirCaso(numeroInterno);
    if (!casoEstaAtivo(caso.status)) {
      throw new ServiceError(409, `O caso ${caso.numeroInterno} não pode ser cancelado no status "${STATUS_CASO[caso.status].rotulo}".`);
    }
    const motivoLimpo = motivo.trim();
    if (!motivoLimpo) throw new ServiceError(400, 'Informe o motivo do cancelamento.');

    const statusAnterior = caso.status;
    caso.status = 'CANCELADO';
    caso.cancelamento = { motivo: motivoLimpo, canceladoPor: usuario, canceladoEm: agoraIso() };
    registrarHistorico(caso, usuario, 'Chefia/Administração', 'CASO_CANCELADO', 'Caso cancelado', motivoLimpo);
    registrarAuditoria(
      usuario,
      'CASO_CANCELADO',
      `caso_ap:${caso.numeroInterno}`,
      { status: statusAnterior },
      { status: 'CANCELADO', motivo: motivoLimpo },
    );
    return montarCaso(caso);
  },

  async registrarImpressao(numeroInterno: string, tipo: TipoImpressao, usuario: Responsavel): Promise<void> {
    await latencia(100);
    const caso = exigirCaso(numeroInterno);
    const titulo = tipo === 'ETIQUETAS' ? 'Etiquetas impressas' : 'Ficha de trabalho impressa';
    const descricao =
      tipo === 'ETIQUETAS' ? `${caso.materiais.length} etiqueta(s) de frasco.` : `Ficha de trabalho ${TIPOS_EXAME[caso.tipoExame].nome}.`;
    registrarHistorico(caso, usuario, SETOR_RECEPCAO, tipo === 'ETIQUETAS' ? 'ETIQUETAS_IMPRESSAS' : 'FICHA_IMPRESSA', titulo, descricao);
    registrarAuditoria(usuario, tipo === 'ETIQUETAS' ? 'ETIQUETAS_IMPRESSAS' : 'FICHA_IMPRESSA', `caso_ap:${caso.numeroInterno}`, null, { tipo });
  },

  async registrarAcionamentoPlantao(numeroInterno: string, usuario: Responsavel): Promise<CasoAp> {
    await latencia(150);
    const caso = exigirCaso(numeroInterno);
    if (caso.tipoExame !== 'CO') throw new ServiceError(422, 'O acionamento do plantão se aplica apenas a congelação.');
    if (caso.plantaoAcionadoEm) throw new ServiceError(409, 'O acionamento da equipe de plantão já foi registrado.');
    caso.plantaoAcionadoEm = agoraIso();
    registrarHistorico(
      caso,
      usuario,
      SETOR_RECEPCAO,
      'PLANTAO_ACIONADO',
      'Equipe de plantão de congelação acionada',
      'Acionamento registrado pela recepção.',
    );
    registrarAuditoria(usuario, 'PLANTAO_ACIONADO', `caso_ap:${caso.numeroInterno}`, { plantaoAcionadoEm: null }, { plantaoAcionadoEm: caso.plantaoAcionadoEm });
    return montarCaso(caso);
  },

  async resolverCodigo(codigo: string): Promise<ResolucaoCodigo> {
    await latencia(150);
    const alvo = normalizarCodigo(codigo);
    if (!alvo) return { tipo: 'NAO_ENCONTRADA' };

    // Solicitação AGHU
    const leitura = classificarSolicitacao(alvo);
    if (leitura.tipo === 'PENDENTE') {
      exigirAghuDisponivel();
      return leitura;
    }
    if (leitura.tipo === 'DEVOLVIDA') return leitura;
    if (leitura.tipo === 'RECEBIDA') {
      const ehIhq = Boolean(leitura.solicitacao.ihqCodigo);
      return { tipo: 'CASO', casoNumero: leitura.casoNumero, aba: ehIhq ? 'ihq' : undefined };
    }

    // Caso pelo número interno
    if (casoInterno(alvo)) return { tipo: 'CASO', casoNumero: alvo };

    // IHQ pelo código interno
    const casoDaIhq = db.casos.find((c) => c.ihqs.some((i) => i.codigoInternoIhq === alvo));
    if (casoDaIhq) return { tipo: 'CASO', casoNumero: casoDaIhq.numeroInterno, aba: 'ihq' };

    // Item de material
    for (const caso of db.casos) {
      if (encontrarItem(caso.materiais, alvo)) {
        return { tipo: 'CASO', casoNumero: caso.numeroInterno, aba: 'materiais', itemCodigo: alvo };
      }
    }
    return { tipo: 'NAO_ENCONTRADA' };
  },
};
