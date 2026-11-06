/**
 * Ponto único de seleção das implementações dos serviços do Sistema AP.
 *
 * Hoje todas são mock. Para integrar com o backend, crie implementações HTTP (usando
 * `services/api.ts`) que respeitem as interfaces de `./types` e troque as atribuições abaixo.
 */
import { db, definirAghuDisponivel, reiniciarDb } from '../../mocks/ap/db';
import { aghuServiceMock } from './mock/aghuServiceMock';
import { casoServiceMock } from './mock/casoServiceMock';
import { naoConformidadeServiceMock } from './mock/naoConformidadeServiceMock';
import { copia, latencia } from './mock/util';
import type { AghuService, AuditoriaService, CasoService, NaoConformidadeService } from './types';

export * from './types';

export const aghuService: AghuService = aghuServiceMock;
export const casoService: CasoService = casoServiceMock;
export const naoConformidadeService: NaoConformidadeService = naoConformidadeServiceMock;
export const auditoriaService: AuditoriaService = {
  async listar() {
    await latencia(100);
    return copia(db.auditoria);
  },
};

/**
 * Em desenvolvimento, expõe os serviços e controles do mock no console do navegador
 * (`window.apMock`), para verificação manual: ex. `apMock.aghuDisponivel(false)`.
 */
if (import.meta.env.DEV && typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).apMock = {
    aghuService,
    casoService,
    naoConformidadeService,
    auditoriaService,
    aghuDisponivel: definirAghuDisponivel,
    reiniciar: reiniciarDb,
  };
}
