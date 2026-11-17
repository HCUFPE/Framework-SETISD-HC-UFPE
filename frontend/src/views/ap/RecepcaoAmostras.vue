<template>
  <div class="space-y-6">
    <p class="text-sm text-gray-600">Leia a etiqueta do AGHU no frasco, confira o material e confirme a entrada.</p>

    <Card v-if="recepcao.passo > 0">
      <Stepper :steps="passos" :current="recepcao.passo" />
    </Card>

    <PassoLeitura v-if="recepcao.passo === 0" ref="passoLeitura" @devolvido="aposDevolucao" />
    <PassoConferencia v-else-if="recepcao.passo === 1" :key="recepcao.solicitacao?.codigoSolicitacao" @devolvido="aposDevolucao" />
    <PassoResultado v-else @proxima="receberProxima" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue';
import Card from '../../components/Card.vue';
import Stepper from '../../components/Stepper.vue';
import PassoConferencia from '../../components/ap/recepcao/PassoConferencia.vue';
import PassoLeitura from '../../components/ap/recepcao/PassoLeitura.vue';
import PassoResultado from '../../components/ap/recepcao/PassoResultado.vue';
import { PASSOS_RECEPCAO, useRecepcaoStore } from '../../stores/recepcao';

const recepcao = useRecepcaoStore();
const passos = PASSOS_RECEPCAO.map((label) => ({ label }));
const passoLeitura = ref<InstanceType<typeof PassoLeitura> | null>(null);

/** Após a devolução na recepção, nenhum caso é criado e a tela volta ao passo 1. */
const aposDevolucao = () => recepcao.reiniciar();

const receberProxima = () => recepcao.reiniciar();

/**
 * Todo reinício (menu, "Receber próxima", devolução) leva à tela inicial:
 * recarrega a fila e devolve o foco ao campo de leitura limpo.
 */
watch(
  () => recepcao.reinicios,
  async () => {
    await nextTick();
    passoLeitura.value?.limparEFocar();
    await recepcao.carregarPendentes();
  },
);

onMounted(() => {
  recepcao.carregarPendentes();
});
</script>
