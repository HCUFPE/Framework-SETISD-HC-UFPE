<template>
  <Modal :show="show" size="md" :close-on-backdrop="false" @close="fechar">
    <template #header>Cancelar caso {{ caso?.numeroInterno }}</template>

    <form v-if="passo === 1" id="form-cancelamento" novalidate class="space-y-3" @submit.prevent="continuar">
      <p class="text-sm text-gray-600">
        O cancelamento encerra o caso e o retira das filas de trabalho. O caso, os materiais e o histórico continuam
        disponíveis para consulta e auditoria.
      </p>
      <div class="form-group mb-0">
        <label for="cancelamento-motivo" class="form-label">Motivo do cancelamento <span class="text-paper-danger">*</span></label>
        <textarea
          id="cancelamento-motivo"
          v-model="motivo"
          rows="3"
          class="form-control"
          :aria-invalid="erro ? 'true' : undefined"
          placeholder="Ex.: solicitação duplicada no AGHU"
          @input="erro = ''"
        ></textarea>
        <p v-if="erro" class="mt-1 text-sm text-paper-danger-strong">{{ erro }}</p>
      </div>
    </form>

    <div v-else class="space-y-3">
      <Alert variant="danger" title="Confirme o cancelamento">
        O caso <strong>{{ caso?.numeroInterno }}</strong> passará a "Cancelado" e ficará somente leitura.
      </Alert>
      <p class="text-sm"><span class="font-bold">Motivo:</span> {{ motivo.trim() }}</p>
    </div>

    <template #footer>
      <template v-if="passo === 1">
        <Button variant="secondary" @click="fechar">Voltar</Button>
        <Button type="submit" form="form-cancelamento" variant="danger">Continuar</Button>
      </template>
      <template v-else>
        <Button variant="secondary" :disabled="salvando" @click="passo = 1">Revisar motivo</Button>
        <Button variant="danger" :loading="salvando" @click="confirmar">Confirmar cancelamento</Button>
      </template>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useToast } from 'vue-toastification';
import Alert from '../../Alert.vue';
import Button from '../../Button.vue';
import Modal from '../../Modal.vue';
import { mensagemDeErro } from '../../../services/ap';
import { useCasosStore } from '../../../stores/casos';
import type { CasoAp } from '../../../types/ap';

const props = defineProps<{ show: boolean; caso: CasoAp | null }>();
const emit = defineEmits<{ (e: 'close'): void; (e: 'cancelado', caso: CasoAp): void }>();

const toast = useToast();
const casosStore = useCasosStore();
const passo = ref<1 | 2>(1);
const motivo = ref('');
const erro = ref('');
const salvando = ref(false);

/** Exige o motivo antes da confirmação explícita. */
const continuar = () => {
  if (!motivo.value.trim()) {
    erro.value = 'Informe o motivo do cancelamento.';
    return;
  }
  passo.value = 2;
};

const confirmar = async () => {
  if (!props.caso) return;
  salvando.value = true;
  try {
    const caso = await casosStore.cancelar(props.caso.numeroInterno, motivo.value);
    toast.success(`Caso ${caso.numeroInterno} cancelado.`);
    emit('cancelado', caso);
  } catch (e) {
    toast.error(mensagemDeErro(e, 'Não foi possível cancelar o caso.'));
  } finally {
    salvando.value = false;
  }
};

const fechar = () => {
  if (!salvando.value) emit('close');
};

watch(
  () => props.show,
  (aberto) => {
    if (!aberto) return;
    passo.value = 1;
    motivo.value = '';
    erro.value = '';
  },
);
</script>
