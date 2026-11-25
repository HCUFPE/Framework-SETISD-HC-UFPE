/**
 * Camada de serviços do SAE-HC.
 * As views consomem somente esta camada, que usa mocks ou a API real conforme
 * VITE_USE_MOCKS. Os contratos HTTP estão em docs/especificacao/05-interfaces.md.
 */
import api from './api';
import { USAR_MOCKS } from '../config/mocks';
import { agoraIso, horasDesdeReferencia, somarHoras } from '../config/tempo';
import { calcularPontuacao, clonar, consultarAdMock, mockDb } from '../mocks/fixtures';
import { classificarPrioridade } from '../utils/format';
import type {
  AdUser,
  CriterioPriorizacao,
  EventoHistorico,
  FiltroFila,
  FiltroIndicadores,
  FormsEvento,
  Indicadores,
  Relatorio,
  ResultadoContato,
  ResultadoFila,
  ResultadoRelatorio,
  Solicitacao,
  UsuarioEquipe,
  VersaoCriterios,
} from '../types/sae';

const pausa = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 120));

const FILTROS_TODOS: FiltroFila = {
  busca: '', status: '', tipoExame: '', periodo: 'todos', pagina: 1, porPagina: 20,
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
      return buscaOk && statusOk && tipoOk && filtrarPorPeriodo(item, filtros.periodo);
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
    detalhes: justificativa.trim() ? `Justificativa: ${justificativa.trim()}` : 'Conferência concluída sem divergências pendentes.',
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
  solicitacao.status = resultado === 'ACEITE' ? 'AGUARDANDO_CONTATO' : 'EM_CONFERENCIA';
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
  if (solicitacao.status !== 'AGUARDANDO_CONTATO') {
    throw new Error('A solicitação precisa estar validada e aguardando contato.');
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
    acao: 'Agendamento efetivado no AGHUX',
    autor,
    categoria: 'NEGOCIO_CLINICO',
    detalhes: `Data e horário confirmados: ${solicitacao.agendamento.dataHora}.`,
  });
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
  const etapas = ['Conferência com AGHUX', 'Contato com paciente', 'Validação automática'];
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
    recebidoEm: '2026-09-28T14:05:34.227',
    processadoEm: '2026-09-28T14:06:12.227',
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
    recebidoEm: '2026-09-28T14:12:08.227',
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
    recebidoEm: '2026-09-28T14:18:41.227',
    processadoEm: '2026-09-28T14:18:55.227',
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
