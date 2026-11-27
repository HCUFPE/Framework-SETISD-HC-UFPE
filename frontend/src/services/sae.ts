/**
 * Camada de serviços do SAE-HC.
 * As views consomem somente esta camada, que usa mocks ou a API real conforme
 * VITE_USE_MOCKS. Os contratos HTTP estão em docs/especificacao/05-interfaces.md.
 */
import api from './api';
import { USAR_MOCKS } from '../config/mocks';
import { REFERENCIA_EM, agoraIso, horasDesdeReferencia, paraIsoLocal, somarHoras } from '../config/tempo';
import { calcularPontuacao, clonar, consultarAdMock, mockDb } from '../mocks/fixtures';
import { classificarPrioridade } from '../utils/format';
import type {
  AdUser,
  AgendaSlot,
  Agendamento,
  CalendarioAgendamentos,
  CriterioPriorizacao,
  EventoHistorico,
  FiltroFila,
  FiltroIndicadores,
  FormsEvento,
  Indicadores,
  PacienteAgendamentos,
  PropostaAgendamentoFila,
  Relatorio,
  ResultadoContato,
  ResultadoFila,
  ResultadoRelatorio,
  Solicitacao,
  SugestaoAgendamento,
  UsuarioEquipe,
  VersaoCriterios,
} from '../types/sae';

const pausa = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 120));

const FILTROS_TODOS: FiltroFila = {
  busca: '', status: '', tipoExame: '', unidadeSolicitante: '',
  periodo: 'todos', pagina: 1, porPagina: 20,
};

function registrar(acao: string, autor: string, categoria: EventoHistorico['categoria'], detalhes: string): void {
  mockDb.auditoria.unshift({
    id: `aud-${crypto.randomUUID()}-${Math.random().toString(36).slice(2, 7)}`,
    em: agoraIso(),
    acao,
    autor,
    categoria,
    detalhes,
  });
}

function filtrarPorPeriodo(solicitacao: Solicitacao, periodo: string): boolean {
  if (periodo === 'todos' || !periodo) return true;
  const horas = Number(periodo);
  return Number.isFinite(horas) && horasDesdeReferencia(solicitacao.recebidaEm) <= horas;
}

/** Fila completa, ordenada da solicitação mais prioritária para a menos prioritária. */
function filaCompleta(filtros: FiltroFila): Solicitacao[] {
  const termo = filtros.busca.trim().toLowerCase();
  return mockDb.solicitacoes
    .map((item) => {
      const pontuacao = calcularPontuacao(item.atributos, mockDb.criterios);
      return { ...clonar(item), pontuacao, prioridade: classificarPrioridade(pontuacao) };
    })
    .filter((item) => {
      const alvo = [
        item.pacienteNome,
        item.protocolo,
        item.prontuario,
        item.exame,
        item.setorSolicitante,
        ...item.itensExame.map((exame) => exame.nomeExame),
      ].join(' ').toLowerCase();
      const buscaOk = !termo || alvo.includes(termo);
      const statusOk = !filtros.status || item.status === filtros.status;
      const tipoOk = !filtros.tipoExame || item.tipoExame === filtros.tipoExame;
      const unidadeOk = !filtros.unidadeSolicitante
        || item.setorSolicitante === filtros.unidadeSolicitante;
      return buscaOk && statusOk && tipoOk && unidadeOk && filtrarPorPeriodo(item, filtros.periodo);
    })
    .sort((a, b) => b.pontuacao - a.pontuacao
      || new Date(a.recebidaEm).getTime() - new Date(b.recebidaEm).getTime()
      || a.codigoSolicitacaoAghux.localeCompare(b.codigoSolicitacaoAghux));
}

export async function listarFila(filtros: FiltroFila): Promise<ResultadoFila> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<ResultadoFila>('/api/fila', { params: filtros });
    return data;
  }
  await pausa();
  const itens = filaCompleta(filtros);
  const porPagina = Math.max(1, filtros.porPagina || 20);
  const totalPaginas = Math.max(1, Math.ceil(itens.length / porPagina));
  const pagina = Math.min(Math.max(1, filtros.pagina || 1), totalPaginas);
  return {
    itens: itens.slice((pagina - 1) * porPagina, pagina * porPagina),
    total: itens.length,
    pagina,
    porPagina,
    totalPaginas,
  };
}

/** Unidades solicitantes disponíveis para o filtro da fila. */
export async function listarUnidadesSolicitantes(): Promise<string[]> {
  if (!USAR_MOCKS) {
    // Endpoint de fila ainda pendente no backend; a lista vem da própria fila.
    const { data } = await api.get<ResultadoFila>('/api/fila', {
      params: { ...FILTROS_TODOS, porPagina: 500 },
    });
    return Array.from(new Set(data.itens.map((item) => item.setorSolicitante))).sort();
  }
  return Array.from(
    new Set(mockDb.solicitacoes.map((item) => item.setorSolicitante)),
  ).sort();
}

export async function obterSolicitacao(id: string): Promise<Solicitacao> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<Solicitacao>(`/api/solicitacoes/${id}`);
    return data;
  }
  await pausa();
  const encontrada = filaCompleta(FILTROS_TODOS).find((item) => item.id === id);
  if (!encontrada) throw new Error('Solicitação não encontrada.');
  return encontrada;
}

export async function validarSolicitacao(id: string, justificativa: string, autor: string): Promise<Solicitacao> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Solicitacao>(`/api/solicitacoes/${id}/validacao`, { justificativa, autor });
    return data;
  }
  await pausa();
  const solicitacao = mockDb.solicitacoes.find((item) => item.id === id);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  const pendentes = solicitacao.divergencias.filter((divergencia) => !divergencia.tratada);
  if (pendentes.length > 0 && !justificativa.trim()) {
    throw new Error('Trate as divergências ou informe uma justificativa antes de validar.');
  }
  pendentes.forEach((divergencia) => {
    divergencia.tratada = true;
    divergencia.justificativa = justificativa.trim();
  });
  solicitacao.status = 'AGUARDANDO_CONTATO';
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: 'Dados validados com assinatura eletrônica',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: justificativa.trim() ? `Justificativa: ${justificativa.trim()}` : 'Validação concluída sem divergências pendentes.',
  });
  registrar('Validação de solicitação', autor, 'NEGOCIO_CLINICO', `${solicitacao.protocolo} validado.`);
  return clonar(solicitacao);
}

export async function registrarContato(
  id: string,
  resultado: ResultadoContato,
  operador: string,
  observacao: string,
): Promise<Solicitacao> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Solicitacao>(`/api/solicitacoes/${id}/contatos`, {
      resultado,
      operador,
      observacao,
    });
    return data;
  }
  await pausa();
  const solicitacao = mockDb.solicitacoes.find((item) => item.id === id);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  solicitacao.contatos.push({
    id: `con-${crypto.randomUUID()}`,
    realizadoEm: agoraIso(),
    canal: 'Telefone',
    resultado,
    operador,
    observacao,
  });
  solicitacao.status = resultado === 'ACEITE'
    ? 'AGUARDANDO_CONFIRMACAO'
    : 'AGUARDANDO_REAGENDAMENTO';
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: `Contato registrado: ${resultado.toLowerCase().replace('_', ' ')}`,
    autor: operador,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: observacao || 'Registro de retorno do contato com o paciente.',
  });
  return clonar(solicitacao);
}

export async function efetivarAgendamento(id: string, dataHora: string, autor: string): Promise<Solicitacao> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Solicitacao>(`/api/solicitacoes/${id}/agendamento`, { dataHora, autor });
    return data;
  }
  await pausa();
  const solicitacao = mockDb.solicitacoes.find((item) => item.id === id);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  if (solicitacao.status !== 'AGUARDANDO_CONTATO' && solicitacao.status !== 'AGUARDANDO_CONFIRMACAO') {
    throw new Error('A solicitação precisa estar aguardando contato ou confirmação.');
  }
  if (!solicitacao.contatos.some((contato) => contato.resultado === 'ACEITE')) {
    throw new Error('Registre o aceite do paciente antes de efetivar o agendamento.');
  }
  solicitacao.status = 'AGENDADA';
  solicitacao.agendamento = {
    dataHora,
    unidade: solicitacao.setorSolicitante,
    confirmadoPor: autor,
    criadoEm: agoraIso(),
  };
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: 'Agendamento registrado na agenda local',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: `Horário reservado no SAE-HC: ${solicitacao.agendamento.dataHora}. Nenhuma marcação foi enviada ao AGHUX.`,
  });
  return clonar(solicitacao);
}

export async function agendarDaFila(
  id: string,
  slotId: string,
  autor: string,
): Promise<Solicitacao> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Solicitacao>(`/api/solicitacoes/${id}/agendar`, {
      slotId, autor,
    });
    return data;
  }
  await pausa();
  const solicitacao = mockDb.solicitacoes.find((item) => item.id === id);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  if (solicitacao.status !== 'RECEBIDA') {
    throw new Error('Somente solicitações recebidas podem ser agendadas da fila.');
  }
  const slot = slotsAgendaMock.find((item) => item.id === slotId);
  if (!slot) throw new Error('Vaga não encontrada.');
  if (agendamentosMock.some((item) =>
    (item.status === 'ATIVO' || item.status === 'PROPOSTO') && item.solicitacaoId === solicitacao.id)) {
    throw new Error('Esta solicitação já possui agendamento ativo.');
  }
  const chave = chavePacienteMock(solicitacao.prontuario);
  if (agendamentosMock.some((item) =>
    (item.status === 'ATIVO' || item.status === 'PROPOSTO') && item.pacienteChave === chave &&
    item.slotId === slotId)) {
    throw new Error('Já existe agendamento ativo para este paciente neste horário.');
  }
  solicitacao.status = 'AGUARDANDO_CONTATO';
  solicitacao.agendamento = {
    dataHora: slot.inicio,
    unidade: slot.unidade,
    confirmadoPor: autor,
    criadoEm: agoraIso(),
  };
  const agendamento: Agendamento = {
    id: `ag-${crypto.randomUUID()}`,
    solicitacaoId: solicitacao.id,
    protocolo: solicitacao.protocolo,
    pacienteChave: chave,
    pacienteNome: solicitacao.pacienteNome,
    prontuario: solicitacao.prontuario,
    unidade: slot.unidade,
    exame: slot.nomeExame,
    slotId: slot.id,
    dataHora: slot.inicio,
    status: 'ATIVO',
    confirmadoPor: autor,
    criadoEm: agoraIso(),
    justificativa: null,
  };
  agendamentosMock.push(agendamento);
  sincronizarOcupacaoMock();
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: 'Agendamento registrado na agenda local (da fila)',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: `Horário reservado no SAE-HC: ${slot.inicio}.`,
  });
  registrar('Agendamento da fila', autor, 'NEGOCIO_CLINICO',
    `${solicitacao.protocolo} → ${slot.inicio}.`);
  return clonar(solicitacao);
}

export async function cancelarDaFila(
  id: string,
  justificativa: string,
  autor: string,
): Promise<{ solicitacaoId: string; status: string; agendamentoCancelado: boolean }> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<{ solicitacaoId: string; status: string; agendamentoCancelado: boolean }>(
      `/api/solicitacoes/${id}/cancelar`, { justificativa, autor },
    );
    return data;
  }
  await pausa();
  const solicitacao = mockDb.solicitacoes.find((item) => item.id === id);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  if (![
    'AGUARDANDO_CONFIRMACAO', 'NAO_CONFIRMADO', 'AGUARDANDO_REAGENDAMENTO', 'AGENDADA',
  ].includes(solicitacao.status)) {
    throw new Error('Esta solicitação não pode ser cancelada.');
  }
  solicitacao.status = 'RECEBIDA';
  let cancelado = false;
  const ag = agendamentosMock.find((item) =>
    item.solicitacaoId === solicitacao.id
    && (item.status === 'ATIVO' || item.status === 'PROPOSTO'));
  if (ag) {
    ag.status = 'CANCELADO';
    ag.justificativa = justificativa.trim();
    ag.canceladoEm = agoraIso();
    cancelado = true;
    sincronizarOcupacaoMock();
  }
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: 'Cancelamento da fila de marcação',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: `Motivo: ${justificativa.trim()}.`,
  });
  registrar('Cancelamento da fila', autor, 'NEGOCIO_CLINICO',
    `${solicitacao.protocolo}: ${justificativa.trim()}.`);
  return { solicitacaoId: id, status: solicitacao.status, agendamentoCancelado: cancelado };
}

export async function reagendarDaFila(
  id: string,
  slotId: string,
  justificativa: string,
  autor: string,
): Promise<Solicitacao> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Solicitacao>(`/api/solicitacoes/${id}/reagendar`, {
      slotId, justificativa, autor,
    });
    return data;
  }
  await pausa();
  const solicitacao = mockDb.solicitacoes.find((item) => item.id === id);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  if (solicitacao.status !== 'AGENDADA') {
    throw new Error('Somente solicitações agendadas podem ser reagendadas.');
  }
  const slot = slotsAgendaMock.find((item) => item.id === slotId);
  if (!slot) throw new Error('Vaga não encontrada.');
  const chave = chavePacienteMock(solicitacao.prontuario);
  if (agendamentosMock.some((item) =>
    (item.status === 'ATIVO' || item.status === 'PROPOSTO') && item.pacienteChave === chave && item.slotId === slotId)) {
    throw new Error('Já existe agendamento ativo para este paciente neste horário.');
  }
  const ag = agendamentosMock.find((item) =>
    item.solicitacaoId === solicitacao.id && item.status === 'ATIVO');
  if (!ag) throw new Error('Nenhum agendamento ativo encontrado.');
  const slotAnterior = ag.slotId;
  ag.slotId = slotId;
  ag.justificativa = justificativa.trim();
  ag.confirmadoPor = autor;
  if (solicitacao.agendamento) {
    solicitacao.agendamento.dataHora = slot.inicio;
    solicitacao.agendamento.unidade = slot.unidade;
    solicitacao.agendamento.confirmadoPor = autor;
  }
  sincronizarOcupacaoMock();
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: 'Reagendamento da fila de marcação',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: `De ${slotAnterior} para ${slot.inicio}. Motivo: ${justificativa.trim()}.`,
  });
  registrar('Reagendamento da fila', autor, 'NEGOCIO_CLINICO',
    `${solicitacao.protocolo}: reagendado para ${slot.inicio}.`);
  return clonar(solicitacao);
}

export async function listarIndicadores(filtros: FiltroIndicadores): Promise<Indicadores> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<Indicadores>('/api/painel/indicadores', { params: filtros });
    return data;
  }
  await pausa();
  const base = filaCompleta({ ...FILTROS_TODOS, tipoExame: filtros.tipoExame, periodo: filtros.periodo });
  const pendentes = base.filter((item) => !['AGENDADA', 'CANCELADA'].includes(item.status)).length;
  const agendados = base.filter((item) => item.status === 'AGENDADA').length;
  const comAlerta = base.filter((item) => item.alertas.length > 0 || item.divergencias.length > 0).length;
  const porTipoMap = new Map<string, number>();
  const porPrioridadeMap = new Map<string, number>();
  const porUnidadeMap = new Map<string, number>();
  const porDiaMap = new Map<string, number>();
  const horas: number[] = [];
  base.forEach((item) => {
    porTipoMap.set(item.tipoExame, (porTipoMap.get(item.tipoExame) ?? 0) + 1);
    porPrioridadeMap.set(item.prioridade, (porPrioridadeMap.get(item.prioridade) ?? 0) + 1);
    porUnidadeMap.set(item.setorSolicitante, (porUnidadeMap.get(item.setorSolicitante) ?? 0) + 1);
    const dia = item.recebidaEm.slice(0, 10);
    porDiaMap.set(dia, (porDiaMap.get(dia) ?? 0) + 1);
    horas.push(horasDesdeReferencia(item.recebidaEm));
  });
  const mediaHoras = horas.length ? Math.round(horas.reduce((soma, valor) => soma + valor, 0) / horas.length) : 0;
  const fator = filtros.periodo === 'todos' ? 4 : Math.max(1, Number(filtros.periodo) / 24);
  const etapas = ['Validação com AGHUX', 'Contato com paciente', 'Validação automática'];
  const gargalos = Array.from(porUnidadeMap, ([unidade, quantidade], indice) => ({
    etapa: etapas[indice] ?? 'Fila de espera',
    unidadeSolicitante: unidade,
    horas: Math.round((9 - indice * 2) * fator),
    quantidade,
  })).slice(0, 3);
  const evolucao = Array.from(porDiaMap.keys()).sort().slice(-7).map((dia) => ({
    rotulo: `${dia.slice(8, 10)}/${dia.slice(5, 7)}`,
    valor: porDiaMap.get(dia) ?? 0,
  }));
  return {
    pendentes,
    tempoMedioValidacao: Math.round((mediaHoras / 24) * 10) / 10,
    agendados,
    taxaErro: base.length ? Math.round((comAlerta / base.length) * 1000) / 10 : 0,
    tempoMedioAgendamento: Math.round((mediaHoras / 24) * 1.3 * 10) / 10,
    gargalos,
    porTipo: Array.from(porTipoMap, ([rotulo, valor]) => ({ rotulo, valor })),
    porPrioridade: Array.from(porPrioridadeMap, ([rotulo, valor]) => ({ rotulo, valor })),
    evolucao,
  };
}

export async function listarRelatorios(): Promise<Relatorio[]> {
  return [
    { id: 'volume-por-exame', nome: 'Volume por exame (AGHUX)', descricao: 'Quantidade de solicitações por código e nome do exame no período.' },
    { id: 'tempo-espera', nome: 'Tempo de espera por prioridade', descricao: 'Horas decorridas desde a solicitação no AGHUX, agrupadas por prioridade.' },
    { id: 'divergencias', nome: 'Divergências com AGHUX', descricao: 'Campos divergentes por solicitação e situação de tratamento.' },
    { id: 'produtividade', nome: 'Produtividade da equipe', descricao: 'Validações e agendamentos por operador.' },
  ];
}

export async function obterRelatorio(id: string, filtros: FiltroIndicadores): Promise<ResultadoRelatorio> {
  const base = filaCompleta({ ...FILTROS_TODOS, tipoExame: filtros.tipoExame, periodo: filtros.periodo });
  if (id === 'volume-por-exame') {
    const mapa = new Map<string, { quantidade: number; nome: string }>();
    base.forEach((item) => {
      item.itensExame.forEach((exame) => {
        const atual = mapa.get(exame.codigoExame) ?? { quantidade: 0, nome: exame.nomeExame };
        atual.quantidade += 1;
        mapa.set(exame.codigoExame, atual);
      });
    });
    return {
      colunas: ['Código', 'Exame', 'Itens solicitados'],
      linhas: Array.from(mapa, ([codigo, valor], indice) => ({
        id: indice + 1,
        Código: codigo,
        Exame: valor.nome,
        'Itens solicitados': valor.quantidade,
      })).sort((a, b) => Number(b['Itens solicitados']) - Number(a['Itens solicitados'])),
    };
  }
  if (id === 'tempo-espera') {
    return {
      colunas: ['Solicitação', 'Prontuário', 'Prioridade', 'Horas na fila'],
      linhas: base.map((item, indice) => ({
        id: indice + 1,
        Solicitação: item.protocolo,
        Prontuário: item.prontuario,
        Prioridade: item.prioridade,
        'Horas na fila': horasDesdeReferencia(item.recebidaEm),
      })),
    };
  }
  if (id === 'divergencias') {
    return {
      colunas: ['Solicitação', 'Campo', 'Valor formulário', 'Valor AGHUX', 'Tratada'],
      linhas: base.flatMap((item, indice) =>
        item.divergencias.map((divergencia, offset) => ({
          id: indice * 10 + offset + 1,
          Solicitação: item.protocolo,
          Campo: divergencia.campo,
          'Valor formulário': divergencia.valorFormulario,
          'Valor AGHUX': divergencia.valorAghux,
          Tratada: divergencia.tratada ? 'Sim' : 'Não',
        })),
      ),
    };
  }
  if (id === 'produtividade') {
    const mapa = new Map<string, { validacoes: number; agendamentos: number }>();
    base.forEach((item) => {
      const autor = item.historico.find((evento) => evento.acao.includes('validados'))?.autor ?? 'Não atribuído';
      const atual = mapa.get(autor) ?? { validacoes: 0, agendamentos: 0 };
      atual.validacoes += item.historico.filter((evento) => evento.acao.includes('validados')).length;
      atual.agendamentos += item.status === 'AGENDADA' ? 1 : 0;
      mapa.set(autor, atual);
    });
    return {
      colunas: ['Operador', 'Validações', 'Agendamentos'],
      linhas: Array.from(mapa, ([operador, valores], indice) => ({
        id: indice + 1,
        Operador: operador,
        Validações: valores.validacoes,
        Agendamentos: valores.agendamentos,
      })),
    };
  }
  throw new Error('Relatório não encontrado.');
}

export interface ResultadoCriterios {
  criterios: CriterioPriorizacao[];
  versoes: VersaoCriterios[];
}

export async function listarCriterios(): Promise<ResultadoCriterios> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<ResultadoCriterios>('/api/criterios-priorizacao');
    return data;
  }
  await pausa();
  return { criterios: clonar(mockDb.criterios), versoes: clonar(mockDb.versoes) };
}

export async function salvarVersaoCriterios(
  criterios: CriterioPriorizacao[],
  justificativa: string,
  autor: string,
): Promise<ResultadoCriterios> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<ResultadoCriterios>('/api/criterios-priorizacao/versoes', {
      criterios,
      justificativa,
      autor,
    });
    return data;
  }
  await pausa();
  if (!justificativa.trim()) throw new Error('A justificativa é obrigatória para salvar uma nova versão.');
  if (!criterios.some((criterio) => criterio.ativo)) throw new Error('Ao menos um critério precisa estar ativo.');
  const novaVersao: VersaoCriterios = {
    numero: mockDb.versoes.length + 1,
    criadoEm: agoraIso(),
    autor,
    justificativa: justificativa.trim(),
    criterios: clonar(criterios),
  };
  mockDb.versoes.unshift(novaVersao);
  mockDb.criterios = clonar(criterios);
  registrar('Nova versão dos critérios de priorização', autor, 'CONFIGURACAO', `Versão ${novaVersao.numero}: ${justificativa.trim()}`);
  return { criterios: clonar(mockDb.criterios), versoes: clonar(mockDb.versoes) };
}

export async function listarEquipe(): Promise<UsuarioEquipe[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<UsuarioEquipe[]>('/api/admin/equipe');
    return data;
  }
  await pausa();
  return clonar(mockDb.equipe);
}

export async function consultarAd(username: string): Promise<AdUser> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<AdUser>(`/api/admin/ad-user-search/${encodeURIComponent(username)}`);
    return data;
  }
  await pausa();
  return consultarAdMock(username);
}

export type DadosUsuario = Pick<UsuarioEquipe, 'login' | 'nome' | 'email' | 'lotacao' | 'perfil'>;

export async function salvarUsuarioEquipe(dados: DadosUsuario, autor: string): Promise<UsuarioEquipe[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<UsuarioEquipe[]>('/api/admin/equipe', dados);
    return data;
  }
  await pausa();
  if (!dados.login.trim() || !dados.nome.trim()) throw new Error('Informe o login e o nome do usuário.');
  if (mockDb.equipe.some((usuario) => usuario.login.toLowerCase() === dados.login.toLowerCase())) {
    throw new Error('Este login já está cadastrado na equipe.');
  }
  mockDb.equipe.unshift({
    ...dados,
    id: `usr-${crypto.randomUUID()}`,
    ativo: true,
    criadoEm: agoraIso(),
  });
  registrar('Usuário cadastrado na equipe', autor, 'SEGURANCA', `${dados.login} com perfil ${dados.perfil}.`);
  return clonar(mockDb.equipe);
}

export async function alternarSituacaoEquipe(id: string, autor: string): Promise<UsuarioEquipe[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.patch<UsuarioEquipe[]>(`/api/admin/equipe/${id}`, {});
    return data;
  }
  await pausa();
  const usuario = mockDb.equipe.find((item) => item.id === id);
  if (!usuario) throw new Error('Usuário não encontrado.');
  usuario.ativo = !usuario.ativo;
  registrar(usuario.ativo ? 'Usuário ativado' : 'Usuário inativado', autor, 'SEGURANCA', `Login ${usuario.login}.`);
  return clonar(mockDb.equipe);
}

export async function listarAuditoria(): Promise<EventoHistorico[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<EventoHistorico[]>('/api/auditoria');
    return data;
  }
  await pausa();
  return clonar(mockDb.auditoria);
}

/** Eventos determinísticos do adaptador mock da integração Forms → AGHUX. */
const eventosFormsMock: FormsEvento[] = [
  {
    responseId: 'resp-forms-1001',
    formId: 'form-solicitacao-exames',
    status: 'PROCESSADA',
    tentativas: 1,
    ultimoErro: null,
    recebidoEm: '2026-11-25T14:05:34.227',
    processadoEm: '2026-11-25T14:06:12.227',
    solicitacaoId: 'SOL-2026-000123',
    divergencias: 1,
    alertas: 0,
  },
  {
    responseId: 'resp-forms-1002',
    formId: 'form-solicitacao-exames',
    status: 'ERRO',
    tentativas: 2,
    ultimoErro: 'AGHUX indisponível no cruzamento do prontuário.',
    recebidoEm: '2026-11-25T14:12:08.227',
    processadoEm: null,
    solicitacaoId: null,
    divergencias: 0,
    alertas: 1,
  },
  {
    responseId: 'resp-forms-1003',
    formId: 'form-solicitacao-exames',
    status: 'DUPLICADA',
    tentativas: 1,
    ultimoErro: null,
    recebidoEm: '2026-11-25T14:18:41.227',
    processadoEm: '2026-11-25T14:18:55.227',
    solicitacaoId: 'SOL-2026-000123',
    divergencias: 0,
    alertas: 1,
  },
];

/** Lista os eventos recentes recebidos do Microsoft Forms (GET /api/integracoes/forms/eventos). */
export async function listarEventosIntegracao(limit = 50): Promise<FormsEvento[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<FormsEvento[]>('/api/integracoes/forms/eventos', { params: { limit } });
    return data;
  }
  await pausa();
  return clonar(eventosFormsMock.slice(0, Math.max(0, limit)));
}

/** Reprocessa um evento Forms e devolve o registro atualizado (POST .../reprocessar). */
export async function reprocessarEventoIntegracao(responseId: string): Promise<FormsEvento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<FormsEvento>(
      `/api/integracoes/forms/eventos/${encodeURIComponent(responseId)}/reprocessar`,
    );
    return data;
  }
  await pausa();
  const evento = eventosFormsMock.find((item) => item.responseId === responseId);
  if (!evento) throw new Error('Evento de integração não encontrado.');
  evento.tentativas += 1;
  evento.ultimoErro = null;
  // O reprocessamento reagenda a tentativa e, quando bem-sucedido, conclui a importação.
  if (evento.status === 'ERRO' && evento.tentativas === 3) {
    evento.status = 'PENDENTE';
    evento.processadoEm = null;
  } else {
    evento.status = 'PROCESSADA';
    evento.processadoEm = somarHoras(evento.recebidoEm, 1);
    evento.solicitacaoId = evento.solicitacaoId ?? `SOL-2026-${String(124 + evento.tentativas).padStart(6, '0')}`;
  }
  registrar('Reprocessamento de evento Forms', 'Área Gestora', 'NEGOCIO_CLINICO', `${responseId} reprocessado: ${evento.status}.`);
  return clonar(evento);
}

/* -------------------------------------------------------------------------- */
/* Agendamentos, calendário, propostas e gestão de vagas (v0.7.0)           */
/* -------------------------------------------------------------------------- */

export interface FiltrosCalendarioAgendamentos {
  de: string;
  ate: string;
  unidade?: string;
  codigoExame?: string;
  pacienteChave?: string;
}

export interface DadosNovoSlot {
  unidade: string;
  codigoExame: string;
  nomeExame: string;
  inicio: string;
  fim: string;
  capacidade: number;
  situacao?: AgendaSlot['status'];
}

export interface CopiaSemanaPayload {
  origem: string;
  destino: string;
  codigoExame?: string;
}

export interface ResultadoCopiaSemana {
  origem: string;
  destino: string;
  codigoExame: string;
  criadas: AgendaSlot[];
  ignoradas: number;
  total: number;
}

export interface AjusteSlot {
  unidade?: string;
  codigoExame?: string;
  nomeExame?: string;
  inicio?: string;
  fim?: string;
  capacidade?: number;
  status?: AgendaSlot['status'];
}

/**
 * Pares reais (unidade solicitante, exame) derivados do export AGHUX.
 * Antes cada unidade mock oferecia todos os exames, o que gerava vagas
 * irreais e permitia propostas em unidades incompatíveis.
 */
const paresAgendaMock = Array.from(
  new Map(
    mockDb.solicitacoes.flatMap((item) => item.itensExame
      .filter((exame) => exame.codigoExame && item.setorSolicitante)
      .map((exame) => [
        `${item.setorSolicitante}|${exame.codigoExame}`,
        {
          unidade: item.setorSolicitante,
          codigoExame: exame.codigoExame,
          nomeExame: exame.nomeExame,
        },
      ] as const)),
  ).values(),
).sort((a, b) => a.unidade.localeCompare(b.unidade)
  || a.codigoExame.localeCompare(b.codigoExame));

const TURNOS_AGENDA = [[8, 10], [10, 12], [13, 15], [15, 17]] as const;

function gerarSlotsDeterministicos(): AgendaSlot[] {
  const referencia = new Date(`${REFERENCIA_EM.slice(0, 10)}T12:00:00`).getTime();
  const slots: AgendaSlot[] = [];
  for (let offset = 0; offset < 30; offset += 1) {
    const data = new Date(referencia + offset * 86_400_000);
    const diaSemana = data.getDay();
    if (diaSemana === 0 || diaSemana === 6) continue;
    const dia = paraIsoLocal(data.getTime()).slice(0, 10);
    paresAgendaMock.forEach((par, indicePar) => {
      TURNOS_AGENDA.forEach(([horaInicio, horaFim], indiceTurno) => {
        const capacidade = 3 + ((offset + indicePar + indiceTurno) % 3);
        const dois = (valor: number): string => String(valor).padStart(2, '0');
        slots.push({
          id: `slot-${dia.replace(/-/g, '')}-${indicePar}-${indiceTurno}`,
          unidade: par.unidade,
          codigoExame: par.codigoExame,
          nomeExame: par.nomeExame,
          inicio: `${dia}T${dois(horaInicio)}:00:00.000`,
          fim: `${dia}T${dois(horaFim)}:00:00.000`,
          capacidade,
          ocupadas: 0,
          livres: capacidade,
          status: 'DISPONIVEL',
        });
      });
    });
  }
  return slots.sort((a, b) => a.inicio.localeCompare(b.inicio) || a.unidade.localeCompare(b.unidade));
}

const slotsAgendaMock: AgendaSlot[] = gerarSlotsDeterministicos();
const agendamentosMock: Agendamento[] = [];
/** Vagas fechadas manualmente pela chefia não são reabertas pela sincronização. */
const slotsFechadosManualmenteMock = new Set<string>();

/** Ocupação sempre reflete ativos e propostas, independente do filtro do paciente. */
function sincronizarOcupacaoMock(): void {
  slotsAgendaMock.forEach((slot) => {
    const ocupadas = agendamentosMock.filter((item) =>
      item.slotId === slot.id && (item.status === 'ATIVO' || item.status === 'PROPOSTO')).length;
    slot.ocupadas = ocupadas;
    slot.livres = Math.max(0, slot.capacidade - ocupadas);
    if (slot.status !== 'ENCERRADO' && !slotsFechadosManualmenteMock.has(slot.id)) {
      slot.status = slot.livres === 0 ? 'LOTADO' : 'DISPONIVEL';
    }
  });
}

/** Propostas pendentes no formato da fila, ordenadas por prioridade e espera. */
function filaPropostasMock(): PropostaAgendamentoFila[] {
  return agendamentosMock
    .filter((agendamento) => agendamento.status === 'PROPOSTO')
    .flatMap((agendamento) => {
      const solicitacao = mockDb.solicitacoes.find((item) => item.id === agendamento.solicitacaoId);
      if (!solicitacao) return [];
      return [{
        agendamentoId: agendamento.id,
        solicitacaoId: solicitacao.id,
        protocolo: agendamento.protocolo,
        pacienteNome: agendamento.pacienteNome,
        prontuario: agendamento.prontuario,
        prioridade: classificarPrioridade(calcularPontuacao(solicitacao.atributos, mockDb.criterios)),
        pontuacao: calcularPontuacao(solicitacao.atributos, mockDb.criterios),
        unidadeSolicitante: solicitacao.setorSolicitante,
        exames: solicitacao.itensExame.map((item) => item.nomeExame).filter(Boolean).join(', ')
          || solicitacao.exame,
        status: 'PROPOSTO' as const,
        statusSolicitacao: solicitacao.status,
        dataHora: agendamento.dataHora,
        unidade: agendamento.unidade,
        nomeExame: agendamento.exame,
        recebidaEm: solicitacao.recebidaEm,
        tempoNaFilaHoras: horasDesdeReferencia(solicitacao.recebidaEm),
      }];
    })
    .sort((a, b) => b.pontuacao - a.pontuacao
      || new Date(a.recebidaEm).getTime() - new Date(b.recebidaEm).getTime()
      || a.protocolo.localeCompare(b.protocolo));
}

function chavePacienteMock(prontuario: string): string {
  return `PAC-${prontuario}`;
}

function encontrarSolicitacaoMock(id: string): Solicitacao | undefined {
  return mockDb.solicitacoes.find((item) =>
    item.id === id || item.protocolo === id || item.codigoSolicitacaoAghux === id);
}

function normalizarIsoMock(valor: string): string {
  return valor.length === 16 ? `${valor}:00.000` : valor;
}

function limitesConsultaMock(de: string, ate: string): { inicio: string; fim: string } {
  const inicio = de.length === 10 ? `${de}T00:00:00.000` : de;
  const fim = ate.length === 10 ? `${ate}T23:59:59.999` : ate;
  return { inicio, fim };
}

function validarSlotMock(slot: AgendaSlot, pacienteChave?: string, ignorarId?: string): void {
  if (slot.status === 'ENCERRADO') throw new Error('Esta vaga foi encerrada pela gestão.');
  if (slot.livres <= 0) throw new Error('Vaga esgotada para o horário selecionado.');
  if (pacienteChave && agendamentosMock.some((item) =>
    (item.status === 'ATIVO' || item.status === 'PROPOSTO') && item.id !== ignorarId
    && item.pacienteChave === pacienteChave && item.slotId === slot.id)) {
    throw new Error('O paciente já possui agendamento ativo neste horário.');
  }
}

/** GET /api/agendamentos/calendario */
export async function listarCalendarioAgendamentos(
  filtros: FiltrosCalendarioAgendamentos,
): Promise<CalendarioAgendamentos> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<CalendarioAgendamentos>('/api/agendamentos/calendario', {
      params: {
        de: filtros.de,
        ate: filtros.ate,
        unidade: filtros.unidade ?? '',
        codigoExame: filtros.codigoExame ?? '',
        pacienteChave: filtros.pacienteChave ?? '',
      },
    });
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const { inicio, fim } = limitesConsultaMock(filtros.de, filtros.ate);
  const slots = slotsAgendaMock.filter((slot) =>
    slot.inicio >= inicio && slot.inicio < fim
    && (!filtros.unidade || slot.unidade === filtros.unidade)
    && (!filtros.codigoExame || slot.codigoExame === filtros.codigoExame));
  const slotsPorId = new Map(slotsAgendaMock.map((slot) => [slot.id, slot]));
  const agendamentos = agendamentosMock.filter((agendamento) =>
    agendamento.dataHora >= inicio && agendamento.dataHora < fim
    && (!filtros.unidade || agendamento.unidade === filtros.unidade)
    && (!filtros.codigoExame || slotsPorId.get(agendamento.slotId)?.codigoExame === filtros.codigoExame)
    && (!filtros.pacienteChave || agendamento.pacienteChave === filtros.pacienteChave));
  return { de: filtros.de, ate: filtros.ate, slots: clonar(slots), agendamentos: clonar(agendamentos) };
}

/** GET /api/agendamentos/pacientes/buscar?q= */
export async function buscarPacientesAgendamento(q: string): Promise<PacienteAgendamentos[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<PacienteAgendamentos[]>('/api/agendamentos/pacientes/buscar', {
      params: { q },
    });
    return data;
  }
  await pausa();
  const pacientes = new Map<string, PacienteAgendamentos>();
  const protocolosPorProntuario = new Map<string, string[]>();
  mockDb.solicitacoes.forEach((solicitacao) => {
    const chave = chavePacienteMock(solicitacao.prontuario);
    if (!pacientes.has(chave)) {
      pacientes.set(chave, {
        pacienteChave: chave,
        pacienteNome: solicitacao.pacienteNome,
        prontuario: solicitacao.prontuario,
        agendamentosAtivos: 0,
      });
    }
    const protocolos = protocolosPorProntuario.get(solicitacao.prontuario) ?? [];
    protocolos.push(solicitacao.protocolo);
    protocolosPorProntuario.set(solicitacao.prontuario, protocolos);
  });
  agendamentosMock.filter((item) => item.status === 'ATIVO').forEach((agendamento) => {
    const paciente = pacientes.get(agendamento.pacienteChave) ?? {
      pacienteChave: agendamento.pacienteChave,
      pacienteNome: agendamento.pacienteNome,
      prontuario: agendamento.prontuario,
      agendamentosAtivos: 0,
    };
    paciente.agendamentosAtivos += 1;
    pacientes.set(paciente.pacienteChave, paciente);
  });
  const termo = q.trim().toLowerCase();
  return Array.from(pacientes.values())
    .filter((paciente) => !termo || [
      paciente.pacienteNome,
      paciente.prontuario,
      ...(protocolosPorProntuario.get(paciente.prontuario) ?? []),
    ].join(' ').toLowerCase().includes(termo))
    .sort((a, b) => a.pacienteNome.localeCompare(b.pacienteNome))
    .slice(0, 20);
}

/** GET /api/agendamentos/paciente/{pacienteChave} */
export async function listarAgendamentosPaciente(pacienteChave: string): Promise<Agendamento[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<Agendamento[]>(
      `/api/agendamentos/paciente/${encodeURIComponent(pacienteChave)}`,
    );
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  return clonar(agendamentosMock
    .filter((item) => item.pacienteChave === pacienteChave || item.prontuario === pacienteChave)
    .sort((a, b) => b.dataHora.localeCompare(a.dataHora)));
}

/** GET /api/agendamentos/sugestoes/{solicitacaoId}?limite=3 */
export async function listarSugestoesAgendamento(
  solicitacaoId: string,
  limite = 3,
): Promise<SugestaoAgendamento[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<SugestaoAgendamento[]>(
      `/api/agendamentos/sugestoes/${encodeURIComponent(solicitacaoId)}`,
      { params: { limite } },
    );
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const solicitacao = encontrarSolicitacaoMock(solicitacaoId);
  const codigoDesejado = solicitacao?.itensExame[0]?.codigoExame ?? '';
  const hoje = agoraIso().slice(0, 10);
  const elegiveis = slotsAgendaMock.filter((slot) =>
    slot.status !== 'ENCERRADO' && slot.livres > 0 && slot.inicio.slice(0, 10) >= hoje);
  // O código do exame da solicitação é filtro duro: não se sugere outro exame.
  const candidatos = (codigoDesejado
    ? elegiveis.filter((slot) => slot.codigoExame === codigoDesejado)
    : elegiveis)
    .map((slot) => {
      const dias = Math.max(0, Math.round((new Date(slot.inicio.slice(0, 10)).getTime()
        - new Date(hoje).getTime()) / 86_400_000));
      const pontuacao = Math.min(99, Math.max(1, 92 - dias * 3 + slot.livres * 2));
      const motivos = [
        codigoDesejado
          ? `Exame ${codigoDesejado} compatível com a solicitação`
          : 'Vaga disponível para a solicitação',
        `${slot.livres} vaga(s) livre(s) no horário`,
        dias === 0 ? 'Horário disponível ainda hoje' : `Disponível em ${dias} dia(s)`,
        'Distância estimada em 12,5 km (simulação, sem endereço do paciente)',
      ];
      const sugestao: SugestaoAgendamento = {
        slot: clonar(slot), pontuacao, motivos, distanciaKm: 12.5, distanciaOrigem: 'MOCK',
      };
      return sugestao;
    })
    .sort((a, b) => b.pontuacao - a.pontuacao || a.slot.inicio.localeCompare(b.slot.inicio));
  return candidatos.slice(0, Math.max(1, Math.min(limite, 10)));
}

/** POST /api/agendamentos */
export async function agendarExame(
  solicitacaoId: string,
  slotId: string,
  autor: string,
): Promise<Agendamento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Agendamento>('/api/agendamentos', { solicitacaoId, slotId, autor });
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const solicitacao = encontrarSolicitacaoMock(solicitacaoId);
  if (!solicitacao) throw new Error('Solicitação não encontrada.');
  if (solicitacao.status === 'CANCELADA') throw new Error('Não é possível agendar uma solicitação cancelada.');
  if (![
    'AGUARDANDO_CONTATO', 'AGUARDANDO_CONFIRMACAO', 'AGUARDANDO_REAGENDAMENTO',
  ].includes(solicitacao.status)) {
    throw new Error('A solicitação precisa estar aguardando contato, confirmação ou reagendamento.');
  }
  if (!solicitacao.contatos.some((contato) => contato.resultado === 'ACEITE')) {
    throw new Error('Registre o aceite do paciente antes de agendar.');
  }
  const slot = slotsAgendaMock.find((item) => item.id === slotId);
  if (!slot) throw new Error('Vaga não encontrada.');
  if (agendamentosMock.some((item) =>
    (item.status === 'ATIVO' || item.status === 'PROPOSTO') && item.solicitacaoId === solicitacao.id)) {
    throw new Error('Esta solicitação já possui agendamento ativo.');
  }
  validarSlotMock(slot, chavePacienteMock(solicitacao.prontuario));
  const agendamento: Agendamento = {
    id: `ag-${crypto.randomUUID()}`,
    solicitacaoId: solicitacao.id,
    protocolo: solicitacao.protocolo,
    pacienteChave: chavePacienteMock(solicitacao.prontuario),
    pacienteNome: solicitacao.pacienteNome,
    prontuario: solicitacao.prontuario,
    unidade: slot.unidade,
    exame: slot.nomeExame,
    slotId: slot.id,
    dataHora: slot.inicio,
    status: 'ATIVO',
    confirmadoPor: autor,
    criadoEm: agoraIso(),
    justificativa: null,
  };
  agendamentosMock.push(agendamento);
  solicitacao.status = 'AGENDADA';
  solicitacao.agendamento = {
    dataHora: slot.inicio,
    unidade: slot.unidade,
    confirmadoPor: autor,
    criadoEm: agoraIso(),
  };
  solicitacao.historico.push({
    id: `hist-${crypto.randomUUID()}`,
    em: agoraIso(),
    acao: 'Agendamento efetivado na agenda',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: `${solicitacao.protocolo} — ${slot.unidade} em ${slot.inicio}.`,
  });
  registrar('Agendamento criado', autor, 'NEGOCIO_CLINICO', `${solicitacao.protocolo} em ${slot.inicio}.`);
  sincronizarOcupacaoMock();
  return clonar(agendamento);
}

/** POST /api/agendamentos/{id}/remarcar */
export async function remarcarAgendamento(
  id: string,
  slotId: string,
  justificativa: string,
  autor: string,
): Promise<Agendamento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Agendamento>(`/api/agendamentos/${encodeURIComponent(id)}/remarcar`, {
      slotId, justificativa, autor,
    });
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const agendamento = agendamentosMock.find((item) => item.id === id);
  if (!agendamento) throw new Error('Agendamento não encontrado.');
  if (agendamento.status !== 'ATIVO' && agendamento.status !== 'PROPOSTO') {
    throw new Error('Somente agendamentos ativos ou propostos podem ser remarcados.');
  }
  if (!justificativa.trim()) throw new Error('A justificativa é obrigatória para remarcar.');
  const slot = slotsAgendaMock.find((item) => item.id === slotId);
  if (!slot) throw new Error('Vaga não encontrada.');
  validarSlotMock(slot, agendamento.pacienteChave, agendamento.id);
  const anterior = agendamento.dataHora;
  agendamento.slotId = slot.id;
  agendamento.dataHora = slot.inicio;
  agendamento.unidade = slot.unidade;
  agendamento.exame = slot.nomeExame;
  agendamento.justificativa = justificativa.trim();
  agendamento.confirmadoPor = autor;
  const solicitacao = encontrarSolicitacaoMock(agendamento.solicitacaoId);
  if (solicitacao?.agendamento) solicitacao.agendamento.dataHora = slot.inicio;
  registrar('Agendamento remarcado', autor, 'NEGOCIO_CLINICO',
    `${agendamento.protocolo}: ${anterior} → ${slot.inicio}. Justificativa: ${justificativa.trim()}`);
  sincronizarOcupacaoMock();
  return clonar(agendamento);
}

/** POST /api/agendamentos/{id}/cancelar */
export async function cancelarAgendamento(
  id: string,
  justificativa: string,
  autor: string,
): Promise<Agendamento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Agendamento>(`/api/agendamentos/${encodeURIComponent(id)}/cancelar`, {
      justificativa, autor,
    });
    return data;
  }
  await pausa();
  const agendamento = agendamentosMock.find((item) => item.id === id);
  if (!agendamento) throw new Error('Agendamento não encontrado.');
  if (agendamento.status !== 'ATIVO' && agendamento.status !== 'PROPOSTO') {
    throw new Error('Somente agendamentos ativos ou propostos podem ser cancelados.');
  }
  if (!justificativa.trim()) throw new Error('A justificativa é obrigatória para cancelar.');
  const eraProposta = agendamento.status === 'PROPOSTO';
  agendamento.status = 'CANCELADO';
  agendamento.justificativa = justificativa.trim();
  agendamento.confirmadoPor = autor;
  const solicitacao = encontrarSolicitacaoMock(agendamento.solicitacaoId);
  if (solicitacao) {
    solicitacao.status = eraProposta ? 'AGUARDANDO_REAGENDAMENTO' : 'CANCELADA';
    solicitacao.agendamento = null;
  }
  registrar('Agendamento cancelado', autor, 'NEGOCIO_CLINICO',
    `${agendamento.protocolo}: ${agendamento.dataHora}. Justificativa: ${justificativa.trim()}`);
  sincronizarOcupacaoMock();
  return clonar(agendamento);
}

export interface ResultadoSimulacaoAgenda {
  geradas: number;
  solicitacoes: number;
  dias: number;
  /** Quantidade de exames/solicitações que não encontraram vaga disponível. */
  deFora: number;
  /** Solicitações filtradas sem contato de ACEITE registrado. */
  semAceite?: number;
  /** Solicitações filtradas com divergência ainda não tratada. */
  comDivergencia?: number;
  /** Solicitações que já possuem agendamento ATIVO ou proposta PROPOSTO. */
  jaReservadas?: number;
  /** Linhas da fila de propostas, já ordenadas por prioridade. */
  propostas: PropostaAgendamentoFila[];
}

/** GET /api/agendamentos/propostas */
export async function listarPropostasAgendamento(
  filtros: FiltrosSimulacao = {},
): Promise<PropostaAgendamentoFila[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<PropostaAgendamentoFila[]>(
      '/api/agendamentos/propostas', { params: { ...filtros } },
    );
    return data;
  }
  await pausa();
  const unidadeFiltro = (filtros.unidade || '').trim().toLowerCase();
  const codigoExameFiltro = (filtros.codigoExame || '').trim().toUpperCase();
  const pacienteChaveFiltro = (filtros.pacienteChave || '').trim();

  return filaPropostasMock().filter((proposta) => {
    if (unidadeFiltro && (proposta.unidade || '').trim().toLowerCase() !== unidadeFiltro) {
      return false;
    }
    if (pacienteChaveFiltro && chavePacienteMock(proposta.prontuario) !== pacienteChaveFiltro) {
      return false;
    }
    if (codigoExameFiltro) {
      const exameNome = (proposta.nomeExame || '').trim().toUpperCase();
      const exames = (proposta.exames || '').toUpperCase();
      if (!exameNome.includes(codigoExameFiltro) && !exames.includes(codigoExameFiltro)) {
        return false;
      }
    }
    return true;
  });
}

/**
 * POST /api/agendamentos/propostas/gerar (simulação local)
 * Pré-aloca solicitações com aceite nas vagas dos próximos dias. A ocupação
 * gerada na própria simulação é contabilizada a cada proposta — inclusive o
 * bloqueio de outro horário do mesmo paciente — antes de escolher a vaga
 * seguinte. As propostas só viram ATIVOS após confirmação do operador.
 * A simulação respeita os filtros ativos (unidade, código de exame e
 * paciente/prontuário); nunca simula todas as solicitações de uma vez.
 */
export interface FiltrosSimulacao {
  unidade?: string;
  codigoExame?: string;
  pacienteChave?: string;
}

export async function gerarPropostasAgendamento(
  dias = 30,
  autor = 'Sistema',
  filtros: FiltrosSimulacao = {},
): Promise<ResultadoSimulacaoAgenda> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<ResultadoSimulacaoAgenda>(
      '/api/agendamentos/propostas/gerar', { dias, autor, ...filtros },
    );
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const inicio = agoraIso();
  const limite = somarHoras(inicio, Math.max(1, dias) * 24).slice(0, 10);
  const unidadeFiltro = (filtros.unidade || '').trim().toLowerCase();
  const codigoExameFiltro = (filtros.codigoExame || '').trim().toUpperCase();
  const pacienteChaveFiltro = (filtros.pacienteChave || '').trim();

  const base = mockDb.solicitacoes
    .filter((solicitacao) => [
      'AGUARDANDO_CONTATO', 'AGUARDANDO_CONFIRMACAO', 'AGUARDANDO_REAGENDAMENTO',
    ].includes(solicitacao.status))
    .filter((solicitacao) => {
      if (unidadeFiltro && (solicitacao.setorSolicitante || '').trim().toLowerCase() !== unidadeFiltro) {
        return false;
      }
      if (pacienteChaveFiltro && chavePacienteMock(solicitacao.prontuario) !== pacienteChaveFiltro) {
        return false;
      }
      if (codigoExameFiltro) {
        const codigos = new Set(solicitacao.itensExame
          .map((item) => item.codigoExame.trim().toUpperCase()).filter(Boolean));
        if (!codigos.has(codigoExameFiltro)) return false;
      }
      return true;
    });

  const temAceite = (solicitacao: (typeof base)[number]): boolean =>
    solicitacao.contatos.some((contato) => contato.resultado === 'ACEITE');
  const temDivergencia = (solicitacao: (typeof base)[number]): boolean =>
    solicitacao.divergencias.some((divergencia) => !divergencia.tratada);
  const jaReservada = (solicitacao: (typeof base)[number]): boolean =>
    agendamentosMock.some((agendamento) => agendamento.solicitacaoId === solicitacao.id
      && (agendamento.status === 'ATIVO' || agendamento.status === 'PROPOSTO'));

  const semAceite = base.filter((solicitacao) => !temAceite(solicitacao)).length;
  const comAceite = base.filter((solicitacao) => temAceite(solicitacao));
  const comDivergencia = comAceite.filter((solicitacao) => temDivergencia(solicitacao)).length;
  const semDivergencia = comAceite.filter((solicitacao) => !temDivergencia(solicitacao));
  const jaReservadas = semDivergencia.filter((solicitacao) => jaReservada(solicitacao)).length;
  const elegiveis = semDivergencia
    .filter((solicitacao) => !jaReservada(solicitacao))
    .sort((a, b) => b.pontuacao - a.pontuacao
      || new Date(a.recebidaEm).getTime() - new Date(b.recebidaEm).getTime());

  const ocupacaoAdicional = new Map<string, number>();
  const pacientesNoDia = new Set<string>();
  agendamentosMock
    .filter((agendamento) => agendamento.status === 'ATIVO' || agendamento.status === 'PROPOSTO')
    .forEach((agendamento) => pacientesNoDia.add(
      `${agendamento.pacienteChave}|${agendamento.dataHora.slice(0, 10)}`,
    ));

  let geradas = 0;
  let deFora = 0;
  elegiveis.forEach((solicitacao) => {
    const codigos = new Set(solicitacao.itensExame
      .map((item) => item.codigoExame.trim().toUpperCase()).filter(Boolean));
    const chave = chavePacienteMock(solicitacao.prontuario);
    const unidadeSolicitante = (solicitacao.setorSolicitante || '').trim().toLowerCase();
    const restante = (slot: AgendaSlot): number =>
      slot.livres - (ocupacaoAdicional.get(slot.id) ?? 0);
    // Com filtro de exame ativo, só o exame filtrado é tentado; os demais
    // códigos da mesma solicitação não entram como "sem vaga".
    const examesParaTentar = codigoExameFiltro
      ? [codigoExameFiltro]
      : codigos.size > 0 ? Array.from(codigos) : [null];
    for (const codigo of examesParaTentar) {
      const slot = slotsAgendaMock
        .filter((candidato) => (codigo === null || codigos.has(candidato.codigoExame.trim().toUpperCase()))
          // A vaga pertence à unidade que realiza o exame: não adianta ter o
          // mesmo código em outra unidade.
          && (!unidadeSolicitante
            || (candidato.unidade || '').trim().toLowerCase() === unidadeSolicitante)
          && candidato.inicio >= inicio
          && candidato.inicio.slice(0, 10) <= limite
          && candidato.status !== 'ENCERRADO'
          && !slotsFechadosManualmenteMock.has(candidato.id)
          && restante(candidato) > 0
          && !pacientesNoDia.has(`${chave}|${candidato.inicio.slice(0, 10)}`))
        .sort((a, b) => a.inicio.localeCompare(b.inicio)
          || (restante(b) / Math.max(1, b.capacidade)) - (restante(a) / Math.max(1, a.capacidade))
          || a.id.localeCompare(b.id))
        .find((candidato) => !agendamentosMock.some((agendamento) => {
          if ((agendamento.status !== 'ATIVO' && agendamento.status !== 'PROPOSTO')
            || agendamento.pacienteChave !== chave) return false;
          const fim = slotsAgendaMock.find((item) => item.id === agendamento.slotId)?.fim
            ?? agendamento.dataHora;
          return new Date(candidato.inicio).getTime() < new Date(fim).getTime()
            && new Date(agendamento.dataHora).getTime() < new Date(candidato.fim).getTime();
        }));
      if (!slot) {
        deFora += 1;
        continue;
      }
      // Garante que a vaga ainda tem espaço considerando ocupação existente +
      // reservas já feitas nesta mesma execução da simulação.
      if (slot.livres <= (ocupacaoAdicional.get(slot.id) ?? 0)) {
        deFora += 1;
        continue;
      }
      const proposta: Agendamento = {
        id: `ag-${crypto.randomUUID()}`,
        solicitacaoId: solicitacao.id,
        protocolo: solicitacao.protocolo,
        pacienteChave: chave,
        pacienteNome: solicitacao.pacienteNome,
        prontuario: solicitacao.prontuario,
        unidade: slot.unidade,
        exame: slot.nomeExame,
        slotId: slot.id,
        dataHora: slot.inicio,
        status: 'PROPOSTO',
        confirmadoPor: autor,
        criadoEm: agoraIso(),
        justificativa: null,
      };
      agendamentosMock.push(proposta);
      ocupacaoAdicional.set(slot.id, (ocupacaoAdicional.get(slot.id) ?? 0) + 1);
      pacientesNoDia.add(`${chave}|${slot.inicio.slice(0, 10)}`);
      solicitacao.status = 'AGUARDANDO_CONFIRMACAO';
      solicitacao.historico.push({
        id: `hist-${crypto.randomUUID()}`,
        em: agoraIso(),
        acao: 'Horário proposto pela simulação da agenda',
        autor,
        categoria: 'NEGOCIO_CLINICO',
        detalhes: `${slot.unidade} · ${slot.inicio} · vaga reservada para confirmação.`,
      });
      geradas += 1;
    }
  });

  sincronizarOcupacaoMock();
  registrar('Simulação de agenda', autor, 'NEGOCIO_CLINICO',
    `${geradas} proposta(s) gerada(s) para os próximos ${dias} dias.`);
  return {
    geradas,
    solicitacoes: base.length,
    dias,
    deFora,
    semAceite,
    comDivergencia,
    jaReservadas,
    propostas: filaPropostasMock(),
  };
}

/** POST /api/agendamentos/{id}/confirmar — confirma a proposta em um clique. */
export async function confirmarPropostaAgendamento(
  id: string, autor: string,
): Promise<Agendamento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Agendamento>(
      `/api/agendamentos/${encodeURIComponent(id)}/confirmar`, { autor },
    );
    return data;
  }
  await pausa();
  const agendamento = agendamentosMock.find((item) => item.id === id);
  if (!agendamento) throw new Error('Proposta não encontrada.');
  if (agendamento.status !== 'PROPOSTO') throw new Error('Somente propostas podem ser confirmadas.');
  agendamento.status = 'ATIVO';
  agendamento.confirmadoPor = autor;
  const solicitacao = encontrarSolicitacaoMock(agendamento.solicitacaoId);
  if (solicitacao) {
    solicitacao.status = 'AGENDADA';
    solicitacao.agendamento = {
      dataHora: agendamento.dataHora,
      unidade: agendamento.unidade,
      confirmadoPor: autor,
      criadoEm: agoraIso(),
    };
    solicitacao.historico.push({
      id: `hist-${crypto.randomUUID()}`,
      em: agoraIso(),
      acao: 'Proposta confirmada pelo operador',
      autor,
      categoria: 'NEGOCIO_CLINICO',
      detalhes: `${agendamento.protocolo} confirmado em ${agendamento.dataHora}.`,
    });
  }
  registrar('Proposta de agendamento confirmada', autor, 'NEGOCIO_CLINICO',
    `${agendamento.protocolo} em ${agendamento.dataHora}.`);
  sincronizarOcupacaoMock();
  return clonar(agendamento);
}

/** POST /api/agendamentos/{id}/nao-confirmado — paciente não confirmou. */
export async function registrarNaoConfirmacaoAgendamento(
  id: string, justificativa: string, autor: string,
): Promise<Agendamento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Agendamento>(
      `/api/agendamentos/${encodeURIComponent(id)}/nao-confirmado`,
      { justificativa, autor },
    );
    return data;
  }
  await pausa();
  const agendamento = agendamentosMock.find((item) => item.id === id);
  if (!agendamento) throw new Error('Agendamento não encontrado.');
  if (agendamento.status !== 'PROPOSTO' && agendamento.status !== 'ATIVO') {
    throw new Error('Somente propostas ou agendamentos ativos podem ser marcados como não confirmados.');
  }
  agendamento.status = 'CANCELADO';
  agendamento.justificativa = justificativa.trim() || 'Paciente não confirmou o horário';
  agendamento.confirmadoPor = autor;
  const solicitacao = encontrarSolicitacaoMock(agendamento.solicitacaoId);
  if (solicitacao) {
    solicitacao.status = 'AGUARDANDO_REAGENDAMENTO';
    solicitacao.agendamento = null;
    solicitacao.historico.push({
      id: `hist-${crypto.randomUUID()}`,
      em: agoraIso(),
      acao: 'Paciente não confirmou o horário',
      autor,
      categoria: 'NEGOCIO_CLINICO',
      detalhes: agendamento.justificativa,
    });
  }
  registrar('Não confirmação de agendamento', autor, 'NEGOCIO_CLINICO',
    `${agendamento.protocolo}: ${agendamento.justificativa}.`);
  sincronizarOcupacaoMock();
  return clonar(agendamento);
}

/** GET /api/admin/agenda/slots */
export async function listarSlotsAdmin(): Promise<AgendaSlot[]> {
  if (!USAR_MOCKS) {
    const { data } = await api.get<AgendaSlot[]>('/api/admin/agenda/slots');
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  return clonar(slotsAgendaMock);
}

/** POST /api/admin/agenda/slots */
export async function criarSlotAdmin(dados: DadosNovoSlot, autor: string): Promise<AgendaSlot> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<AgendaSlot>('/api/admin/agenda/slots', { ...dados, autor });
    return data;
  }
  await pausa();
  const unidade = dados.unidade.trim();
  const codigoExame = dados.codigoExame.trim();
  const nomeExame = dados.nomeExame.trim();
  const inicio = normalizarIsoMock(dados.inicio);
  const fim = normalizarIsoMock(dados.fim);
  const capacidade = Number(dados.capacidade);
  if (!unidade || !codigoExame || !nomeExame || !dados.inicio || !dados.fim) {
    throw new Error('Preencha unidade, exame, início e fim da vaga.');
  }
  if (!Number.isInteger(capacidade) || capacidade < 1) {
    throw new Error('A capacidade deve ser um número inteiro maior que zero.');
  }
  if (new Date(fim).getTime() <= new Date(inicio).getTime()) {
    throw new Error('O fim da vaga deve ser posterior ao início.');
  }
  if (slotsAgendaMock.some((slot) =>
    slot.unidade === unidade && slot.codigoExame === codigoExame && slot.inicio === inicio)) {
    throw new Error('Já existe uma vaga com estes unidade, exame e horário.');
  }
  const situacao = dados.situacao ?? 'DISPONIVEL';
  if (!['DISPONIVEL', 'LOTADO', 'ENCERRADO'].includes(situacao)) {
    throw new Error('Situação de vaga inválida.');
  }
  const slot: AgendaSlot = {
    id: `slot-${crypto.randomUUID()}`,
    unidade,
    codigoExame,
    nomeExame,
    inicio,
    fim,
    capacidade,
    ocupadas: 0,
    livres: capacidade,
    status: situacao,
  };
  slotsAgendaMock.push(slot);
  if (situacao === 'LOTADO') slotsFechadosManualmenteMock.add(slot.id);
  registrar('Vaga criada', autor, 'CONFIGURACAO', `${unidade} · ${nomeExame} · ${inicio} (${capacidade} vagas, ${situacao}).`);
  sincronizarOcupacaoMock();
  return clonar(slot);
}

/** PATCH /api/admin/agenda/slots/{id} */
export async function atualizarSlotAdmin(
  id: string,
  ajuste: AjusteSlot,
  autor: string,
): Promise<AgendaSlot> {
  if (!USAR_MOCKS) {
    const { data } = await api.patch<AgendaSlot>(`/api/admin/agenda/slots/${encodeURIComponent(id)}`, {
      ...ajuste, autor,
    });
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const slot = slotsAgendaMock.find((item) => item.id === id);
  if (!slot) throw new Error('Vaga não encontrada.');
  if (ajuste.capacidade !== undefined) {
    const capacidade = Number(ajuste.capacidade);
    if (!Number.isInteger(capacidade) || capacidade < 1) {
      throw new Error('A capacidade deve ser um número inteiro maior que zero.');
    }
    if (capacidade < slot.ocupadas) {
      throw new Error(`A capacidade não pode ficar abaixo das ${slot.ocupadas} vaga(s) ocupada(s).`);
    }
    slot.capacidade = capacidade;
  }
  if (ajuste.unidade !== undefined) {
    if (!ajuste.unidade.trim()) throw new Error('A unidade da vaga não pode ficar vazia.');
    slot.unidade = ajuste.unidade.trim();
  }
  if (ajuste.codigoExame !== undefined) {
    if (!ajuste.codigoExame.trim()) throw new Error('O código do exame não pode ficar vazio.');
    slot.codigoExame = ajuste.codigoExame.trim();
  }
  if (ajuste.nomeExame !== undefined) {
    if (!ajuste.nomeExame.trim()) throw new Error('O nome do exame não pode ficar vazio.');
    slot.nomeExame = ajuste.nomeExame.trim();
  }
  if (ajuste.inicio !== undefined) {
    if (!ajuste.inicio) throw new Error('Informe o início da vaga.');
    slot.inicio = normalizarIsoMock(ajuste.inicio);
  }
  if (ajuste.fim !== undefined) {
    if (!ajuste.fim) throw new Error('Informe o fim da vaga.');
    slot.fim = normalizarIsoMock(ajuste.fim);
  }
  if (new Date(slot.fim).getTime() <= new Date(slot.inicio).getTime()) {
    throw new Error('O fim da vaga deve ser posterior ao início.');
  }
  if (slotsAgendaMock.some((item) => item.id !== slot.id
    && item.unidade === slot.unidade && item.codigoExame === slot.codigoExame
    && item.inicio === slot.inicio)) {
    throw new Error('Já existe uma vaga com estes unidade, exame e horário.');
  }
  if (ajuste.status !== undefined) {
    if (!['DISPONIVEL', 'LOTADO', 'ENCERRADO'].includes(ajuste.status)) {
      throw new Error('Situação de vaga inválida.');
    }
    slot.status = ajuste.status;
    if (ajuste.status === 'LOTADO') slotsFechadosManualmenteMock.add(slot.id);
    else slotsFechadosManualmenteMock.delete(slot.id);
  }
  registrar('Vaga atualizada', autor, 'CONFIGURACAO',
    `${slot.unidade} · ${slot.nomeExame} · capacidade ${slot.capacidade}, situação ${slot.status}.`);
  sincronizarOcupacaoMock();
  return clonar(slot);
}

/** DELETE /api/admin/agenda/slots/{id} — remove uma vaga sem ocupação. */
export async function removerSlotAdmin(id: string, autor: string): Promise<AgendaSlot> {
  if (!USAR_MOCKS) {
    const { data } = await api.delete<AgendaSlot>(`/api/admin/agenda/slots/${encodeURIComponent(id)}`, {
      data: { autor },
    });
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const indice = slotsAgendaMock.findIndex((item) => item.id === id);
  if (indice < 0) throw new Error('Vaga não encontrada.');
  const slot = slotsAgendaMock[indice];
  const ocupada = agendamentosMock.some((agendamento) =>
    agendamento.slotId === id
    && (agendamento.status === 'ATIVO' || agendamento.status === 'PROPOSTO'));
  if (ocupada) {
    throw new Error('Não é possível remover uma vaga com agendamentos ativos ou propostas.');
  }
  slotsAgendaMock.splice(indice, 1);
  slotsFechadosManualmenteMock.delete(id);
  registrar('Vaga removida', autor, 'CONFIGURACAO',
    `${slot.unidade} · ${slot.nomeExame} · ${slot.inicio} (${slot.capacidade} vagas).`);
  return clonar(slot);
}

/** POST /api/admin/agenda/copiar-semana — replica uma semana de vagas na outra. */
export async function copiarSemanaAdmin(
  dados: CopiaSemanaPayload,
  autor: string,
): Promise<ResultadoCopiaSemana> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<ResultadoCopiaSemana>('/api/admin/agenda/copiar-semana', {
      ...dados, autor,
    });
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const origem = inicioSemanaIsoMock(dados.origem, 'origem');
  const destino = inicioSemanaIsoMock(dados.destino, 'destino');
  if (origem === destino) {
    throw new Error('A semana de destino deve ser diferente da semana de origem.');
  }
  const deslocamento = diasEntreSemanasMock(origem, destino);
  const filtroExame = dados.codigoExame?.trim() ?? '';
  const candidatas = slotsAgendaMock.filter((slot) =>
    inicioSemanaIsoMock(slot.inicio, 'inicio') === origem
    && (!filtroExame || slot.codigoExame === filtroExame));
  if (!candidatas.length) {
    throw new Error('Não há vagas para copiar na semana de origem.');
  }

  const chaves = new Set(slotsAgendaMock.map((slot) =>
    `${slot.unidade}|${slot.codigoExame}|${normalizarIsoMock(slot.inicio).slice(0, 19)}`));
  const criadas: AgendaSlot[] = [];
  let ignoradas = 0;
  for (const slot of candidatas) {
    const inicio = normalizarIsoMock(deslocarIsoMock(slot.inicio, deslocamento));
    const fim = normalizarIsoMock(deslocarIsoMock(slot.fim, deslocamento));
    const chave = `${slot.unidade}|${slot.codigoExame}|${inicio.slice(0, 19)}`;
    if (chaves.has(chave)) {
      ignoradas += 1;
      continue;
    }
    const copia: AgendaSlot = {
      id: `slot-${crypto.randomUUID()}`,
      unidade: slot.unidade,
      codigoExame: slot.codigoExame,
      nomeExame: slot.nomeExame,
      inicio,
      fim,
      capacidade: slot.capacidade,
      ocupadas: 0,
      livres: slot.capacidade,
      status: slot.status,
    };
    slotsAgendaMock.push(copia);
    chaves.add(chave);
    if (copia.status === 'LOTADO') slotsFechadosManualmenteMock.add(copia.id);
    criadas.push(clonar(copia));
  }
  registrar('Semana de vagas copiada', autor, 'CONFIGURACAO',
    `${origem} → ${destino}: ${criadas.length} vaga(s) criada(s), ${ignoradas} já existiam.`);
  sincronizarOcupacaoMock();
  return { origem, destino, codigoExame: filtroExame, criadas, ignoradas, total: candidatas.length };
}

/** POST /api/agendamentos/{id}/mover — move uma proposta para outro horário (drag & drop). */
export async function moverPropostaAgendamento(
  id: string,
  slotId: string,
  autor: string,
): Promise<Agendamento> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<Agendamento>(
      `/api/agendamentos/${encodeURIComponent(id)}/mover`, { slotId, autor },
    );
    return data;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const agendamento = agendamentosMock.find((item) => item.id === id);
  if (!agendamento) throw new Error('Proposta não encontrada.');
  if (agendamento.status !== 'PROPOSTO') throw new Error('Somente propostas podem ser movidas.');
  const slot = slotsAgendaMock.find((item) => item.id === slotId);
  if (!slot) throw new Error('Vaga de destino não encontrada.');
  if (slot.id === agendamento.slotId) throw new Error('A vaga informada já é a atual.');
  const solicitacao = encontrarSolicitacaoMock(agendamento.solicitacaoId);
  const codigos = new Set(
    (solicitacao?.itensExame ?? [])
      .map((item) => item.codigoExame.trim().toUpperCase())
      .filter(Boolean),
  );
  if (codigos.size > 0 && !codigos.has(slot.codigoExame.trim().toUpperCase())) {
    throw new Error('A vaga de destino não corresponde ao exame solicitado.');
  }
  validarSlotMock(slot, agendamento.pacienteChave, agendamento.id);
  const anterior = agendamento.dataHora;
  agendamento.slotId = slot.id;
  agendamento.dataHora = slot.inicio;
  agendamento.unidade = slot.unidade;
  agendamento.exame = slot.nomeExame;
  if (solicitacao?.agendamento) solicitacao.agendamento.dataHora = slot.inicio;
  registrar('Proposta movida (arrastar e soltar)', autor, 'NEGOCIO_CLINICO',
    `${agendamento.protocolo}: ${anterior} → ${slot.inicio}.`);
  sincronizarOcupacaoMock();
  return clonar(agendamento);
}

/** POST /api/agendamentos/lote — edição em lote de status na fila. */
export async function alterarStatusLoteAgendamento(
  agendamentoIds: string[],
  novoStatus: string,
  justificativa: string,
  autor: string,
): Promise<{ processados: number; novoStatus: string; itens: Array<{
  agendamentoId: string; statusAnterior: string; statusNovo: string;
  protocolo: string; pacienteNome: string;
}> }> {
  if (!USAR_MOCKS) {
    const { data } = await api.post<{
      processados: number; novoStatus: string; itens: any[];
    }>('/api/agendamentos/lote', {
      agendamentoIds, novoStatus, justificativa, autor,
    });
    return data as any;
  }
  await pausa();
  sincronizarOcupacaoMock();
  const itens: Array<{
    agendamentoId: string; statusAnterior: string; statusNovo: string;
    protocolo: string; pacienteNome: string;
  }> = [];
  for (const id of agendamentoIds) {
    const agendamento = agendamentosMock.find((item) => item.id === id);
    if (!agendamento) throw new Error(`Agendamento ${id} não encontrado.`);
    const statusAnterior = agendamento.status;
    agendamento.status = novoStatus as unknown as Agendamento['status'];
    agendamento.justificativa = justificativa.trim();
    agendamento.confirmadoPor = autor;
    const solicitacao = encontrarSolicitacaoMock(agendamento.solicitacaoId);
    if (solicitacao) {
      if (novoStatus === 'ATIVO') solicitacao.status = 'AGENDADA' as Solicitacao['status'];
      solicitacao.agendamento = solicitacao.agendamento || {
        dataHora: agendamento.dataHora,
        unidade: agendamento.unidade,
        confirmadoPor: autor,
        criadoEm: agoraIso(),
      };
    }
    registrar('Alteração de status em lote', autor, 'NEGOCIO_CLINICO',
      `${agendamento.protocolo}: ${statusAnterior} → ${novoStatus}.`);
    itens.push({
      agendamentoId: id,
      statusAnterior,
      statusNovo: novoStatus,
      protocolo: agendamento.protocolo,
      pacienteNome: agendamento.pacienteNome,
    });
  }
  sincronizarOcupacaoMock();
  return { processados: itens.length, novoStatus, itens };
}

function inicioSemanaIsoMock(valor: string, campo: string): string {
  const texto = valor.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
    throw new Error(`Campo ${campo} deve ser uma data ISO.`);
  }
  const data = new Date(`${texto}T12:00:00`);
  if (Number.isNaN(data.getTime())) throw new Error(`Campo ${campo} deve ser uma data válida.`);
  data.setDate(data.getDate() - ((data.getDay() + 6) % 7));
  return paraIsoLocal(data.getTime()).slice(0, 10);
}

function diasEntreSemanasMock(origem: string, destino: string): number {
  const partesOrigem = origem.split('-').map(Number);
  const partesDestino = destino.split('-').map(Number);
  return Math.round((
    Date.UTC(partesDestino[0], partesDestino[1] - 1, partesDestino[2])
    - Date.UTC(partesOrigem[0], partesOrigem[1] - 1, partesOrigem[2])
  ) / 86_400_000);
}

function deslocarIsoMock(iso: string, dias: number): string {
  const data = new Date(`${iso.slice(0, 10)}T12:00:00`);
  data.setDate(data.getDate() + dias);
  return `${paraIsoLocal(data.getTime()).slice(0, 10)}T${iso.slice(11)}`;
}
