<template>
  <div class="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-5">
    <input
      :value="busca"
      class="form-control"
      placeholder="Buscar por paciente, prontuário, protocolo ou exame"
      aria-label="Buscar solicitações"
      @input="aoBusca"
    />
    <select :value="status" class="form-control" aria-label="Filtrar por status" @change="aoStatus">
      <option value="">Todos os status</option>
      <option v-for="(rotulo, chave) in ROTULOS_STATUS" :key="chave" :value="chave">{{ rotulo }}</option>
    </select>
    <select :value="tipoExame" class="form-control" aria-label="Filtrar por tipo de exame" @change="aoTipo">
      <option value="">Todos os tipos</option>
      <option v-for="tipo in tiposExame" :key="tipo" :value="tipo">{{ tipo }}</option>
    </select>
    <select :value="unidadeSolicitante" class="form-control" aria-label="Filtrar por unidade solicitante" @change="aoUnidade">
      <option value="">Todas as unidades solicitantes</option>
      <option v-for="unidade in unidadesSolicitantes" :key="unidade" :value="unidade">{{ unidade }}</option>
    </select>
    <div class="flex gap-2">
      <select :value="periodo" class="form-control" aria-label="Filtrar por período" @change="aoPeriodo">
        <option value="24">Últimas 24 h</option>
        <option value="72">Últimas 72 h</option>
        <option value="168">Últimos 7 dias</option>
        <option value="720">Últimos 30 dias</option>
        <option value="todos">Todo o período</option>
      </select>
      <Button variant="primary" @click="emit('filtrar')">Filtrar</Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ROTULOS_STATUS } from '../types/sae';
import Button from './Button.vue';

defineProps<{
  busca: string;
  status: string;
  tipoExame: string;
  unidadeSolicitante: string;
  periodo: string;
  tiposExame: string[];
  unidadesSolicitantes: string[];
}>();

const emit = defineEmits<{
  (e: 'update:busca', valor: string): void;
  (e: 'update:status', valor: string): void;
  (e: 'update:tipoExame', valor: string): void;
  (e: 'update:unidadeSolicitante', valor: string): void;
  (e: 'update:periodo', valor: string): void;
  (e: 'filtrar'): void;
}>();

function aoBusca(evento: Event): void {
  emit('update:busca', (evento.target as HTMLInputElement).value);
}

function aoStatus(evento: Event): void {
  emit('update:status', (evento.target as HTMLSelectElement).value);
}

function aoTipo(evento: Event): void {
  emit('update:tipoExame', (evento.target as HTMLSelectElement).value);
}

function aoUnidade(evento: Event): void {
  emit('update:unidadeSolicitante', (evento.target as HTMLSelectElement).value);
}

function aoPeriodo(evento: Event): void {
  emit('update:periodo', (evento.target as HTMLSelectElement).value);
}
</script>
