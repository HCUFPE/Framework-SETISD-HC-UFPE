import { defineStore } from 'pinia';
import { ref } from 'vue';
import { alternarSituacaoEquipe, consultarAd, listarEquipe, salvarUsuarioEquipe } from '../services/sae';
import type { AdUser, Perfil, UsuarioEquipe } from '../types/sae';
import { useAuthStore } from './auth';

export const useEquipeStore = defineStore('equipe', () => {
  const usuarios = ref<UsuarioEquipe[]>([]);
  const login = ref('');
  const adUser = ref<AdUser | null>(null);
  const perfil = ref<Perfil>('OPERADOR');
  const lotacao = ref('');
  const carregando = ref(false);
  const erro = ref('');
  const mensagem = ref('');

  async function carregar(): Promise<void> {
    carregando.value = true;
    erro.value = '';
    try {
      usuarios.value = await listarEquipe();
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível carregar a equipe.';
    } finally {
      carregando.value = false;
    }
  }

  async function consultar(): Promise<void> {
    erro.value = '';
    mensagem.value = '';
    try {
      adUser.value = await consultarAd(login.value.trim());
      if (adUser.value.exists) {
        lotacao.value = adUser.value.department;
        mensagem.value = 'Usuário localizado no Active Directory.';
      } else {
        mensagem.value = 'Usuário não encontrado no Active Directory.';
      }
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Falha na consulta ao Active Directory.';
    }
  }

  async function salvar(): Promise<boolean> {
    erro.value = '';
    try {
      if (!adUser.value?.exists) throw new Error('Consulte o AD antes de cadastrar o usuário.');
      const autor = useAuthStore().user?.displayName?.[0] ?? 'Área Gestora';
      usuarios.value = await salvarUsuarioEquipe(
        {
          login: adUser.value.username,
          nome: adUser.value.displayName,
          email: adUser.value.email,
          lotacao: lotacao.value || adUser.value.department,
          perfil: perfil.value,
        },
        autor,
      );
      login.value = '';
      adUser.value = null;
      lotacao.value = '';
      mensagem.value = 'Usuário cadastrado com perfil local.';
      return true;
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível cadastrar o usuário.';
      return false;
    }
  }

  async function alternar(id: string): Promise<void> {
    erro.value = '';
    try {
      const autor = useAuthStore().user?.displayName?.[0] ?? 'Área Gestora';
      usuarios.value = await alternarSituacaoEquipe(id, autor);
    } catch (e) {
      erro.value = e instanceof Error ? e.message : 'Não foi possível alterar a situação do usuário.';
    }
  }

  return {
    usuarios,
    login,
    adUser,
    perfil,
    lotacao,
    carregando,
    erro,
    mensagem,
    carregar,
    consultar,
    salvar,
    alternar,
  };
});
