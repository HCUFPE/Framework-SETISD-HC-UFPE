/**
 * Base de dados simulada do SAE-HC.
 *
 * As solicitações vêm do export CSV do AGHUX (Documentos de Apoio), importado
 * por scripts/importar_dados_aghux.py para dadosAghux.json. Dados vivos ficam
 * em memória e são alterados pelas ações das telas; ao trocar VITE_USE_MOCKS
 * para false, os serviços passam a chamar a API documentada.
 */
import dadosAghuxJson from './dadosAghux.json';
import { REFERENCIA_EM, somarHoras } from '../config/tempo';
import { classificarPrioridade, horasDesde } from '../utils/format';
import type {
  AdUser,
  Alerta,
  CampoComparacao,
  CriterioPriorizacao,
  Divergencia,
  EventoHistorico,
  FonteAghux,
  Perfil,
  Solicitacao,
  UsuarioEquipe,
  VersaoCriterios,
} from '../types/sae';

const dadosAghux = dadosAghuxJson as FonteAghux;

export const clonar = <T>(valor: T): T => JSON.parse(JSON.stringify(valor)) as T;

export const criteriosPadrao: CriterioPriorizacao[] = [
  {
    id: 'crit-1',
    chave: 'urgenciaClinica',
    nome: 'Urgência clínica',
    descricao: 'Não consta no export AGHUX; valor neutro simulado até a integração da triagem.',
    peso: 40,
    ordem: 1,
    ativo: true,
  },
  {
    id: 'crit-2',
    chave: 'idade',
    nome: 'Idade do paciente',
    descricao: 'Não consta no export AGHUX; valor neutro simulado até a integração do prontuário.',
    peso: 25,
    ordem: 2,
    ativo: true,
  },
  {
    id: 'crit-3',
    chave: 'tempoEspera',
    nome: 'Tempo de espera',
    descricao: 'Derivado de data_solicitao do AGHUX: 1 ponto a cada 6 dias de espera (máximo 10).',
    peso: 20,
    ordem: 3,
    ativo: true,
  },
  {
    id: 'crit-4',
    chave: 'complexidadeExame',
    nome: 'Complexidade do exame',
    descricao: 'Derivada do código do exame (codigo_exame) presente no export AGHUX.',
    peso: 15,
    ordem: 4,
    ativo: true,
  },
];

/** Pontuação 0-100: atributos de 0 a 10 ponderados pelos pesos dos critérios ativos. */
export function calcularPontuacao(atributos: Record<string, number>, criterios: CriterioPriorizacao[]): number {
  const total = criterios
    .filter((criterio) => criterio.ativo)
    .reduce((soma, criterio) => soma + (atributos[criterio.chave] ?? 0) * criterio.peso, 0);
  return Math.min(100, Math.round(total / 10));
}

/** Complexidade estimada a partir da sigla do exame no AGHU. */
function complexidadeExame(codigo: string): number {
  const sigla = codigo.toUpperCase();
  if (/^(CM|PET|RM|TC|CT)/.test(sigla)) return 9;
  if (/^(MBIOP|CITOP|ANA|PAT)/.test(sigla)) return 8;
  if (/^US/.test(sigla)) return 6;
  if (/^(MAMO|DMO|DEN)/.test(sigla)) return 5;
  if (/^RX/.test(sigla)) return 3;
  if (/^(LOG|ATL|IMT|PA|AUDI)/.test(sigla)) return 4;
  return 5;
}

/** 1 ponto a cada 6 dias de espera, limitado a 10 (evita saturar a fila). */
function tempoEspera(dataSolicitacao: string): number {
  return Math.min(10, Math.round(horasDesde(dataSolicitacao) / 144));
}

function comparacoes(item: FonteAghux['solicitacoes'][number]): CampoComparacao[] {
  const iguais = (campo: string, valor: string): CampoComparacao => ({
    campo, formulario: valor, aghux: valor,
  });
  return [
    iguais('Nome completo', item.nome),
    iguais('Prontuário', item.prontuario),
    iguais('Telefone', item.telefone),
    iguais('Cidade / UF', `${item.cidade} / ${item.estado}`),
    iguais('Unidade solicitante', item.unidadeSolicitante),
    iguais('Profissional solicitante', `${item.solicitante.nome} (${item.solicitante.codigo})`),
  ];
}

function historico(item: FonteAghux['solicitacoes'][number]): EventoHistorico[] {
  const codigo = item.codigoSolicitacao;
  return [
    {
      id: `${codigo}-h1`,
      em: item.dataSolicitacao,
      acao: 'Solicitação recebida do formulário externo',
      autor: 'AGHUX',
      categoria: 'NEGOCIO_CLINICO',
      detalhes: `Export ${dadosAghux.fonte} — ${item.itens.length} item(ns) de exame.`,
    },
    {
      id: `${codigo}-h2`,
      em: somarHoras(item.dataSolicitacao, 1),
      acao: 'Solicitação inserida na fila priorizada',
      autor: 'Sistema',
      categoria: 'NEGOCIO_CLINICO',
      detalhes: 'Prioridade calculada pelos critérios vigentes.',
    },
  ];
}

const solicitacoes: Solicitacao[] = dadosAghux.solicitacoes.map((item) => {
  const atributos: Record<string, number> = {
    urgenciaClinica: 5,
    idade: 5,
    tempoEspera: tempoEspera(item.dataSolicitacao),
    complexidadeExame: complexidadeExame(item.itens[0]?.codigoExame ?? ''),
  };
  const pontuacao = calcularPontuacao(atributos, criteriosPadrao);
  return {
    id: `aghux-${item.codigoSolicitacao}`,
    protocolo: `AGHUX-${item.codigoSolicitacao}`,
    codigoSolicitacaoAghux: item.codigoSolicitacao,
    prontuario: item.prontuario,
    pacienteNome: item.nome,
    telefone: item.telefone,
    cidade: item.cidade,
    estado: item.estado,
    exame: item.itens[0]?.nomeExame ?? 'Exame não informado',
    itensExame: clonar(item.itens),
    tipoExame: item.tipoExame,
    setorSolicitante: item.unidadeSolicitante,
    solicitanteCodigo: item.solicitante.codigo,
    solicitanteNome: item.solicitante.nome,
    status: 'RECEBIDA',
    pontuacao,
    prioridade: classificarPrioridade(pontuacao),
    recebidaEm: item.dataSolicitacao,
    prazoValidacaoEm: somarHoras(item.dataSolicitacao, 24),
    atributos,
    atributosSimulados: ['urgenciaClinica', 'idade'],
    comparacoes: comparacoes(item),
    alertas: [] as Alerta[],
    divergencias: [] as Divergencia[],
    contatos: [],
    historico: historico(item),
    agendamento: null,
  };
});

export const tiposExameDisponiveis = Array.from(
  new Set(solicitacoes.map((item) => item.tipoExame)),
).sort();

const versaoInicial: VersaoCriterios = {
  numero: 1,
  criadoEm: somarHoras(REFERENCIA_EM, -240),
  autor: 'Área Gestora',
  justificativa: 'Definição inicial dos critérios e pesos pela gestão da Central de Marcação.',
  criterios: clonar(criteriosPadrao),
};

const equipe: UsuarioEquipe[] = [
  {
    id: 'usr-1',
    login: 'maria.gestora',
    nome: 'Maria Gestora',
    email: 'maria.gestora@ebserh.gov.br',
    lotacao: 'Central de Marcação',
    perfil: 'AREA_GESTORA',
    ativo: true,
    criadoEm: somarHoras(REFERENCIA_EM, -500),
  },
  {
    id: 'usr-2',
    login: 'ana.operadora',
    nome: 'Ana Operadora',
    email: 'ana.operadora@ebserh.gov.br',
    lotacao: 'Central de Marcação',
    perfil: 'OPERADOR',
    ativo: true,
    criadoEm: somarHoras(REFERENCIA_EM, -420),
  },
  {
    id: 'usr-3',
    login: 'joao.chefia',
    nome: 'João Chefia',
    email: 'joao.chefia@ebserh.gov.br',
    lotacao: 'Central de Marcação',
    perfil: 'CHEFIA',
    ativo: true,
    criadoEm: somarHoras(REFERENCIA_EM, -400),
  },
  {
    id: 'usr-4',
    login: 'carla.coordenacao',
    nome: 'Carla Coordenação',
    email: 'carla.coordenacao@ebserh.gov.br',
    lotacao: 'Gerência de Atenção à Saúde',
    perfil: 'COORDENACAO',
    ativo: true,
    criadoEm: somarHoras(REFERENCIA_EM, -380),
  },
  {
    id: 'usr-5',
    login: 'tiago.setisd',
    nome: 'Tiago Ferrão',
    email: 'tiago.ferrao@ebserh.gov.br',
    lotacao: 'SETISD',
    perfil: 'ADMIN_TI',
    ativo: true,
    criadoEm: somarHoras(REFERENCIA_EM, -360),
  },
  {
    id: 'usr-6',
    login: 'paula.operadora',
    nome: 'Paula Operadora',
    email: 'paula.operadora@ebserh.gov.br',
    lotacao: 'Central de Marcação',
    perfil: 'OPERADOR',
    ativo: false,
    criadoEm: somarHoras(REFERENCIA_EM, -300),
  },
];

export const mockDb = {
  solicitacoes,
  criterios: clonar(criteriosPadrao),
  versoes: [versaoInicial],
  equipe,
  auditoria: [] as EventoHistorico[],
};

/** Usuário simulado para navegação sem backend. Os perfis são alternáveis na interface. */
export function usuarioMock(): {
  username: string;
  groups: string[];
  displayName: string[];
  email: string[];
  perfis: Perfil[];
} {
  return {
    username: 'ana.operadora',
    groups: ['GLO-SEC-HCPE-SETISD'],
    displayName: ['Ana Operadora'],
    email: ['ana.operadora@ebserh.gov.br'],
    perfis: ['OPERADOR', 'CHEFIA', 'AREA_GESTORA', 'COORDENACAO', 'ADMIN_TI'],
  };
}

/** Busca simulada no Active Directory para o botão "Consultar AD". */
export function consultarAdMock(username: string): AdUser {
  if (!username || username.toLowerCase().includes('inexistente')) {
    return { exists: false, username, displayName: '', email: '', department: '' };
  }
  const nome = username.split('.').map((parte) => parte.charAt(0).toUpperCase() + parte.slice(1)).join(' ');
  return {
    exists: true,
    username,
    displayName: nome,
    email: `${username}@ebserh.gov.br`,
    department: 'Central de Marcação de Exames',
  };
}
