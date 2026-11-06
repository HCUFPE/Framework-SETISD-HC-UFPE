<template>
  <div
    :class="config.box"
    :role="variant === 'danger' || variant === 'warning' ? 'alert' : 'status'"
    class="flex items-start gap-3 rounded-lg border border-l-4 p-4 text-sm"
  >
    <component :is="config.icon" :class="config.iconColor" class="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
    <div class="flex-1 min-w-0 leading-relaxed">
      <p v-if="title" class="font-bold mb-0.5">{{ title }}</p>
      <slot></slot>
    </div>
    <button
      v-if="dismissible"
      type="button"
      aria-label="Fechar alerta"
      :class="config.close"
      class="focus-ring -m-1 p-1 rounded-md shrink-0 transition active:scale-95"
      @click="emit('dismiss')"
    >
      <XMarkIcon class="h-4 w-4" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue';
import {
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline';

export type AlertVariant = 'info' | 'success' | 'warning' | 'danger';

const props = withDefaults(
  defineProps<{
    variant?: AlertVariant;
    title?: string;
    /** Exibe o botão de fechar; a tela oculta o alerta ao receber `dismiss`. */
    dismissible?: boolean;
  }>(),
  { variant: 'info', title: undefined, dismissible: false },
);

const emit = defineEmits<{ (e: 'dismiss'): void }>();

interface AlertConfig {
  icon: Component;
  box: string;
  iconColor: string;
  close: string;
}

const CONFIGS: Record<AlertVariant, AlertConfig> = {
  info: {
    icon: InformationCircleIcon,
    box: 'bg-paper-info-soft text-paper-info-strong border-paper-info/40 border-l-paper-info',
    iconColor: 'text-paper-info-strong',
    close: 'hover:bg-paper-info/20 active:bg-paper-info/30',
  },
  success: {
    icon: CheckCircleIcon,
    box: 'bg-paper-success-soft text-paper-success-strong border-paper-success/40 border-l-paper-success',
    iconColor: 'text-paper-success-strong',
    close: 'hover:bg-paper-success/20 active:bg-paper-success/30',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    box: 'bg-paper-warning-soft text-paper-warning-strong border-paper-warning/50 border-l-paper-warning',
    iconColor: 'text-paper-warning-strong',
    close: 'hover:bg-paper-warning/25 active:bg-paper-warning/35',
  },
  danger: {
    icon: XCircleIcon,
    box: 'bg-paper-danger-soft text-paper-danger-strong border-paper-danger/40 border-l-paper-danger',
    iconColor: 'text-paper-danger-strong',
    close: 'hover:bg-paper-danger/20 active:bg-paper-danger/30',
  },
};

const config = computed(() => CONFIGS[props.variant]);
</script>
