export type TipoEtiqueta = 'frasco' | 'cassete' | 'bloco' | 'lamina';

export const PRINT_QR_SIZE: Record<TipoEtiqueta, number> = {
  frasco: 90,
  cassete: 36,
  bloco: 50,
  lamina: 30,
};

export const TIPO_LABEL: Record<TipoEtiqueta, string> = {
  frasco: 'Frasco',
  cassete: 'Cassete',
  bloco: 'Bloco de Parafina',
  lamina: 'Lâmina',
};