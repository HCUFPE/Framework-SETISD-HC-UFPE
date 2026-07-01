import api from './api';
import type { ExamCaseDetail, AghuData } from '../types/exam';
import type { ExamType } from '../constants/examTypes';

export interface DashboardExame {
  id: string;
  solicitacao: string;
  paciente: string;
  etapa: string;
  data_entrada: string;
  atrasado: boolean;
}

export interface ExameCreate {
  paciente: { cpf?: string; cns?: string; nome: string; data_nascimento?: string; origem?: string };
  tipo_exame?: string;
  tipo_peca?: string;
  topografia?: string;
  numero_exame_aghu?: string | null;
}

// --- Respostas do backend (subconjunto usado pelo frontend) ---
export interface TriagemResult {
  exame: { id: string; numero_solicitacao: string; tipo_exame: string; status: string; data_recebimento?: string };
  frasco: { id: string; codigo_interno: string; qr_code: string; status: string };
  etiqueta: { tipo: string; numero_solicitacao: string; codigo: string; qr_code: string };
}

export interface FrascoDetalhe {
  id_frasco: string;
  id_exame: string;
  codigo_interno: string;
  status: string;
  numero_solicitacao: string;
  numero_exame_aghu?: string | null;
  tipo_peca?: string | null;
  paciente_nome: string;
  data_criacao?: string | null;
}

export interface CasseteOut {
  id: string;
  id_frasco: string;
  letra_fragmento: string;
  qr_code: string;
  coloracao_padrao: string;
  status: string;
}

export interface MacroscopiaResult {
  macroscopia: { id: string; id_frasco: string; descricao: string; numero_cassetes: number };
  frasco: { id: string; status: string };
  cassetes: CasseteOut[];
  etiquetas: { tipo: string; numero_solicitacao: string; codigo: string; qr_code: string }[];
}

export interface CasseteFila {
  id: string;
  letra_fragmento: string;
  qr_code: string;
  status: string;
  codigo_interno_frasco?: string | null;
  numero_solicitacao?: string | null;
  paciente_nome?: string | null;
  data_criacao?: string | null;
}

export interface BlocoOut {
  id: string;
  id_cassete: string;
  id_lote: string;
  codigo_bloco: string;
  qr_code: string;
  status: string;
}

// Detalhe agregado do caso (GET /api/exames/{id}/detalhe) — snake_case do backend.
export interface ExameDetalheApi {
  codigo_local: string;
  etapa_atual: string;
  urgente: boolean;
  aghu: {
    nome_paciente: string;
    prontuario: string | null;
    idade: number;
    origem: string;
    tipo_material: string;
    tipo_exame: string;
    numero_solicitacao_aghu: string;
    procedimento_sus: string;
    indicacao_clinica: string;
  };
  recepcao: { data_entrada: string; quantidade_frascos: number; descricao_fisica: string; frascos_ids: string[]; responsavel: string } | null;
  macroscopia: { data_macro: string; responsavel: string; descricao: string; sobra_material: boolean; cassetes: { id: string; estrutura: string; coloracao: string }[] } | null;
  processamento: { blocos: { id: string; cassete_id: string; responsavel: string; data_inclusao: string }[]; laminas: { id: string; bloco_id: string; coloracao: string }[]; data_liberacao: string | null; responsavel: string } | null;
  microscopia: { data_recebimento: string; data_liberacao_laudo: string | null; responsavel: string; laudo: string | null } | null;
}

export interface MicroscopiaPendencia {
  id: string;
  numero_solicitacao: string;
  paciente_nome: string;
  status: string;
  tipo_exame: string;
  data_recebimento: string | null;
}

// Converte o detalhe agregado do backend (snake_case) no ExamCaseDetail das telas.
export function mapExameDetalhe(d: ExameDetalheApi): ExamCaseDetail {
  return {
    codigoLocal: d.codigo_local,
    etapaAtual: d.etapa_atual as ExamCaseDetail['etapaAtual'],
    urgente: d.urgente,
    aghu: {
      numeroSolicitacaoAghu: d.aghu.numero_solicitacao_aghu,
      nomePaciente: d.aghu.nome_paciente,
      prontuario: d.aghu.prontuario ?? '—',
      idade: d.aghu.idade,
      sexo: 'M',
      origem: d.aghu.origem as AghuData['origem'],
      tipoMaterial: d.aghu.tipo_material,
      tipoExame: d.aghu.tipo_exame as ExamType,
      procedimentoSus: d.aghu.procedimento_sus,
      indicacaoClinica: d.aghu.indicacao_clinica,
    },
    recepcao: d.recepcao
      ? {
          dataEntrada: new Date(d.recepcao.data_entrada),
          quantidadeFrascos: d.recepcao.quantidade_frascos,
          descricaoFisica: d.recepcao.descricao_fisica,
          frascosIds: d.recepcao.frascos_ids,
          responsavel: d.recepcao.responsavel,
        }
      : undefined,
    macroscopia: d.macroscopia
      ? {
          dataMacro: new Date(d.macroscopia.data_macro),
          responsavel: d.macroscopia.responsavel,
          descricaoMacroscopica: d.macroscopia.descricao,
          sobraMaterial: d.macroscopia.sobra_material,
          cassetes: d.macroscopia.cassetes,
        }
      : undefined,
    processamentoTecnico: d.processamento
      ? {
          blocos: d.processamento.blocos.map(b => ({
            id: b.id,
            casseteId: b.cassete_id,
            responsavel: b.responsavel,
            dataInclusao: new Date(b.data_inclusao),
          })),
          laminas: d.processamento.laminas.map(l => ({ id: l.id, blocoId: l.bloco_id, coloracao: l.coloracao })),
          dataLiberacao: d.processamento.data_liberacao ? new Date(d.processamento.data_liberacao) : undefined,
          responsavelLiberacao: d.processamento.responsavel,
        }
      : undefined,
    microscopia: d.microscopia
      ? {
          dataRecebimento: new Date(d.microscopia.data_recebimento),
          solicitouComplemento: false,
          dataLiberacaoLaudo: d.microscopia.data_liberacao_laudo ? new Date(d.microscopia.data_liberacao_laudo) : undefined,
          responsavelLiberacao: d.microscopia.responsavel,
          laudo: d.microscopia.laudo ?? undefined,
        }
      : undefined,
  };
}

export const exameService = {
  // --- Dashboard ---
  async dashboard(): Promise<DashboardExame[]> {
    const { data } = await api.get('/api/exames/dashboard');
    return data;
  },
  async detalhe(id: string): Promise<ExameDetalheApi> {
    const { data } = await api.get(`/api/exames/${id}/detalhe`);
    return data;
  },

  // --- Microscopia ---
  async pendenciasMicroscopia(): Promise<MicroscopiaPendencia[]> {
    const { data } = await api.get('/api/microscopia/pendencias');
    return data;
  },
  async registrarLaudo(idExame: string, dados: { acao: 'liberar' | 'revisao' | 'complemento'; responsavel?: string; laudo?: string; observacoes?: string }) {
    const { data } = await api.post(`/api/microscopia/${idExame}/laudo`, dados);
    return data;
  },

  // --- Triagem / Recepção ---
  async criar(dados: ExameCreate): Promise<TriagemResult> {
    const { data } = await api.post('/api/exames', dados);
    return data;
  },
  async encaminharMacroscopia(frascoId: string) {
    const { data } = await api.post(`/api/frascos/${frascoId}/encaminhar-macroscopia`, {});
    return data;
  },

  // --- Recepção ---
  async pendenciasRecepcao(): Promise<FrascoDetalhe[]> {
    const { data } = await api.get('/api/frascos/pendencias-recepcao');
    return data;
  },

  // --- Macroscopia ---
  async buscarFrasco(params: { numero_solicitacao?: string; codigo_interno?: string }): Promise<FrascoDetalhe[]> {
    const { data } = await api.get('/api/frascos/buscar', { params });
    return data;
  },
  async iniciarMacroscopia(frascoId: string) {
    const { data } = await api.post(`/api/frascos/${frascoId}/iniciar-macroscopia`, {});
    return data;
  },
  async registrarMacroscopia(dados: { id_frasco: string; descricao: string; numero_cassetes: number }): Promise<MacroscopiaResult> {
    const { data } = await api.post('/api/macroscopia', dados);
    return data;
  },

  // --- Processamento Técnico ---
  async pendenciasProcessamento(): Promise<CasseteFila[]> {
    const { data } = await api.get('/api/processamento/pendencias');
    return data;
  },
  async iniciarLote(dados: { cassete_ids: string[]; observacoes?: string; responsavel?: string }): Promise<{ lote: { id: string }; total_cassetes: number }> {
    const { data } = await api.post('/api/processamento/lote', dados);
    return data;
  },
  async concluirLote(loteId: string, dados: { observacoes?: string }): Promise<{ lote: { id: string }; blocos_gerados: number; blocos: BlocoOut[] }> {
    const { data } = await api.post(`/api/processamento/lote/${loteId}/concluir`, dados);
    return data;
  },
  async gerarLaminas(blocoId: string, dados: { quantidade: number; coloracao: string }): Promise<{ bloco_id: string; codigo_bloco: string; laminas: unknown[]; etiquetas: unknown[] }> {
    const { data } = await api.post(`/api/processamento/blocos/${blocoId}/laminas`, dados);
    return data;
  },
};
