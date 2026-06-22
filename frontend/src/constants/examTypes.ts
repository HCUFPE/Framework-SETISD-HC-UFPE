export type ExamType = 'HP' | 'IHQ' | 'HPDerm' | 'CCV' | 'CG' | 'RevInt' | 'Congela';

export const EXAM_TYPE_PREFIX: Record<ExamType, string> = {
  HP: 'HP',
  IHQ: 'IH',
  HPDerm: 'HD',
  CCV: 'CV',
  CG: 'CG',
  RevInt: 'RI',
  Congela: 'CO',
};

export const EXAM_TYPE_LABEL: Record<ExamType, string> = {
  HP: 'Histopatológico Geral',
  IHQ: 'Imunohistoquímica',
  HPDerm: 'Histopatológico Dermatológico',
  CCV: 'Citologia Cervicovaginal',
  CG: 'Citologia Geral',
  RevInt: 'Revisão Interna',
  Congela: 'Congelação',
};