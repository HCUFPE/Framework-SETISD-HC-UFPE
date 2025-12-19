import { Leito, LeitoFormatado, BedStatus, BedType } from '../../types';

// Dados mockados de leitos baseados no CSV
const LEITOS_MOCK: Leito[] = [
  {
    leito_numero: 'UTI-01',
    status: 'ocupado',
    tipo: 'cirurgico',
    paciente_prontuario: '77018',
    paciente_idade: 30,
    paciente_especialidade: 'Cirurgia Geral',
    proximo_prontuario: '77012',
    proximo_especialidade: 'Nefrologia',
    tipo_reserva: 'Emergencia',
    sinalizacao_transferencia: false,
    previsao_liberacao: '2025-12-03',
  },
  {
    leito_numero: 'UTI-02',
    status: 'ocupado',
    tipo: 'hem',
    paciente_prontuario: '77016',
    paciente_idade: 27,
    paciente_especialidade: 'Hematologia',
    sinalizacao_transferencia: false,
    previsao_liberacao: '2025-12-12',
  },
  {
    leito_numero: 'UTI-03',
    status: 'ocupado',
    tipo: 'obstetrico',
    paciente_prontuario: '77007',
    paciente_idade: 40,
    paciente_especialidade: 'Obstetricia',
    proximo_prontuario: '77009',
    proximo_especialidade: 'Infectologia',
    tipo_reserva: 'Clinica',
    sinalizacao_transferencia: true,
    previsao_liberacao: '2025-12-01',
  },
  {
    leito_numero: 'UTI-04',
    status: 'disponivel',
    tipo: 'nao_definido',
    sinalizacao_transferencia: false,
  },
  {
    leito_numero: 'UTI-05',
    status: 'higienizacao',
    tipo: 'nao_definido',
    sinalizacao_transferencia: false,
    previsao_liberacao: '2025-11-27',
  },
  {
    leito_numero: 'UTI-06',
    status: 'disponivel',
    tipo: 'cirurgico',
    proximo_prontuario: '77018',
    proximo_especialidade: 'Cirurgia Geral',
    tipo_reserva: 'Cirurgico',
    sinalizacao_transferencia: false,
    previsao_liberacao: '2025-11-29',
  },
  {
    leito_numero: 'UTI-07',
    status: 'ocupado',
    tipo: 'outro',
    paciente_prontuario: '77006',
    paciente_idade: 25,
    paciente_especialidade: 'Neurologia',
    proximo_prontuario: '77014',
    proximo_especialidade: 'Pneumologia',
    tipo_reserva: 'Clinica',
    sinalizacao_transferencia: false,
    previsao_liberacao: '2025-12-05',
  },
  {
    leito_numero: 'UTI-08',
    status: 'desativado',
    tipo: 'outro',
    sinalizacao_transferencia: false,
  },
  {
    leito_numero: 'UTI-09',
    status: 'ocupado',
    tipo: 'cirurgico',
    paciente_prontuario: '77010',
    paciente_idade: 21,
    paciente_especialidade: 'Trauma',
    proximo_prontuario: '77002',
    proximo_especialidade: 'Ortopedia',
    tipo_reserva: 'Emergencia',
    sinalizacao_transferencia: true,
    previsao_liberacao: '2025-12-04',
  },
  {
    leito_numero: 'UTI-10',
    status: 'alta',
    tipo: 'nao_definido',
    paciente_prontuario: '77005',
    paciente_idade: 49,
    paciente_especialidade: 'Oncologia',
    proximo_prontuario: '77011',
    proximo_especialidade: 'Reumatologia',
    tipo_reserva: 'Clinica',
    sinalizacao_transferencia: false,
    previsao_liberacao: '2025-11-30',
  },
];

/**
 * Simula um delay de rede para tornar o mock mais realista
 */
const delay = (ms: number = 300) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Converte um Leito do formato CSV para o formato usado no componente BedCard
 */
export const formatarLeito = (leito: Leito): LeitoFormatado => {
  return {
    leitoNumero: leito.leito_numero,
    status: leito.status,
    tipo: leito.tipo,
    pacienteAtual: leito.paciente_prontuario
      ? {
          prontuario: leito.paciente_prontuario,
          idade: leito.paciente_idade!,
          especialidade: leito.paciente_especialidade!,
        }
      : undefined,
    proximoPaciente: leito.proximo_prontuario
      ? {
          prontuario: leito.proximo_prontuario,
          idade: 0, // Idade não disponível na reserva
          especialidade: leito.proximo_especialidade!,
        }
      : undefined,
    tipoReserva: leito.tipo_reserva,
    sinalizacaoTransferencia: leito.sinalizacao_transferencia,
    previsaoLiberacao: leito.previsao_liberacao,
  };
};

/**
 * Retorna todos os leitos
 */
export const listarLeitos = async (): Promise<Leito[]> => {
  await delay();
  return [...LEITOS_MOCK];
};

/**
 * Retorna todos os leitos formatados para o componente BedCard
 */
export const listarLeitosFormatados = async (): Promise<LeitoFormatado[]> => {
  await delay();
  return LEITOS_MOCK.map(formatarLeito);
};

/**
 * Busca um leito por número
 */
export const obterLeitoPorNumero = async (numero: string): Promise<Leito | null> => {
  await delay();
  const leito = LEITOS_MOCK.find(l => l.leito_numero === numero);
  return leito || null;
};

/**
 * Busca leitos por status
 */
export const listarLeitosPorStatus = async (status: BedStatus): Promise<Leito[]> => {
  await delay();
  return LEITOS_MOCK.filter(l => l.status === status);
};

/**
 * Busca leitos por tipo
 */
export const listarLeitosPorTipo = async (tipo: BedType): Promise<Leito[]> => {
  await delay();
  return LEITOS_MOCK.filter(l => l.tipo === tipo);
};

/**
 * Retorna estatísticas dos leitos
 */
export const obterEstatisticasLeitos = async () => {
  await delay();
  
  const total = LEITOS_MOCK.length;
  const ocupados = LEITOS_MOCK.filter(l => l.status === 'ocupado').length;
  const disponiveis = LEITOS_MOCK.filter(l => l.status === 'disponivel').length;
  const higienizacao = LEITOS_MOCK.filter(l => l.status === 'higienizacao').length;
  const desativados = LEITOS_MOCK.filter(l => l.status === 'desativado').length;
  const alta = LEITOS_MOCK.filter(l => l.status === 'alta').length;
  const comReserva = LEITOS_MOCK.filter(l => l.proximo_prontuario).length;
  const alertasTransferencia = LEITOS_MOCK.filter(l => l.sinalizacao_transferencia).length;

  return {
    total,
    ocupados,
    disponiveis,
    higienizacao,
    desativados,
    alta,
    comReserva,
    alertasTransferencia,
    taxaOcupacao: ((ocupados / (total - desativados)) * 100).toFixed(1),
  };
};
