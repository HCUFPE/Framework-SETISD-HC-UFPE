import type { ExamType } from '../constants/examTypes';
import type { ExamStatus } from '../constants/statuses';

/** Dados importados do AGHU — somente leitura, nunca editados pelo nosso sistema. */
export interface AghuData {
  numeroSolicitacaoAghu: string;
  nomePaciente: string;
  prontuario: string;
  idade: number;
  origem: 'Internado' | 'Ambulatorial';
  clinica?: string; // só relevante se Internado (ex: "Hepatologia") — nunca andar/ala
  tipoMaterial: string; // descrição do material, às vezes vem vazia do AGHU
  tipoExame: ExamType;
  procedimentoSus: string; // subclassificação de faturamento: Geral, Biópsia, Peça de mama etc
  indicacaoClinica: string;
}

export interface RecepcaoData {
  dataEntrada: Date;
  quantidadeFrascos: number;
  responsavel: string;
}

export interface MacroscopiaData {
  dataMacro: Date;
  responsavel: string;
  descricaoMacroscopica: string;
  quantidadeCassetes: number;
  destino: 'Histotécnico' | 'Manual';
  coloracaoEspecial: boolean;
  coloracaoQual?: string;
  sobraMaterial: boolean;
}

export interface ProcessamentoData {
  quantidadeBlocos: number;
  quantidadeLaminas: number;
  dataLiberacao: Date;
  responsavel: string;
  materialComplementarDataSaida?: Date; // preenchido quando teve recorte adicional
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