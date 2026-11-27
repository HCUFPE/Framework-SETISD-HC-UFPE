<template>
  <div class="space-y-6">
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
import { useRoute } from 'vue-router';
import { useToast } from 'vue-toastification';
import Card from '../../components/Card.vue';
import Stepper from '../../components/Stepper.vue';
import PassoConferencia from '../../components/ap/recepcao/PassoConferencia.vue';
import PassoLeitura from '../../components/ap/recepcao/PassoLeitura.vue';
import PassoResultado from '../../components/ap/recepcao/PassoResultado.vue';
import { PASSOS_RECEPCAO, useRecepcaoStore } from '../../stores/recepcao';
import { mensagemDeErro } from '../../services/ap';

const recepcao = useRecepcaoStore();
const route = useRoute();
const toast = useToast();
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

onMounted(async () => {
  await recepcao.carregarPendentes();
  const codigo = route.query.solicitacao;
  if (typeof codigo === 'string' && codigo.trim()) {
    try {
      await recepcao.lerCodigo(codigo);
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
    }
  }
});
</script>
