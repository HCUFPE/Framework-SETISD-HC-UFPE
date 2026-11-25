<template>
  <div class="space-y-5">
    <Card>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-xl font-bold text-paper-text">Critérios de Priorização</h2>
            <p class="text-sm text-gray-500">Alterações criam uma nova versão e exigem justificativa formal (RN-03)</p>
          </div>
          <Button v-if="podeEditar" variant="info" @click="store.adicionar()">Adicionar critério</Button>
        </div>
      </template>

      <p v-if="!podeEditar" class="mb-4 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
        Somente a Área Gestora pode alterar os critérios. Os demais perfis têm acesso somente leitura.
      </p>
      <p v-if="store.erro" class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{ store.erro }}</p>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th class="px-3 py-2">Ordem</th>
              <th class="px-3 py-2">Critério</th>
              <th class="px-3 py-2">Descrição</th>
              <th class="px-3 py-2">Peso (0-100)</th>
              <th class="px-3 py-2">Ativo</th>
              <th class="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="criterio in store.criterios" :key="criterio.id" class="bg-white">
              <td class="px-3 py-2"><input v-model.number="criterio.ordem" type="number" min="1" class="form-control w-20" :disabled="!podeEditar" /></td>
              <td class="px-3 py-2"><input v-model="criterio.nome" class="form-control" :disabled="!podeEditar" /></td>
              <td class="px-3 py-2"><input v-model="criterio.descricao" class="form-control" :disabled="!podeEditar" /></td>
              <td class="px-3 py-2"><input v-model.number="criterio.peso" type="number" min="0" max="100" class="form-control w-24" :disabled="!podeEditar" /></td>
              <td class="px-3 py-2"><input v-model="criterio.ativo" type="checkbox" class="h-5 w-5 accent-paper-primary" :disabled="!podeEditar" /></td>
              <td class="px-3 py-2">
                <Button v-if="podeEditar" variant="danger" @click="store.remover(criterio.id)">Desativar</Button>
              </td>
            </tr>
            <tr v-if="!store.criterios.length">
              <td colspan="6" class="px-3 py-6 text-center text-gray-500">Nenhum critério cadastrado.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="podeEditar" class="mt-5 border-t border-gray-100 pt-4">
        <label class="form-label" for="justificativa-criterios">Justificativa da nova versão</label>
        <textarea id="justificativa-criterios" v-model="store.justificativa" class="form-control" rows="2" placeholder="Descreva o motivo da alteração e quem a solicitou"></textarea>
        <div class="mt-3">
          <Button variant="primary" :loading="store.carregando" @click="salvar">Salvar nova versão</Button>
        </div>
      </div>
    </Card>

    <Card>
      <template #header>
        <h2 class="text-lg font-bold text-paper-text">Histórico de versões</h2>
      </template>
      <ol class="space-y-3">
        <li v-for="versao in store.versoes" :key="versao.numero" class="rounded-lg border border-gray-200 p-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="text-sm font-semibold text-gray-800">Versão {{ versao.numero }}</span>
            <span class="text-xs text-gray-500">{{ formatarDataHora(versao.criadoEm) }} · {{ versao.autor }}</span>
          </div>
          <p class="mt-1 text-sm text-gray-600">{{ versao.justificativa }}</p>
          <p class="mt-1 text-xs text-gray-500">{{ versao.criterios.filter((item) => item.ativo).length }} critério(s) ativo(s)</p>
        </li>
        <li v-if="!store.versoes.length" class="text-sm text-gray-500">Nenhuma versão registrada.</li>
      </ol>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import { useAuthStore } from '../stores/auth';
import { useCriteriosStore } from '../stores/criterios';
import { useSolicitacaoStore } from '../stores/solicitacao';
import { formatarDataHora } from '../utils/format';

const store = useCriteriosStore();
const auth = useAuthStore();
const fila = useSolicitacaoStore();
const toast = useToast();

const podeEditar = computed(() => auth.temPerfil('AREA_GESTORA'));

onMounted(() => { void store.carregar(); });

async function salvar(): Promise<void> {
  const ok = await store.salvar();
  if (ok) {
    toast.success('Nova versão salva. A fila foi recalculada.');
    await fila.carregar();
  }
}
</script>
