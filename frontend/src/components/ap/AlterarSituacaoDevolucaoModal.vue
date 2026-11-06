<template>
  <Modal :show="show" size="md" :close-on-backdrop="!salvando" @close="fechar">
    <template #header>Alterar situação da devolução</template>

    <form v-if="devolucao" id="form-situacao-devolucao" novalidate class="space-y-4" @submit.prevent="salvar">
      <dl class="grid gap-3 rounded-md bg-gray-50 px-4 py-3 text-sm sm:grid-cols-2">
        <div>
          <dt class="text-xs font-bold uppercase text-gray-500">Natureza</dt>
          <dd>{{ devolucao.rejeicaoNaRecepcao ? 'Rejeição na recepção' : 'Devolução de caso' }}</dd>
        </div>
        <div>
          <dt class="text-xs font-bold uppercase text-gray-500">{{ devolucao.casoNumero ? 'Caso' : 'Solicitação' }}</dt>
          <dd class="tabular-nums">
            {{ devolucao.casoNumero ?? (devolucao.solicitacaoCodigo ? `AGHU ${devolucao.solicitacaoCodigo}` : 'Sem etiqueta do AGHU') }}
          </dd>
        </div>
        <div>
          <dt class="text-xs font-bold uppercase text-gray-500">Tipo</dt>
          <dd>{{ TIPOS_NAO_CONFORMIDADE[devolucao.naoConformidade.tipo] }}</dd>
        </div>
        <div>
          <dt class="text-xs font-bold uppercase text-gray-500">Situação atual</dt>
          <dd>
            <Badge :variant="SITUACOES_DEVOLUCAO[devolucao.situacao].variante" size="sm">
              {{ SITUACOES_DEVOLUCAO[devolucao.situacao].rotulo }}
            </Badge>
          </dd>
        </div>
      </dl>

      <fieldset>
        <legend class="form-label">Nova situação <span class="text-paper-danger">*</span></legend>
        <div class="space-y-2" role="radiogroup">
          <label
            v-for="(info, codigo) in SITUACOES_DEVOLUCAO"
            :key="codigo"
            :class="situacao === codigo ? 'border-paper-primary bg-paper-primary-soft text-paper-primary-strong' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'"
            class="relative flex cursor-pointer items-center gap-3 rounded-md border px-4 py-2.5 text-sm font-semibold transition active:bg-gray-100 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-paper-primary"
          >
            <input v-model="situacao" type="radio" name="situacao-devolucao" :value="codigo" class="h-4 w-4 accent-paper-primary" />
            {{ info.rotulo }}
            <span v-if="codigo === devolucao.situacao" class="ml-auto text-xs font-normal text-gray-500">atual</span>
          </label>
        </div>
      </fieldset>
    </form>

    <template #footer>
      <Button variant="secondary" :disabled="salvando" @click="fechar">Cancelar</Button>
      <Button type="submit" form="form-situacao-devolucao" :loading="salvando" :disabled="!alterou">Salvar</Button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useToast } from 'vue-toastification';
import Badge from '../Badge.vue';
import Button from '../Button.vue';
import Modal from '../Modal.vue';
import { SITUACOES_DEVOLUCAO, TIPOS_NAO_CONFORMIDADE } from '../../constants/ap';
import { mensagemDeErro } from '../../services/ap';
import { useDevolucoesStore } from '../../stores/devolucoes';
import type { DevolucaoDetalhada, SituacaoDevolucao } from '../../types/ap';

const props = defineProps<{ show: boolean; devolucao: DevolucaoDetalhada | null }>();
const emit = defineEmits<{ (e: 'close'): void; (e: 'alterada', devolucao: DevolucaoDetalhada): void }>();

const toast = useToast();
const store = useDevolucoesStore();
const situacao = ref<SituacaoDevolucao | null>(null);
const salvando = ref(false);

/** Só permite salvar quando a situação escolhida difere da atual. */
const alterou = computed(() => !!props.devolucao && !!situacao.value && situacao.value !== props.devolucao.situacao);

/** A cada abertura, parte da situação atual. */
watch(
  () => [props.show, props.devolucao?.id] as const,
  ([aberto]) => {
    if (aberto) situacao.value = props.devolucao?.situacao ?? null;
  },
  { immediate: true },
);

const fechar = () => {
  if (!salvando.value) emit('close');
};

/** Grava a nova situação (auditada pelo serviço) e fecha o modal. */
const salvar = async () => {
  if (!props.devolucao || !situacao.value || !alterou.value) return;
  salvando.value = true;
  try {
    const atualizada = await store.atualizarSituacao(props.devolucao.id, situacao.value);
    toast.success(`Situação atualizada para "${SITUACOES_DEVOLUCAO[atualizada.situacao].rotulo}".`);
    emit('alterada', atualizada);
  } catch (erro) {
    toast.error(mensagemDeErro(erro, 'Não foi possível atualizar a situação.'));
  } finally {
    salvando.value = false;
  }
};
</script>
