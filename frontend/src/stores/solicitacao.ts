import { defineStore } from 'pinia';
import { ref } from 'vue';
import {
  efetivarAgendamento,
  listarFila,
  obterSolicitacao,
  registrarContato,
  validarSolicitacao,
} from '../services/sae';
import type { FiltroFila, ResultadoContato, ResultadoFila, Solicitacao } from '../types/sae';
import { useAuthStore } from './auth';

export const useSolicitacaoStore = defineStore('solicitacao', () => {
  const solicitacoes = ref<Solicitacao[]>([]);
  const selecionada = ref<Solicitacao | null>(null);
  const filtros = ref<FiltroFila>({
    busca: '', status: '', tipoExame: '', unidadeSolicitante: '',
    periodo: 'todos', pagina: 1, porPagina: 20,
  });
  const paginacao = ref<Omit<ResultadoFila, 'itens'>>({
    total: 0, pagina: 1, porPagina: 20, totalPaginas: 1,
  });
  const carregando = ref(false);
  const erro = ref('');

  async function carregar(): Promise<void> {
    carregando.value = true;
    erro.value = '';
    try {
      const resultado = await listarFila(filtros.value);
      solicitacoes.value = resultado.itens;
      paginacao.value = {
        total: resultado.total,
        pagina: resultado.pagina,
        porPagina: resultado.porPagina,
        totalPaginas: resultado.totalPaginas,
      };
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível carregar a fila.';
    } finally {
      carregando.value = false;
    }
  }

  function irParaPagina(pagina: number): void {
    filtros.value.pagina = Math.max(1, pagina);
    void carregar();
  }

  function aoFiltrar(): void {
    filtros.value.pagina = 1;
    void carregar();
  }

  async function abrir(id: string): Promise<void> {
    erro.value = '';
    try {
      selecionada.value = await obterSolicitacao(id);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível abrir a solicitação.';
    }
  }

  function fechar(): void {
    selecionada.value = null;
  }

  async function validar(justificativa: string): Promise<void> {
    if (!selecionada.value) return;
    const autor = useAuthStore().user?.displayName?.[0] ?? 'Operador';
    try {
      await validarSolicitacao(selecionada.value.id, justificativa, autor);
      await Promise.all([carregar(), abrir(selecionada.value.id)]);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível validar a solicitação.';
    }
  }

  async function contatar(resultado: ResultadoContato, observacao: string): Promise<void> {
    if (!selecionada.value) return;
    const autor = useAuthStore().user?.displayName?.[0] ?? 'Operador';
    try {
      await registrarContato(selecionada.value.id, resultado, autor, observacao);
      await Promise.all([carregar(), abrir(selecionada.value.id)]);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível registrar o contato.';
    }
  }

  async function agendar(dataHora: string): Promise<void> {
    if (!selecionada.value) return;
    const autor = useAuthStore().user?.displayName?.[0] ?? 'Operador';
    try {
      await efetivarAgendamento(selecionada.value.id, dataHora, autor);
      await Promise.all([carregar(), abrir(selecionada.value.id)]);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível efetivar o agendamento.';
    }
  }

  return {
    solicitacoes,
    selecionada,
    filtros,
    paginacao,
    carregando,
    erro,
    carregar,
    irParaPagina,
    aoFiltrar,
    abrir,
    fechar,
    validar,
    contatar,
    agendar,
  };
});
