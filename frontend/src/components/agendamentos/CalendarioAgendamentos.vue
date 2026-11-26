<template>
  <div>
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <p class="text-sm text-gray-500">
        Clique em um dia ou horário para ver as vagas. Arraste um agendamento para remarcar.
      </p>
      <div class="flex flex-wrap items-center gap-2 text-xs">
        <span class="rounded-full bg-emerald-100 px-2 py-1 font-semibold text-emerald-800">Vagas livres</span>
        <span class="rounded-full bg-amber-100 px-2 py-1 font-semibold text-amber-800">Últimas vagas</span>
        <span class="rounded-full bg-red-100 px-2 py-1 font-semibold text-red-800">Esgotada / encerrada</span>
        <span class="rounded-full bg-sky-100 px-2 py-1 font-semibold text-sky-800">Proposta a confirmar</span>
      </div>
    </div>
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <FullCalendar ref="calendario" :options="opcoes" />
    </div>
    <p v-if="!readonly" class="mt-2 text-xs text-gray-500">
      A remarcação por arrastar e soltar sempre exige justificativa e confirmação antes de ser salva.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { DateClickArg } from '@fullcalendar/interaction';
import ptBrLocale from '@fullcalendar/core/locales/pt-br';
import type {
  CalendarOptions,
  DatesSetArg,
  EventClickArg,
  EventDropArg,
  EventInput,
} from '@fullcalendar/core';
import { agoraIso, paraIsoLocal } from '../../config/tempo';
import type { AgendaSlot, Agendamento, PropostaAgendamentoFila } from '../../types/sae';

const props = defineProps<{
  slots: AgendaSlot[];
  agendamentos: Agendamento[];
  propostas: PropostaAgendamentoFila[];
  readonly?: boolean;
}>();

const emit = defineEmits<{
  'periodo-alterado': [de: string, ate: string];
  'dia-selecionado': [data: string];
  'slot-selecionado': [slot: AgendaSlot];
  'agendamento-selecionado': [agendamento: Agendamento];
  remarcar: [agendamento: Agendamento, slot: AgendaSlot];
  'proposta-movida': [proposta: PropostaAgendamentoFila, slot: AgendaSlot];
  'erro-slot': [mensagem: string];
}>();

const calendario = ref<InstanceType<typeof FullCalendar> | null>(null);

/** Leva o calendário para o mês/semana da data informada. */
function irParaData(dataIso: string): void {
  if (!dataIso) return;
  calendario.value?.getApi().gotoDate(dataIso.slice(0, 10));
}

defineExpose({ irParaData });

function corOcupacao(slot: AgendaSlot): string {
  if (slot.status === 'ENCERRADO' || slot.livres === 0) return '#fecaca';
  if (slot.capacidade > 0 && slot.livres / slot.capacidade <= 0.4) return '#fde68a';
  return '#a7f3d0';
}

function corStatus(status: Agendamento['status']): string {
  if (status === 'CANCELADO') return '#dc2626';
  if (status === 'CONCLUIDO') return '#6b7280';
  if (status === 'PROPOSTO') return '#0284c7';
  return '#0d9488';
}

const eventos = computed<EventInput[]>(() => [
  ...props.slots.map((slot) => ({
    id: `vaga-${slot.id}`,
    title: `${slot.livres}/${slot.capacidade} vagas`,
    start: slot.inicio,
    end: slot.fim,
    display: 'background' as const,
    backgroundColor: corOcupacao(slot),
    borderColor: 'transparent',
    extendedProps: { tipo: 'slot', slot },
  })),
  ...props.agendamentos
    // Propostas são renderizadas como cards próprios (arrastáveis) abaixo.
    .filter((agendamento) => agendamento.status !== 'PROPOSTO')
    .map((agendamento) => ({
      id: `agendamento-${agendamento.id}`,
      title: `${agendamento.pacienteNome} · ${agendamento.exame}`,
      start: agendamento.dataHora,
      backgroundColor: corStatus(agendamento.status),
      borderColor: corStatus(agendamento.status),
      textColor: '#ffffff',
      classNames: ['agendamento-evento'],
      extendedProps: { tipo: 'agendamento', agendamento },
    })),
  ...props.propostas.map((proposta) => ({
    id: `proposta-${proposta.agendamentoId}`,
    title: `${proposta.pacienteNome} · ${proposta.nomeExame}`,
    start: proposta.dataHora,
    backgroundColor: corStatus('PROPOSTO'),
    borderColor: corStatus('PROPOSTO'),
    textColor: '#ffffff',
    classNames: ['proposta-evento'],
    extendedProps: { tipo: 'proposta', proposta },
  })),
]);

const opcoes = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  locales: [ptBrLocale],
  locale: 'pt-br',
  initialView: 'dayGridMonth',
  initialDate: agoraIso().slice(0, 10),
  now: agoraIso(),
  firstDay: 1,
  height: 'auto',
  editable: !props.readonly,
  eventStartEditable: !props.readonly,
  eventDurationEditable: false,
  selectable: false,
  slotMinTime: '07:00:00',
  slotMaxTime: '18:00:00',
  slotDuration: '01:00:00',
  allDaySlot: false,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek',
  },
  buttonText: { today: 'Hoje', month: 'Mês', week: 'Semana' },
  events: eventos.value,
  datesSet: (info: DatesSetArg) => {
    emit('periodo-alterado', paraIsoLocal(info.start.getTime()), paraIsoLocal(info.end.getTime()));
  },
  dateClick: (info: DateClickArg) => {
    emit('dia-selecionado', paraIsoLocal(info.date.getTime()).slice(0, 10));
  },
  eventClick: (info: EventClickArg) => {
    const slot = info.event.extendedProps.slot as AgendaSlot | undefined;
    if (slot) {
      emit('dia-selecionado', slot.inicio.slice(0, 10));
      emit('slot-selecionado', slot);
      return;
    }
    const agendamento = info.event.extendedProps.agendamento as Agendamento | undefined;
    if (agendamento) emit('agendamento-selecionado', agendamento);
  },
  eventDidMount: (info) => {
    const slot = info.event.extendedProps.slot as AgendaSlot | undefined;
    if (slot) {
      info.el.title = `${slot.livres}/${slot.capacidade} vagas · ${slot.unidade} · ${slot.nomeExame}`;
      return;
    }
    const agendamento = info.event.extendedProps.agendamento as Agendamento | undefined;
    if (agendamento) {
      info.el.title = `${agendamento.pacienteNome} · ${agendamento.protocolo} · ${agendamento.status}`;
      return;
    }
    const proposta = info.event.extendedProps.proposta as PropostaAgendamentoFila | undefined;
    if (proposta) {
      info.el.title = `${proposta.pacienteNome} · ${proposta.nomeExame} · ${proposta.dataHora} · ${proposta.statusSolicitacao}`;
    }
  },
  eventAllow: (_dropInfo, draggedEvent) => {
    if (props.readonly) return false;
    const tipo = draggedEvent?.extendedProps.tipo as string | undefined;
    return tipo === 'agendamento' || tipo === 'proposta';
  },
  eventDrop: (info: EventDropArg) => {
    if (props.readonly) {
      info.revert();
      return;
    }
    const tipo = info.event.extendedProps.tipo as string | undefined;
    const destino = paraIsoLocal(info.event.start?.getTime() ?? 0).slice(0, 16);
    const slot = props.slots.find((item) =>
      item.inicio.slice(0, 16) === destino && item.status !== 'ENCERRADO');
    if (!slot) {
      info.revert();
      emit('erro-slot', 'Não há vaga cadastrada para o horário de destino.');
      return;
    }
    info.revert();
    if (tipo === 'agendamento') {
      // Arraste de agendamento ATIVO/PROPOSTO via calendário: usar o fluxo de
      // remarcação com justificativa, que só salva após confirmação.
      const agendamento = info.event.extendedProps.agendamento as Agendamento | undefined;
      if (agendamento) emit('remarcar', agendamento, slot);
      return;
    }
    if (tipo !== 'proposta') return;
    const proposta = info.event.extendedProps.proposta as PropostaAgendamentoFila | undefined;
    if (proposta) emit('proposta-movida', proposta, slot);
  },
}));
</script>
