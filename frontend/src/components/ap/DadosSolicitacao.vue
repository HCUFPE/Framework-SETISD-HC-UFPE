<template>
  <div>
    <p class="mb-3 inline-flex items-center gap-1.5 rounded-full bg-paper-info-soft px-3 py-1 text-xs font-bold text-paper-info-strong">
      <LockClosedIcon class="h-3.5 w-3.5" aria-hidden="true" />
      Origem: AGHU · somente leitura
    </p>

    <dl class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="campo in campos" :key="campo.rotulo" :class="campo.largo ? 'sm:col-span-2' : ''" class="campo-aghu">
        <dt>{{ campo.rotulo }}</dt>
        <dd>{{ campo.valor }}</dd>
      </div>
    </dl>

    <div class="mt-4 grid gap-3 lg:grid-cols-2">
      <div class="rounded-lg border border-paper-info/40 bg-paper-info-soft p-4">
        <p class="flex items-center gap-2 text-xs font-bold uppercase text-paper-info-strong">
          <BeakerIcon class="h-4 w-4" aria-hidden="true" /> Descrição do material
        </p>
        <p class="mt-1 text-lg font-extrabold text-gray-900">{{ solicitacao.descricaoMaterial }}</p>
      </div>
      <div class="rounded-lg border border-paper-info/40 bg-paper-info-soft p-4">
        <p class="flex items-center gap-2 text-xs font-bold uppercase text-paper-info-strong">
          <ClipboardDocumentListIcon class="h-4 w-4" aria-hidden="true" /> Informações clínicas
        </p>
        <p class="mt-1 text-sm text-gray-800">{{ solicitacao.informacoesClinicas || 'Não informadas.' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BeakerIcon, ClipboardDocumentListIcon, LockClosedIcon } from '@heroicons/vue/24/outline';
import { ORIGENS } from '../../constants/ap';
import { calcularIdade, formatarData, formatarDataHora } from '../../helpers/formato';
import type { SolicitacaoAghu } from '../../types/ap';

/** Dados da solicitação AGHU exibidos sem edição (conferência e aba "Solicitação AGHU"). */
const props = defineProps<{ solicitacao: SolicitacaoAghu }>();

const campos = computed(() => {
  const s = props.solicitacao;
  return [
    { rotulo: 'Nº da solicitação', valor: s.codigoSolicitacao },
    { rotulo: 'Prontuário', valor: s.prontuario },
    { rotulo: 'Nome do paciente', valor: s.nomePaciente, largo: true },
    { rotulo: 'Nascimento e idade', valor: `${formatarData(s.dataNascimento)} · ${calcularIdade(s.dataNascimento)} anos` },
    { rotulo: 'Sexo', valor: s.sexo },
    { rotulo: 'Origem', valor: ORIGENS[s.origem] },
    { rotulo: 'Data da solicitação', valor: formatarDataHora(s.dataSolicitacao) },
    { rotulo: 'Unidade solicitante', valor: s.unidade, largo: true },
    { rotulo: 'Especialidade', valor: s.especialidade },
    { rotulo: 'Médico solicitante', valor: s.nomeSolicitante },
    { rotulo: 'Exame', valor: `${s.nomeExame} (${s.siglaExame})`, largo: true },
    { rotulo: 'Status no AGHU', valor: s.statusAghuDescricao },
  ];
});
</script>

<style scoped>
.campo-aghu {
  border-radius: 0.375rem;
  border: 1px solid color-mix(in srgb, var(--color-paper-info) 30%, transparent);
  background: color-mix(in srgb, var(--color-paper-info-soft) 60%, white);
  padding: 0.5rem 0.75rem;
}
.campo-aghu dt {
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-paper-info-strong);
}
.campo-aghu dd {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-gray-800);
}
</style>
