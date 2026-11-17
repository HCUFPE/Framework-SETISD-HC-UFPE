/**
 * "Banco" em memória do mock do Sistema AP.
 *
 * Usado apenas pelas implementações mock dos serviços (`services/ap/mock`). Os dados voltam à
 * carga inicial ao recarregar a página.
 *
 * - Fonte "mock": começa com o seed fictício (solicitações, casos, devoluções).
 * - Fonte "api": começa vazio e recebe só as solicitações do CSV/backend; casos, devoluções e
 *   não conformidades são apenas os criados na sessão. Se o backend falhar, usa o seed como
 *   dados de demonstração.
 */
import { fonteSolicitacoes } from '../../services/ap/http/fonte';
import type { SolicitacaoAghu } from '../../types/ap';
import { criarCargaInicial, type MockDb } from './seed';

/** Banco sem nenhum dado (modo "api", antes da carga do backend). */
function criarCargaVazia(): MockDb {
  return {
    solicitacoes: [],
    casos: [],
    conferencias: [],
    naoConformidades: [],
    devolucoes: [],
    auditoria: [],
    aghuDisponivel: true,
    sequencias: { historico: 0, conferencia: 0, naoConformidade: 0, devolucao: 0, auditoria: 0 },
  };
}

/** Indica que o banco está com o seed de demonstração por falha do backend (modo "api"). */
let emDemonstracao = false;

/** Carga inicial conforme a fonte configurada. */
function cargaPadrao(): MockDb {
  return fonteSolicitacoes() === 'api' && !emDemonstracao ? criarCargaVazia() : criarCargaInicial(new Date());
}

export let db: MockDb = cargaPadrao();

/** Última carga de solicitações vinda do backend (modo híbrido), para reaplicar no reinício. */
let solicitacoesExternas: SolicitacaoAghu[] | null = null;

/**
 * Substitui as solicitações AGUARDANDO_RECEBIMENTO do banco pelas vindas do backend.
 *
 * Mantém os exames RECEBIDA e DEVOLVIDA já existentes (os do seed, ligados a casos e devoluções do
 * mock, e os do backend já recebidos/devolvidos nesta sessão) e não reinsere como pendente um exame
 * (código + sigla) que já esteja no banco.
 */
export function aplicarSolicitacoesExternas(lista: SolicitacaoAghu[]): void {
  // Saindo da demonstração: descarta o seed para ficar só com os dados do backend.
  if (emDemonstracao) {
    emDemonstracao = false;
    db = criarCargaVazia();
  }
  solicitacoesExternas = structuredClone(lista);
  const mantidas = db.solicitacoes.filter((s) => s.situacaoRecepcao !== 'AGUARDANDO_RECEBIMENTO');
  const ids = new Set(mantidas.map((s) => s.id));
  const novas = structuredClone(lista).filter((s) => !ids.has(s.id));
  db.solicitacoes = [...mantidas, ...novas];
}

/** Recria a carga inicial e reaplica a última carga do backend, se houver. */
export function reiniciarDb(): void {
  db = cargaPadrao();
  if (solicitacoesExternas) aplicarSolicitacoesExternas(solicitacoesExternas);
}

/**
 * Falha na carga do backend (modo "api"): passa a exibir o seed como dados de demonstração.
 * Só troca o banco na primeira falha, para não apagar o que foi feito na demonstração.
 */
export function usarDadosDeDemonstracao(): void {
  if (emDemonstracao) return;
  emDemonstracao = true;
  solicitacoesExternas = null;
  db = criarCargaInicial(new Date());
}

/** Próximo identificador numérico da sequência informada. */
export function proximoId(sequencia: keyof MockDb['sequencias']): number {
  db.sequencias[sequencia] += 1;
  return db.sequencias[sequencia];
}

/** Simula indisponibilidade (ou retorno) do AGHU. */
export function definirAghuDisponivel(disponivel: boolean): void {
  db.aghuDisponivel = disponivel;
}
