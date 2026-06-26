import type { Sector } from '../constants/sectors';

export interface MockUser {
  username: string;
  password: string;
  fullName: string;
  setor: Sector;
  groups: string[];
  title?: string;
  employeeNumber?: string;
}

export const MOCK_USERS: MockUser[] = [
  { username: 'recepcao', password: '123456', fullName: 'Ana Souza', setor: 'recepcao', groups: [] },
  { username: 'macroscopia', password: '123456', fullName: 'Carlos Lima', setor: 'macroscopia', groups: [] },
  { username: 'microscopia', password: '123456', fullName: 'Beatriz Andrade', setor: 'microscopia', groups: [] },
  { username: 'tecnico', password: '123456', fullName: 'Rafael Costa', setor: 'processamento_tecnico', groups: [] },
  {
    username: 'admin',
    password: '123456',
    fullName: 'Admin do Sistema',
    setor: 'admin',
    groups: [],
    title: 'Administrador do Sistema',
    employeeNumber: '0001-TI',
  },
];