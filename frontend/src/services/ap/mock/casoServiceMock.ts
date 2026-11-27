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
  casoEstaAtivo,
  etapaAposRecepcao,
} from '../../../constants/ap';
import { resumoMaterial, rotuloQuantidadeAmostras } from '../../../helpers/aghu';
import { db, proximoId } from '../../../mocks/ap/db';
import type {
  CasoAp,
  CasoElegivelIhq,
  ConfirmarEntradaInput,
  ExameIhq,
  ItemMaterial,
  ResultadoBuscaCasos,
  Responsavel,
  SolicitacaoAghu,
  VincularIhqInput,
} from '../../../types/ap';
import { ServiceError, type CasoService } from '../types';
import {
  agoraIso,
  casoInterno,
  copia,
  exigirAghuDisponivel,
  latencia,
  montarCaso,
  normalizarCodigo,
  normalizarTexto,
  proximoNumero,
  registrarAuditoria,
  registrarHistorico,
} from './util';

/** Exame da solicitação pendente pela chave de recebimento, ou erro. */
function solicitacaoPendente(id: string): SolicitacaoAghu {
  const solicitacao = db.solicitacoes.find((s) => s.id === normalizarCodigo(id));
  if (!solicitacao) throw new ServiceError(404, `Nenhuma solicitação encontrada para ${id}.`);
  if (solicitacao.situacaoRecepcao !== 'AGUARDANDO_RECEBIMENTO') {
    throw new ServiceError(
      409,
      `O exame ${solicitacao.siglaExame} da solicitação ${solicitacao.codigoSolicitacao} não está aguardando recebimento.`,
    );
  }
  return solicitacao;
}

/** Registra a conferência aceita com as amostras do exame. */
function registrarConferenciaAceita(solicitacao: SolicitacaoAghu, casoNumero: string, usuario: Responsavel): void {
  db.conferencias.push({
    id: proximoId('conferencia'),
    solicitacaoId: solicitacao.id,
    solicitacaoCodigo: solicitacao.codigoSolicitacao,
    casoNumero,
    amostras: solicitacao.amostras.map((a) => a.numeroAmostra),
    resultado: 'ACEITA',
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
          tipoExame: c.tipoExame,
          nomePaciente: c.solicitacao.nomePaciente,
          prontuario: c.solicitacao.prontuario,
          descricaoMaterial: resumoMaterial(c.solicitacao),
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
    const solicitacao = solicitacaoPendente(input.solicitacaoId);
    if (solicitacao.amostras.length === 0) throw new ServiceError(422, 'O exame não tem amostras no AGHU.');
    if (!input.procedimento.trim()) throw new ServiceError(400, 'Selecione o procedimento.');

    const agora = agoraIso();
    const numero = proximoNumero(input.tipoExame, db.casos.map((c) => c.numeroInterno));
    const proximaEtapa = etapaAposRecepcao(input.tipoExame);

    // Uma amostra do caso por amostra do exame no AGHU, com o número e a descrição dela.
    const quantidade = solicitacao.amostras.length;
    const materiais: ItemMaterial[] = solicitacao.amostras.map((amostra, i) => ({
      codigo: i === 0 ? numero : `${numero}-F${i + 1}`,
      tipoItem: 'AMOSTRA',
      rotulo: `Amostra ${amostra.numeroAmostra}`,
      descricao: amostra.descricaoMaterial,
      numeroAmostraAghu: amostra.numeroAmostra,
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
      procedimento: input.procedimento,
      quantidade,
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
    registrarConferenciaAceita(solicitacao, numero, usuario);

    registrarHistorico(
      caso,
      usuario,
      SETOR_RECEPCAO,
      'ENTRADA_CONFIRMADA',
      'Entrada confirmada',
      `Nº interno ${numero} gerado a partir da solicitação AGHU ${solicitacao.codigoSolicitacao} (exame ${solicitacao.siglaExame}, ${rotuloQuantidadeAmostras(quantidade)}: ${solicitacao.amostras.map((a) => a.numeroAmostra).join(', ')}). Conferência aceita. Encaminhado para ${ETAPAS[proximaEtapa]}.`,
    );
    if (caso.urgente) {
      registrarHistorico(caso, usuario, SETOR_RECEPCAO, 'URGENCIA_MARCADA', 'Marcado como URGENTE', 'Urgência da solicitação AGHU.');
    }
    registrarAuditoria(
      usuario,
      'ENTRADA_CONFIRMADA',
      `caso_ap:${numero}`,
      { solicitacao: solicitacao.codigoSolicitacao, exame: solicitacao.siglaExame, situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO' },
      {
        numeroInterno: numero,
        tipoExame: input.tipoExame,
        status: 'RECEBIDO',
        etapaAtual: proximaEtapa,
        urgente: caso.urgente,
        quantidade,
        amostras: solicitacao.amostras.map((a) => a.numeroAmostra),
        procedimento: input.procedimento,
      },
    );
    return montarCaso(caso);
  },

  async vincularIhq(input: VincularIhqInput, usuario: Responsavel) {
    await latencia();
    exigirAghuDisponivel();
    const solicitacao = solicitacaoPendente(input.solicitacaoId);
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
    registrarConferenciaAceita(solicitacao, caso.numeroInterno, usuario);

    const avisoDivergencia = divergente
      ? ` Vínculo confirmado apesar do prontuário divergente (solicitação ${solicitacao.prontuario}, caso ${caso.solicitacao.prontuario}).`
      : '';
    registrarHistorico(
      caso,
      usuario,
      SETOR_RECEPCAO,
      'IHQ_VINCULADA',
      `IHQ ${ihq.codigoInternoIhq} vinculada ao caso`,
      `Solicitação AGHU ${solicitacao.codigoSolicitacao} (exame ${solicitacao.siglaExame}, amostra(s) ${solicitacao.amostras.map((a) => a.numeroAmostra).join(', ')}) recebida pela recepção.${avisoDivergencia}`,
    );
    registrarAuditoria(
      usuario,
      'IHQ_VINCULADA',
      `exame_ihq:${ihq.codigoInternoIhq}`,
      { solicitacao: solicitacao.codigoSolicitacao, exame: solicitacao.siglaExame, situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO' },
      {
        codigoInternoIhq: ihq.codigoInternoIhq,
        casoOrigem: caso.numeroInterno,
        status: ihq.status,
        prontuarioDivergente: divergente,
      },
    );
    return { caso: montarCaso(caso), ihq: copia(ihq), solicitacao: copia(solicitacao) };
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

  async buscar(termo: string, limite: number): Promise<ResultadoBuscaCasos> {
    await latencia(120);
    const alvo = normalizarTexto(termo);
    if (!alvo) return { itens: [], total: 0 };
    const encontrados = db.casos
      .filter((c) =>
        [
          c.numeroInterno,
          c.solicitacao.prontuario,
          c.solicitacao.nomePaciente,
          c.solicitacao.codigoSolicitacao,
          // IHQ vinculadas: o código da solicitação delas também leva ao caso de origem
          ...c.ihqs.map((i) => i.solicitacaoAghuCodigo),
        ].some((campo) => normalizarTexto(campo).includes(alvo)),
      )
      .sort((a, b) => {
        const exato = (c: CasoAp) =>
          normalizarTexto(c.numeroInterno) === alvo || normalizarTexto(c.solicitacao.codigoSolicitacao) === alvo ? 0 : 1;
        const exatoA = exato(a);
        const exatoB = exato(b);
        return exatoA - exatoB || b.dataEntradaSap.localeCompare(a.dataEntradaSap);
      });
    return {
      total: encontrados.length,
      itens: encontrados.slice(0, limite).map((c) => ({
        numeroInterno: c.numeroInterno,
        tipoExame: c.tipoExame,
        nomePaciente: c.solicitacao.nomePaciente,
        prontuario: c.solicitacao.prontuario,
        codigoSolicitacao: c.solicitacao.codigoSolicitacao,
        status: c.status,
      })),
    };
  },
};
