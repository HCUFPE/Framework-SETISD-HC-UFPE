export type Sector = 'recepcao' | 'macroscopia' | 'microscopia' | 'processamento_tecnico' | 'congelamento' | 'admin';

export const SECTOR_INFO: Record<Sector, { path: string; label: string }> = {
  recepcao: { path: '/recepcao', label: 'Recepção' },
  macroscopia: { path: '/macroscopia', label: 'Macroscopia' },
  microscopia: { path: '/microscopia', label: 'Microscopia' },
  processamento_tecnico: { path: '/processamento-tecnico', label: 'Processamento Técnico' },
  congelamento: { path: '/congelamento', label: 'Congelamento' },
  admin: { path: '/admin', label: 'TI / Administração' },
};

export const OPERATIONAL_SECTORS: Sector[] = [
  'recepcao',
  'macroscopia',
  'processamento_tecnico',
  'microscopia',
  'congelamento',
];