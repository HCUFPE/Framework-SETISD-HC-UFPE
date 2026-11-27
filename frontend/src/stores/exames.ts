import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../services/api';
import { executar } from '../services/requisicao';
import type {
  IAtualizarStatusRequest,
  IBuscaAghuParams,
  IFiltrosFila,
  IItemFila,
  IItemFilaDetalhe,
  ISolicitacaoAghu,
  IVincularSolicitacaoRequest,
} from '../types/exames';

/** Remove valores vazios (e flags false) para não enviar query params sem efeito. */
function semVazios(params: object): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(params)
      .map(([chave, valor]) => [chave, typeof valor === 'string' ? valor.trim() : valor])
      .filter(([, valor]) => valor !== undefined && valor !== null && valor !== '' && valor !== false),
  );
}

/** Fila de exames (/api/exames): listagem paginada, detalhe, status, busca ativa e vínculo. */
export const useExamesStore = defineStore('exames', () => {
  const itens = ref<IItemFila[]>([]);
  const total = ref(0);
  const carregando = ref(false);
  const erro = ref<string | null>(null);

  const detalhe = ref<IItemFilaDetalhe | null>(null);
  const carregandoDetalhe = ref(false);
  const erroDetalhe = ref<string | null>(null);

  const salvando = ref(false);
  const erroAcao = ref<string | null>(null);

  const resultadosAghu = ref<ISolicitacaoAghu[]>([]);
  const buscandoAghu = ref(false);
  const erroAghu = ref<string | null>(null);

  /** Carrega uma página da fila na ordem da API; o total vem do header X-Total-Count. */
  async function carregarFila(filtros: IFiltrosFila, limit: number, offset: number) {
    const resultado = await executar(carregando, erro, async () => {
      const resposta = await api.get<IItemFila[]>('/api/exames/fila', {
        params: semVazios({ ...filtros, limit, offset }),
      });
      itens.value = resposta.data;
      total.value = Number(resposta.headers['x-total-count'] ?? resposta.data.length);
      return resposta.data;
    });
    if (resultado === null) {
      itens.value = [];
      total.value = 0;
    }
    return resultado;
  }

  /** Detalhe com outros exames do prontuário, todos os alertas e orientações de preparo. */
  async function carregarDetalhe(id: number) {
    detalhe.value = null;
    return executar(carregandoDetalhe, erroDetalhe, async () => {
      detalhe.value = (await api.get<IItemFilaDetalhe>(`/api/exames/fila/${id}`)).data;
      return detalhe.value;
    });
  }

  /** Transição de status operacional (auditada no backend). */
  async function atualizarStatus(id: number, corpo: IAtualizarStatusRequest) {
    return executar(salvando, erroAcao, async () =>
      (await api.patch<IItemFilaDetalhe>(`/api/exames/fila/${id}/status`, corpo)).data,
    );
  }

  /** Busca ativa somente-leitura no AGHU (prontuário, solicitação ou nome). */
  async function buscarAghu(params: IBuscaAghuParams) {
    resultadosAghu.value = [];
    return executar(buscandoAghu, erroAghu, async () => {
      resultadosAghu.value = (
        await api.get<ISolicitacaoAghu[]>('/api/exames/aghu/buscar', { params: semVazios(params) })
      ).data;
      return resultadosAghu.value;
    });
  }

  /** Vincula ao item a solicitação correta encontrada no AGHU. */
  async function vincularSolicitacao(id: number, corpo: IVincularSolicitacaoRequest) {
    return executar(salvando, erroAcao, async () =>
      (await api.patch<IItemFilaDetalhe>(`/api/exames/fila/${id}/vincular-solicitacao`, corpo)).data,
    );
  }

  return {
    itens,
    total,
    carregando,
    erro,
    detalhe,
    carregandoDetalhe,
    erroDetalhe,
    salvando,
    erroAcao,
    resultadosAghu,
    buscandoAghu,
    erroAghu,
    carregarFila,
    carregarDetalhe,
    atualizarStatus,
    buscarAghu,
    vincularSolicitacao,
  };
});
