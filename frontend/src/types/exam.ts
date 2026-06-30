import type { ExamType } from '../constants/examTypes';
import type { ExamStatus } from '../constants/statuses';

export interface AghuData {
  numeroSolicitacaoAghu: string;
  nomePaciente: string;
  prontuario: string;
  idade: number;
  sexo: 'M' | 'F';
  origem: 'Internado' | 'Ambulatorial';
  clinica?: string;
  tipoMaterial: string;
  tipoExame: ExamType;
  procedimentoSus: string;
  indicacaoClinica: string;
}

export interface RecepcaoData {
  dataEntrada: Date;
  quantidadeFrascos: number;
  descricaoFisica: string;
  frascosIds: string[];
  responsavel: string;
}

export interface CasseteInfo {
  id: string; // ex: 'A1', 'B', 'C3'
  estrutura: string; // ex: 'Útero', 'Trompa direita'
  coloracao: string;
  observacao?: string;
}

export interface MacroscopiaData {
  dataMacro: Date;
  responsavel: string;
  descricaoMacroscopica: string;
  sobraMaterial: boolean;
  cassetes: CasseteInfo[];
}

export interface ProcessamentoData {
  quantidadeBlocos: number;
  quantidadeLaminas: number;
  dataLiberacao: Date;
  responsavel: string;
  materialComplementarDataSaida?: Date;
}

export interface MicroscopiaData {
  dataRecebimento: Date;
  laudo?: string;
  solicitouComplemento: boolean;
  dataLiberacaoLaudo?: Date;
  responsavelLiberacao?: string;
}

export interface ExamCaseDetail {
  codigoLocal: string;
  etapaAtual: ExamStatus;
  urgente: boolean;
  aghu: AghuData;
  recepcao?: RecepcaoData;
  macroscopia?: MacroscopiaData;
  processamentoTecnico?: ProcessamentoData;
  microscopia?: MicroscopiaData;
}