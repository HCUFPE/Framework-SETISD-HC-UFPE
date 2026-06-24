import api from './api';

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

export const exameService = {
  async dashboard(): Promise<DashboardExame[]> {
    const { data } = await api.get('/api/exames/dashboard');
    return data;
  },
  async criar(dados: ExameCreate) {
    const { data } = await api.post('/api/exames', dados);
    return data;
  },
};
