<template>
  <!-- Ficha de trabalho A4: blocos de dados + quadro de acompanhamento físico por setor. -->
  <article class="ficha-trabalho">
    <header class="flex items-start justify-between border-b-2 border-black pb-[3mm]">
      <div>
        <p class="text-[8pt] uppercase tracking-wide">Hospital das Clínicas da UFPE · Serviço de Anatomia Patológica</p>
        <h1 class="text-[15pt] font-extrabold leading-tight">Ficha de trabalho</h1>
        <p class="text-[10pt]">{{ TIPOS_EXAME[caso.tipoExame].nome }} ({{ caso.tipoExame }})</p>
      </div>
      <p class="text-right text-[8pt] leading-snug">Emitida em<br /><strong>{{ formatarDataHora(emitidaEm) }}</strong></p>
    </header>

    <!-- 1. Identificação -->
    <section class="bloco">
      <h2>1. Identificação</h2>
      <div class="flex items-center justify-between gap-[6mm]">
        <div>
          <p class="text-[24pt] font-extrabold leading-none tracking-tight">{{ caso.numeroInterno }}</p>
          <p v-if="caso.urgente" class="mt-[1.5mm] inline-block border-2 border-black px-[1.5mm] text-[9pt] font-extrabold">
            URGENTE — {{ caso.motivoUrgencia }}
          </p>
          <p class="mt-[1.5mm] text-[9pt]"><span class="rotulo">Recebimento no SAP:</span> {{ formatarDataHora(caso.dataEntradaSap) }}</p>
        </div>
        <Barcode :valor="caso.numeroInterno" class="h-[14mm] w-[62mm] shrink-0" />
      </div>
    </section>

    <div class="grid grid-cols-2 gap-x-[6mm]">
      <!-- 2. Solicitação -->
      <section class="bloco">
        <h2>2. Solicitação</h2>
        <dl>
          <dt>Nº da solicitação AGHU</dt>
          <dd>{{ caso.solicitacao.codigoSolicitacao }}</dd>
          <dt>Data da solicitação</dt>
          <dd>{{ formatarDataHora(caso.solicitacao.dataSolicitacao) }}</dd>
          <dt>Exame</dt>
          <dd>{{ caso.solicitacao.nomeExame }}</dd>
        </dl>
      </section>

      <!-- 3. Paciente e origem -->
      <section class="bloco">
        <h2>3. Paciente e origem</h2>
        <dl>
          <dt>Prontuário</dt>
          <dd>{{ caso.solicitacao.prontuario }}</dd>
          <dt>Origem</dt>
          <dd>{{ ORIGENS[caso.solicitacao.origem] }}</dd>
          <dt>Unidade solicitante</dt>
          <dd>{{ caso.solicitacao.unidade }}</dd>
        </dl>
      </section>
    </div>

    <!-- 4. Solicitante -->
    <section class="bloco">
      <h2>4. Solicitante</h2>
      <dl class="grid grid-cols-2 gap-x-[6mm]">
        <div>
          <dt>Especialidade</dt>
          <dd>{{ caso.solicitacao.especialidade }}</dd>
        </div>
        <div>
          <dt>Médico solicitante</dt>
          <dd>{{ caso.solicitacao.nomeSolicitante }}</dd>
        </div>
      </dl>
    </section>

    <!-- 5. Material -->
    <section class="bloco">
      <h2>5. Material</h2>
      <dl>
        <dt>Descrição do material</dt>
        <dd class="text-[11pt] font-bold">{{ caso.solicitacao.descricaoMaterial }}</dd>
        <dt>Informações clínicas</dt>
        <dd>{{ caso.solicitacao.informacoesClinicas || '—' }}</dd>
      </dl>
    </section>

    <!-- Acompanhamento físico -->
    <section class="bloco">
      <h2>Acompanhamento físico por setor</h2>
      <table class="w-full border-collapse text-[9pt]">
        <thead>
          <tr>
            <th class="w-[34%]">Setor</th>
            <th class="w-[22%]">Data/hora</th>
            <th class="w-[30%]">Responsável</th>
            <th class="w-[14%]">Visto</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="etapa in etapas" :key="etapa">
            <td class="font-semibold">{{ ETAPAS[etapa] }}</td>
            <td></td>
            <td></td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </section>

    <footer class="mt-[4mm] flex justify-between border-t border-black pt-[1.5mm] text-[7.5pt]">
      <span>Caso {{ caso.numeroInterno }} · Solicitação AGHU {{ caso.solicitacao.codigoSolicitacao }}</span>
      <span>Emitida em {{ formatarDataHora(emitidaEm) }}</span>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import Barcode from './Barcode.vue';
import { ETAPAS, ORIGENS, TIPOS_EXAME, fluxoDoCaso } from '../../constants/ap';
import { formatarDataHora } from '../../helpers/formato';
import type { CasoAp } from '../../types/ap';

const props = defineProps<{ caso: CasoAp; emitidaEm: string }>();

/** Uma linha por etapa do fluxo do tipo do caso (IHQ entra antes da microscopia, se houver). */
const etapas = computed(() => fluxoDoCaso(props.caso.tipoExame, props.caso.ihqs.length > 0));
</script>

<style scoped>
.ficha-trabalho {
  width: 186mm;
  min-height: 270mm;
  padding: 0;
  background: #fff;
  color: #000;
  font-family: 'Nunito', ui-sans-serif, system-ui, sans-serif;
  font-size: 9.5pt;
  line-height: 1.35;
}
.bloco {
  margin-top: 4mm;
  border: 1px solid #000;
  padding: 2.5mm 3mm;
  break-inside: avoid;
}
.bloco h2 {
  margin-bottom: 1.5mm;
  font-size: 8pt;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.bloco dt,
.rotulo {
  font-size: 7.5pt;
  font-weight: 700;
  text-transform: uppercase;
  color: #333;
}
.bloco dd {
  margin-bottom: 1.5mm;
}
.bloco th,
.bloco td {
  border: 1px solid #000;
  padding: 1.5mm 2mm;
  text-align: left;
}
.bloco td {
  height: 9mm;
}
</style>
