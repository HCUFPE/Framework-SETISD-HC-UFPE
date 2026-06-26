export type ExamStatus =
  | 'Na Recepção'
  | 'Em Macroscopia'
  | 'Em Processamento'
  | 'Em Microscopia'
  | 'Em Congelamento'
  | 'Revisão Pendente'
  | 'Liberado';

export type BadgeColor = 'gray' | 'blue' | 'purple' | 'orange' | 'green' | 'red';

export const STATUS_COLOR: Record<ExamStatus, BadgeColor> = {
  'Na Recepção': 'gray',
  'Em Macroscopia': 'blue',
  'Em Processamento': 'blue',
  'Em Microscopia': 'blue',
  'Em Congelamento': 'purple',
  'Revisão Pendente': 'orange',
  'Liberado': 'green',
};

export const EXAM_STATUSES: ExamStatus[] = [
  'Na Recepção',
  'Em Macroscopia',
  'Em Processamento',
  'Em Microscopia',
  'Em Congelamento',
  'Revisão Pendente',
  'Liberado',
];