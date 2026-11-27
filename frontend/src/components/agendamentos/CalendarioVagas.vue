<template>
  <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
    <FullCalendar ref="calendario" :options="opcoes" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import ptBrLocale from '@fullcalendar/core/locales/pt-br';
import type { CalendarOptions, EventInput } from '@fullcalendar/core';
import type { DateClickArg } from '@fullcalendar/interaction';
import { agoraIso } from '../../config/tempo';
import { diaLocal } from '../../utils/datetime';
import type { AgendaSlot } from '../../types/sae';

const props = defineProps<{
  slots: AgendaSlot[];
  dataSelecionada: string;
}>();

const emit = defineEmits<{
  'dia-selecionado': [data: string];
}>();

const calendario = ref<InstanceType<typeof FullCalendar> | null>(null);

/** Uma faixa por dia com a quantidade de vagas do exame selecionado. */
const porDia = computed(() => {
  const mapa = new Map<string, { total: number; livres: number }>();
  props.slots.forEach((slot) => {
    const dia = diaLocal(slot.inicio);
    const atual = mapa.get(dia) ?? { total: 0, livres: 0 };
    atual.total += 1;
    atual.livres += slot.livres;
    mapa.set(dia, atual);
  });
  return mapa;
});

const eventos = computed<EventInput[]>(() => Array.from(porDia.value, ([dia, contagem]) => ({
  start: dia,
  title: `${contagem.total} vaga(s) · ${contagem.livres} livre(s)`,
  display: 'background' as const,
  backgroundColor: contagem.livres > 0 ? '#dbeafe' : '#fee2e2',
  borderColor: 'transparent',
})));

const opcoes = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  locales: [ptBrLocale],
  locale: 'pt-br',
  initialView: 'dayGridMonth',
  initialDate: props.dataSelecionada || agoraIso().slice(0, 10),
  now: agoraIso(),
  firstDay: 1,
  height: 'auto',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
  buttonText: { today: 'Hoje' },
  events: eventos.value,
  dateClick: (info: DateClickArg) => emit('dia-selecionado', info.dateStr),
  eventClick: (info) => emit('dia-selecionado', info.event.startStr.slice(0, 10)),
  dayCellClassNames: (info) => (info.dateStr === props.dataSelecionada
    ? ['vaga-dia-selecionado']
    : []),
}));
</script>

<style scoped>
:deep(.vaga-dia-selecionado) {
  background-color: #eff6ff;
  box-shadow: inset 0 0 0 2px #2563eb;
}
</style>
