export interface MockUser {
  username: string;
  password: string;
  fullName: string;
  setor: 'recepcao' | 'macroscopia' | 'microscopia' | 'processamento_tecnico';
  groups: string[];
}

export const MOCK_USERS: MockUser[] = [
  { username: 'recepcao', password: '123456', fullName: 'Ana Souza', setor: 'recepcao', groups: [] },
  { username: 'macroscopia', password: '123456', fullName: 'Carlos Lima', setor: 'macroscopia', groups: [] },
  { username: 'microscopia', password: '123456', fullName: 'Beatriz Andrade', setor: 'microscopia', groups: [] },
  { username: 'tecnico', password: '123456', fullName: 'Rafael Costa', setor: 'processamento_tecnico', groups: [] },
];