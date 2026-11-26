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

    <!-- Amostras: uma linha por amostra (número, exame, descrição e status no AGHU) -->
    <section class="amostras-aghu mt-4" aria-labelledby="titulo-amostras-aghu">
      <header class="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
        <h3 id="titulo-amostras-aghu" class="flex items-center gap-2 text-xs font-bold uppercase text-paper-info-strong">
          <BeakerIcon class="h-4 w-4" aria-hidden="true" />
          {{ tituloAmostras }}
        </h3>
        <Badge variant="info" size="sm">{{ rotuloQuantidadeAmostras(amostras.length) }}</Badge>
      </header>
      <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead>
          <tr>
            <th scope="col" class="w-28">Amostra</th>
            <th scope="col" class="w-56">Exame</th>
            <th scope="col">Descrição do material</th>
            <th scope="col" class="w-32 text-right">Status no AGHU</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="amostra in amostras"
            :key="amostra.numeroAmostra"
            :class="mesmaAmostra(amostra.numeroAmostra, props.amostraBipada) ? 'bg-paper-primary-soft/60' : ''"
          >
            <th scope="row" class="whitespace-nowrap font-bold text-gray-900 tabular-nums">
              <span class="inline-flex items-center gap-1.5">
                Amostra {{ amostra.numeroAmostra }}
                <Badge v-if="mesmaAmostra(amostra.numeroAmostra, props.amostraBipada)" variant="primary" size="sm">
                  Bipada
                </Badge>
              </span>
            </th>
            <td>
              <span class="flex items-start gap-1.5">
                <Badge :variant="amostra.tipoExame === 'CO' ? 'danger' : 'primary'" size="sm" :title="TIPOS_EXAME[amostra.tipoExame].nome">
                  {{ amostra.tipoExame }}
                </Badge>
                <span class="min-w-0 leading-tight">
                  <span class="block font-bold text-gray-900">{{ amostra.siglaExame }}</span>
                  <span class="block text-xs text-gray-600">{{ amostra.nomeExame }}</span>
                </span>
              </span>
            </td>
            <td :class="amostra.descricaoMaterial ? 'font-semibold text-gray-800' : 'italic text-gray-500'">
              {{ amostra.descricaoMaterial || NAO_INFORMADO }}
            </td>
            <td class="text-right">
              <Badge :variant="statusItemAghu(amostra.codStatusItem, amostra.statusItemDescricao).variante" size="sm">
                {{ statusItemAghu(amostra.codStatusItem, amostra.statusItemDescricao).rotulo }}
              </Badge>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </section>

    <div class="mt-4 rounded-lg border border-paper-info/40 bg-paper-info-soft p-4">
      <p class="flex items-center gap-2 text-xs font-bold uppercase text-paper-info-strong">
        <ClipboardDocumentListIcon class="h-4 w-4" aria-hidden="true" /> Informações clínicas
      </p>
      <p class="mt-1 whitespace-pre-line text-sm text-gray-800">{{ solicitacao.informacoesClinicas || NAO_INFORMADO }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BeakerIcon, ClipboardDocumentListIcon, LockClosedIcon } from '@heroicons/vue/24/outline';
import Badge from '../Badge.vue';
import { NAO_INFORMADO, TIPOS_EXAME, rotuloOrigem, statusItemAghu } from '../../constants/ap';
import { calcularIdade, formatarData } from '../../helpers/formato';
import { amostrasDosGrupos, mesmaAmostra, rotuloQuantidadeAmostras } from '../../helpers/aghu';
import type { SolicitacaoAghu } from '../../types/ap';

/**
 * Dados do exame da solicitação AGHU exibidos sem edição (conferência e aba "Solicitação AGHU").
 * Só exibe campos que existem no AGHU (ver `data/dicionario_dados.md`).
 */
const props = withDefaults(
  defineProps<{
    /** Dados de cabeçalho da solicitação (paciente, origem etc.). */
    solicitacao: SolicitacaoAghu;
    /** Grupos (tipos de exame) cujas amostras são listadas; padrão: só o da `solicitacao`. */
    exames?: SolicitacaoAghu[];
    /** Título da tabela de amostras. */
    titulo?: string;
    /** Número da amostra bipada para destaque visual na tabela. */
    amostraBipada?: string | null;
  }>(),
  { exames: undefined, titulo: undefined, amostraBipada: null },
);

/** Amostras de todos os grupos exibidos, em ordem de número, com o tipo de exame de cada uma. */
const amostras = computed(() => amostrasDosGrupos(props.exames ?? [props.solicitacao]));
const tituloAmostras = computed(() => props.titulo ?? 'Amostras da solicitação');

const campos = computed(() => {
  const s = props.solicitacao;
  const idade = calcularIdade(s.dataNascimento);
  return [
    { rotulo: 'Nº da solicitação', valor: s.codigoSolicitacao },
    { rotulo: 'Prontuário', valor: s.prontuario || NAO_INFORMADO },
    { rotulo: 'Nome do paciente', valor: s.nomePaciente || NAO_INFORMADO, largo: true },
    { rotulo: 'Nascimento e idade', valor: idade === null ? NAO_INFORMADO : `${formatarData(s.dataNascimento)} · ${idade} anos` },
    { rotulo: 'Origem', valor: rotuloOrigem(s.origem) },
    { rotulo: 'Data da solicitação', valor: formatarData(s.dataSolicitacao) },
    { rotulo: 'Especialidade', valor: s.especialidade || NAO_INFORMADO },
    { rotulo: 'Unidade solicitante', valor: s.unidade || NAO_INFORMADO, largo: true },
  ];
});
</script>

<style scoped>
.amostras-aghu {
  overflow: hidden;
  border-radius: 0.5rem;
  border: 1px solid color-mix(in srgb, var(--color-paper-info) 30%, transparent);
  background: #fff;
}
.amostras-aghu > header {
  background: color-mix(in srgb, var(--color-paper-info-soft) 60%, white);
  border-bottom: 1px solid color-mix(in srgb, var(--color-paper-info) 30%, transparent);
}
.amostras-aghu thead th {
  padding: 0.5rem 1rem 0.25rem;
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-paper-info-strong);
}
.amostras-aghu tbody th,
.amostras-aghu tbody td {
  padding: 0.625rem 1rem;
  vertical-align: middle;
  border-top: 1px solid var(--color-gray-100);
}
.amostras-aghu tbody tr:first-child th,
.amostras-aghu tbody tr:first-child td {
  border-top: 0;
}
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
  overflow-wrap: anywhere;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-gray-800);
}
</style>
