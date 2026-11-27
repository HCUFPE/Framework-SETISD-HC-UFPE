import axios from 'axios';
import type { Ref } from 'vue';

/** Mensagem do padrão {"detail": "..."} do backend, ou a mensagem padrão. */
export function mensagemErro(erro: unknown, padrao = 'Falha na comunicação com o servidor.'): string {
  if (axios.isAxiosError(erro)) {
    const detail = erro.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
  }
  return padrao;
}

/** Executa a chamada controlando loading e erro; devolve null em caso de falha. */
export async function executar<T>(
  carregando: Ref<boolean>,
  erro: Ref<string | null>,
  chamada: () => Promise<T>,
): Promise<T | null> {
  carregando.value = true;
  erro.value = null;
  try {
    return await chamada();
  } catch (e) {
    erro.value = mensagemErro(e);
    return null;
  } finally {
    carregando.value = false;
  }
}
