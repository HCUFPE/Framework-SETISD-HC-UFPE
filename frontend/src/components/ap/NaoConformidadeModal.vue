<template>
  <!-- Registro de não conformidade e devolução em modal (conferência, sem etiqueta e detalhe do caso). -->
  <Modal :show="show" size="lg" :close-on-backdrop="false" @close="fechar">
    <template #header>
      <span class="flex items-center gap-2">
        <ExclamationTriangleIcon class="h-6 w-6 text-paper-danger" aria-hidden="true" />
        Não conformidade e devolução
      </span>
    </template>

    <!-- Recriado a cada abertura, para começar sempre com o formulário vazio -->
    <NaoConformidadeFormulario
      v-if="show"
      ref="formulario"
      :id-formulario="idFormulario"
      :contexto="contexto"
      :etapa-caso="etapaCaso"
      :exames-devolviveis="examesDevolviveis"
      @registrado="(devolucao) => emit('registrado', devolucao)"
    />

    <template #footer>
      <Button variant="secondary" :disabled="salvando" @click="fechar">Cancelar</Button>
      <Button type="submit" :form="idFormulario" variant="danger" :loading="salvando">
        <ArrowUturnLeftIcon class="h-5 w-5 mr-2" aria-hidden="true" /> Registrar devolução
      </Button>
    </template>
  </Modal>
</template>

<script lang="ts">
/** Contador para ids únicos entre instâncias do modal. */
let instancias = 0;
</script>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ArrowUturnLeftIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import Button from '../Button.vue';
import Modal from '../Modal.vue';
import NaoConformidadeFormulario from './NaoConformidadeFormulario.vue';
import type { ContextoNaoConformidade, DevolucaoDetalhada, EtapaCodigo, SolicitacaoAghu } from '../../types/ap';

withDefaults(
  defineProps<{
    show: boolean;
    contexto: ContextoNaoConformidade;
    /** Etapa atual do caso, quando o registro parte do detalhe. */
    etapaCaso?: EtapaCodigo | null;
    /** Conferência: tipos de exame pendentes que podem ser devolvidos. */
    examesDevolviveis?: SolicitacaoAghu[];
  }>(),
  { etapaCaso: null, examesDevolviveis: () => [] },
);

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'registrado', devolucao: DevolucaoDetalhada): void;
}>();

const idFormulario = `form-nao-conformidade-${++instancias}`;
const formulario = ref<InstanceType<typeof NaoConformidadeFormulario> | null>(null);
const salvando = computed(() => formulario.value?.salvando ?? false);

/** Não fecha enquanto a devolução está sendo registrada. */
const fechar = () => {
  if (!salvando.value) emit('close');
};
</script>
