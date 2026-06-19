export type Sector = 'recepcao' | 'macroscopia' | 'microscopia' | 'processamento_tecnico' | 'admin';

export const SECTOR_INFO: Record<Sector, { path: string; label: string }> = {
  recepcao: { path: '/recepcao', label: 'Recepção' },
  macroscopia: { path: '/macroscopia', label: 'Macroscopia' },
  microscopia: { path: '/microscopia', label: 'Microscopia' },
  processamento_tecnico: { path: '/processamento-tecnico', label: 'Processamento Técnico' },
  admin: { path: '/admin', label: 'Administração' },
};

// Setores "operacionais" (exclui admin) — usado pra listar no menu do admin.
export const OPERATIONAL_SECTORS: Sector[] = ['recepcao', 'macroscopia', 'microscopia', 'processamento_tecnico'];