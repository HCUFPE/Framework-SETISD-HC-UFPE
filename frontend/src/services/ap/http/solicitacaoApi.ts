/**
 * Acesso HTTP às solicitações do AGHU expostas pelo backend (`GET /api/solicitacoes`).
 *
 * Usa o `api` de `services/api.ts`, preservando os interceptadores (token e refresh).
 */
import api from '../../api';
import { EXAMES_AGHU, ORIGENS } from '../../../constants/ap';
import { chaveExame, limparTextoAghu, ordenarAmostras, resumirExamesDoGrupo } from '../../../helpers/aghu';
import type { OrigemAtendimento, SolicitacaoAghu, TipoExame } from '../../../types/ap';

export { fonteSolicitacoes, type FonteSolicitacoes } from './fonte';

const LIMITE_PADRAO = 200;
const LIMITE_MAXIMO = 1000;

/** Registro como devolvido pelo backend: uma linha por amostra (camelCase, campos podem vir nulos). */
export interface SolicitacaoApiDto {
  id: string;
  codigoSolicitacao: string;
  numeroAmostra: string;
  prontuario: string | null;
  nomePaciente: string | null;
  dataNascimento: string | null;
  origem: string | null;
  unidade: string | null;
  especialidade: string | null;
  dataSolicitacao: string | null;
  siglaExame: string | null;
  nomeExame: string | null;
  tipoExameSugerido: TipoExame;
  descricaoMaterial: string | null;
  informacoesClinicas: string | null;
  statusAghuDescricao: string | null;
  codStatusItem?: string | null;
  codigoLab?: string | null;
  convenio?: string | null;
}

/** Limite configurado em `VITE_AP_SOLICITACOES_LIMITE`, restrito a 1..1000. */
function limiteConfigurado(): number {
  const valor = Number.parseInt(import.meta.env.VITE_AP_SOLICITACOES_LIMITE ?? '', 10);
  if (!Number.isFinite(valor) || valor < 1) return LIMITE_PADRAO;
  return Math.min(valor, LIMITE_MAXIMO);
}

/** Origem reconhecida pelo SAP ou null (nula/desconhecida). */
function paraOrigem(origem: string | null): OrigemAtendimento | null {
  return origem && origem in ORIGENS ? (origem as OrigemAtendimento) : null;
}

/** Só a data (AAAA-MM-DD): o AGHU não fornece hora da solicitação. */
function soData(valor: string | null): string {
  return (valor ?? '').slice(0, 10);
}

/**
 * Agrupa as linhas do backend (uma por amostra) por solicitação e tipo de exame:
 * mesmo `codigoSolicitacao` + mesmo tipo do SAP → um `SolicitacaoAghu` com suas amostras.
 */
export function agruparSolicitacoes(dtos: SolicitacaoApiDto[]): SolicitacaoAghu[] {
  const grupos = new Map<string, SolicitacaoAghu>();
  for (const dto of dtos) {
    const codigo = limparTextoAghu(dto.codigoSolicitacao);
    const sigla = limparTextoAghu(dto.siglaExame).toUpperCase();
    const id = chaveExame(codigo, dto.tipoExameSugerido);
    let grupo = grupos.get(id);
    if (!grupo) {
      grupo = {
        id,
        codigoSolicitacao: codigo,
        prontuario: limparTextoAghu(dto.prontuario),
        nomePaciente: limparTextoAghu(dto.nomePaciente),
        dataNascimento: soData(dto.dataNascimento),
        origem: paraOrigem(dto.origem),
        unidade: limparTextoAghu(dto.unidade),
        especialidade: limparTextoAghu(dto.especialidade),
        dataSolicitacao: soData(dto.dataSolicitacao),
        siglaExame: '',
        nomeExame: '',
        tipoExameSugerido: dto.tipoExameSugerido,
        informacoesClinicas: (dto.informacoesClinicas ?? '').trim(),
        amostras: [],
        situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO',
      };
      grupos.set(id, grupo);
    }
    grupo.amostras.push({
      numeroAmostra: limparTextoAghu(dto.numeroAmostra),
      siglaExame: sigla,
      nomeExame: limparTextoAghu(dto.nomeExame) || EXAMES_AGHU[sigla]?.nome || sigla,
      descricaoMaterial: limparTextoAghu(dto.descricaoMaterial),
      codStatusItem: limparTextoAghu(dto.codStatusItem).toUpperCase(),
      statusItemDescricao: limparTextoAghu(dto.statusAghuDescricao),
    });
  }
  return [...grupos.values()].map((g) => resumirExamesDoGrupo({ ...g, amostras: ordenarAmostras(g.amostras) }));
}

/** Busca no backend as solicitações aguardando recebimento, já agrupadas por exame. */
export async function buscarSolicitacoesPendentes(): Promise<SolicitacaoAghu[]> {
  const params: Record<string, string | number> = { limite: limiteConfigurado() };
  const dataInicio = (import.meta.env.VITE_AP_SOLICITACOES_DATA_INICIO ?? '').trim();
  if (dataInicio) params.data_inicio = dataInicio;

  const { data } = await api.get<SolicitacaoApiDto[]>('/api/solicitacoes', { params });
  return agruparSolicitacoes(data);
}
