<template>
  <div class="space-y-5">
    <Card>
      <template #header>
        <div>
          <h2 class="text-xl font-bold text-paper-text">Equipe e Perfis</h2>
          <p class="text-sm text-gray-500">A conta é autenticada no AD; a autorização é definida pelo perfil local</p>
        </div>
      </template>

      <p v-if="store.erro" class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ store.erro }}</p>
      <p v-if="store.mensagem" class="mb-4 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ store.mensagem }}</p>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div>
          <label class="form-label" for="login-ad">Login de rede</label>
          <div class="flex gap-2">
            <input id="login-ad" v-model="store.login" class="form-control" placeholder="Ex.: ana.operadora" @keyup.enter="store.consultar()" />
            <Button variant="info" @click="store.consultar()">Consultar AD</Button>
          </div>
        </div>
        <div>
          <label class="form-label" for="nome-ad">Nome completo</label>
          <input id="nome-ad" :value="store.adUser?.displayName ?? ''" class="form-control bg-gray-50" readonly />
        </div>
        <div>
          <label class="form-label" for="email-ad">E-mail</label>
          <input id="email-ad" :value="store.adUser?.email ?? ''" class="form-control bg-gray-50" readonly />
        </div>
        <div>
          <label class="form-label" for="perfil-usuario">Perfil local</label>
          <select id="perfil-usuario" v-model="store.perfil" class="form-control">
            <option v-for="perfil in PERFIS" :key="perfil" :value="perfil">{{ ROTULOS_PERFIL[perfil] }}</option>
          </select>
        </div>
      </div>

      <div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div>
          <label class="form-label" for="lotacao">Lotação / setor</label>
          <input id="lotacao" v-model="store.lotacao" class="form-control" />
        </div>
        <div class="flex items-end">
          <Button variant="primary" :disabled="!store.adUser?.exists" :loading="store.carregando" @click="cadastrar">Cadastrar no sistema</Button>
        </div>
      </div>
    </Card>

    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-paper-text">Usuários cadastrados</h2>
      </template>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th class="px-3 py-2">Login</th>
              <th class="px-3 py-2">Nome</th>
              <th class="px-3 py-2">Lotação</th>
              <th class="px-3 py-2">Perfil</th>
              <th class="px-3 py-2">Situação</th>
              <th class="px-3 py-2">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="usuario in store.usuarios" :key="usuario.id" class="bg-white">
              <td class="px-3 py-2 text-gray-700">{{ usuario.login }}</td>
              <td class="px-3 py-2 text-gray-700">{{ usuario.nome }}</td>
              <td class="px-3 py-2 text-gray-600">{{ usuario.lotacao }}</td>
              <td class="px-3 py-2 text-gray-600">{{ ROTULOS_PERFIL[usuario.perfil] }}</td>
              <td class="px-3 py-2">
                <span :class="usuario.ativo ? 'text-emerald-600' : 'text-gray-500'" class="text-xs font-semibold">
                  {{ usuario.ativo ? 'Ativo' : 'Inativo' }}
                </span>
              </td>
              <td class="px-3 py-2">
                <Button :variant="usuario.ativo ? 'danger' : 'success'" @click="store.alternar(usuario.id)">
                  {{ usuario.ativo ? 'Inativar' : 'Ativar' }}
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-paper-text">Trilha de alterações de acesso</h2>
      </template>
      <HistoryTimeline :eventos="auditoria" />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import HistoryTimeline from '../components/HistoryTimeline.vue';
import { listarAuditoria } from '../services/sae';
import { useEquipeStore } from '../stores/equipe';
import { PERFIS, ROTULOS_PERFIL, type EventoHistorico } from '../types/sae';

const store = useEquipeStore();
const toast = useToast();
const auditoria = ref<EventoHistorico[]>([]);

onMounted(async () => {
  await store.carregar();
  auditoria.value = (await listarAuditoria())
    .filter((evento) => ['SEGURANCA', 'CONFIGURACAO'].includes(evento.categoria))
    .slice(0, 10);
});

async function cadastrar(): Promise<void> {
  const ok = await store.salvar();
  if (ok) toast.success('Usuário cadastrado com validação no AD.');
}
</script>
