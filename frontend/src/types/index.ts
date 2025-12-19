// ==========================================
// TIPOS DE PACIENTE
// ==========================================

export interface Paciente {
  codigo: number;
  prontuario: string;
  nome: string;
  dt_nascimento: string;
  idade: number;
  nome_mae: string;
  nome_pai?: string;
  sexo: 'M' | 'F';
  cor: string;
  especialidade_atual: string;
  diagnostico_principal: string;
  data_admissao: string;
  data_alta_prevista?: string;
  origem_atendimento: string;
}

export interface PacienteResumo {
  prontuario: string;
  idade: number;
  especialidade: string;
}

// ==========================================
// TIPOS DE LEITO
// ==========================================

export type BedStatus = 'disponivel' | 'ocupado' | 'higienizacao' | 'desativado' | 'alta';
export type BedType = 'cirurgico' | 'hem' | 'obstetrico' | 'outro' | 'nao_definido';

export interface Leito {
  leito_numero: string;
  status: BedStatus;
  tipo: BedType;
  paciente_prontuario?: string;
  paciente_idade?: number;
  paciente_especialidade?: string;
  proximo_prontuario?: string;
  proximo_especialidade?: string;
  tipo_reserva?: string;
  sinalizacao_transferencia: boolean;
  previsao_liberacao?: string;
}

// Interface para o formato usado no componente BedCard
export interface LeitoFormatado {
  leitoNumero: string;
  status: BedStatus;
  tipo: BedType;
  pacienteAtual?: PacienteResumo;
  proximoPaciente?: PacienteResumo;
  tipoReserva?: string;
  sinalizacaoTransferencia?: boolean;
  previsaoLiberacao?: string;
}

// ==========================================
// TIPOS DE RESPOSTA DE API
// ==========================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PacientesListResponse {
  pacientes: Paciente[];
  total: number;
}

export interface LeitosListResponse {
  leitos: Leito[];
  total: number;
}
