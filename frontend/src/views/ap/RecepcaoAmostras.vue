<template>
  <div class="space-y-6">
    <p class="text-sm text-gray-600">Leia a etiqueta do AGHU no frasco, confira o material e confirme a entrada.</p>

    <Card v-if="recepcao.passo > 0">
      <Stepper :steps="passos" :current="recepcao.passo" />
    </Card>

    <PassoLeitura v-if="recepcao.passo === 0" ref="passoLeitura" @sem-etiqueta="abrirNaoConformidade({ tipo: 'SEM_ETIQUETA' })" />
    <PassoConferencia v-else-if="recepcao.passo === 1" @nao-conformidade="abrirNaoConformidadeConferencia" />
    <PassoComplemento v-else-if="recepcao.passo === 2" :key="recepcao.solicitacao?.codigoSolicitacao" />
    <PassoResultado v-else @proxima="receberProxima" />

    <NaoConformidadeModal
      :show="contextoNc !== null"
      :contexto="contextoNc"
      :solicitacao="contextoNc?.tipo === 'SOLICITACAO' ? recepcao.solicitacao : null"
      @close="contextoNc = null"
      @registrado="aposDevolucao"
    />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue';
import Card from '../../components/Card.vue';
import Stepper from '../../components/Stepper.vue';
import NaoConformidadeModal from '../../components/ap/NaoConformidadeModal.vue';
import PassoComplemento from '../../components/ap/recepcao/PassoComplemento.vue';
import PassoConferencia from '../../components/ap/recepcao/PassoConferencia.vue';
import PassoLeitura from '../../components/ap/recepcao/PassoLeitura.vue';
import PassoResultado from '../../components/ap/recepcao/PassoResultado.vue';
import { PASSOS_RECEPCAO, useRecepcaoStore } from '../../stores/recepcao';
import type { ContextoNaoConformidade } from '../../types/ap';

const recepcao = useRecepcaoStore();
const passos = PASSOS_RECEPCAO.map((label) => ({ label }));
const contextoNc = ref<ContextoNaoConformidade | null>(null);
const passoLeitura = ref<InstanceType<typeof PassoLeitura> | null>(null);

const abrirNaoConformidade = (contexto: ContextoNaoConformidade) => {
  contextoNc.value = contexto;
};

/** Não conformidade a partir da conferência: guarda os itens no estado em que estavam. */
const abrirNaoConformidadeConferencia = () => {
  if (!recepcao.solicitacao) return;
  abrirNaoConformidade({
    tipo: 'SOLICITACAO',
    solicitacaoCodigo: recepcao.solicitacao.codigoSolicitacao,
    conferencia: { ...recepcao.conferencia },
  });
};

/** Após a devolução na recepção, nenhum caso é criado e a tela volta ao passo 1. */
const aposDevolucao = () => recepcao.reiniciar();

const receberProxima = () => recepcao.reiniciar();

/**
 * Todo reinício (menu, "Receber próxima", devolução) leva à tela inicial:
 * fecha o modal, recarrega a fila e devolve o foco ao campo de leitura limpo.
 */
watch(
  () => recepcao.reinicios,
  async () => {
    contextoNc.value = null;
    await nextTick();
    passoLeitura.value?.limparEFocar();
    await recepcao.carregarPendentes();
  },
);

onMounted(() => {
  recepcao.carregarPendentes();
});
</script>
