<template>
  <button
    :type="type"
    :disabled="isDisabled"
    :aria-busy="loading || undefined"
    :class="[baseClass, sizeClass, variantClass]"
  >
    <!-- Com ícone: o indicador ocupa o lugar do ícone, mantendo a largura. -->
    <template v-if="$slots.icon">
      <span :class="iconGapClass" class="inline-flex shrink-0">
        <Spinner v-if="loading" :class="spinnerSizeClass" />
        <slot v-else name="icon"></slot>
      </span>
      <slot></slot>
    </template>

    <!-- Sem ícone: o indicador fica sobre o texto, que fica transparente (mantém largura e nome acessível). -->
    <template v-else>
      <span v-if="loading" class="absolute inset-0 flex items-center justify-center">
        <Spinner :class="spinnerSizeClass" />
      </span>
      <span :class="{ 'opacity-0': loading }" class="inline-flex items-center">
        <slot></slot>
      </span>
    </template>
  </button>
</template>

<script setup lang="ts">
import { computed, h, type FunctionalComponent } from 'vue';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger'
  | 'default'
  | 'outline';

export type ButtonSize = 'sm' | 'md';

const props = withDefaults(
  defineProps<{
    variant?: ButtonVariant;
    size?: ButtonSize;
    type?: 'button' | 'submit' | 'reset';
    loading?: boolean;
    disabled?: boolean;
  }>(),
  {
    variant: 'primary',
    size: 'md',
    type: 'button',
    loading: false,
    disabled: false,
  },
);

/** Indicador giratório (SVG inline) exibido durante o carregamento. */
const Spinner: FunctionalComponent = () =>
  h(
    'svg',
    { class: 'animate-spin', viewBox: '0 0 24 24', fill: 'none', 'aria-hidden': 'true' },
    [
      h('circle', { class: 'opacity-25', cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '4' }),
      h('path', { class: 'opacity-75', fill: 'currentColor', d: 'M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z' }),
    ],
  );

const isDisabled = computed(() => props.disabled || props.loading);

const baseClass =
  'focus-ring relative inline-flex items-center justify-center rounded font-bold select-none ' +
  'transition duration-150 ease-in-out enabled:active:scale-[0.97]';

const sizeClass = computed(() =>
  props.size === 'sm' ? 'h-8 px-3 text-sm' : 'h-10 px-4 text-base',
);

const iconGapClass = computed(() => (props.size === 'sm' ? 'mr-1.5' : 'mr-2'));

const spinnerSizeClass = computed(() => (props.size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'));

/** Classes de cor por variante: normal, hover e pressionado (apenas quando habilitado). */
const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    'bg-paper-primary text-white enabled:hover:bg-paper-primary-hover enabled:active:bg-paper-primary-strong',
  secondary:
    'bg-paper-secondary text-paper-text enabled:hover:bg-paper-secondary-hover enabled:active:brightness-90',
  info: 'bg-paper-info text-white enabled:hover:bg-paper-info-hover enabled:active:bg-paper-info-strong',
  success:
    'bg-paper-success text-white enabled:hover:bg-paper-success-hover enabled:active:bg-paper-success-strong',
  warning:
    'bg-paper-warning text-white enabled:hover:bg-paper-warning-hover enabled:active:bg-paper-warning-strong',
  danger:
    'bg-paper-danger text-white enabled:hover:bg-paper-danger-hover enabled:active:bg-paper-danger-strong',
  default:
    'bg-paper-default text-white enabled:hover:bg-paper-default-hover enabled:active:brightness-75',
  outline:
    'bg-transparent border border-paper-primary text-paper-primary-strong ' +
    'enabled:hover:bg-paper-primary-soft enabled:active:bg-paper-primary enabled:active:text-white',
};

const variantClass = computed(() => {
  if (isDisabled.value) {
    return props.variant === 'outline'
      ? 'bg-transparent border border-gray-300 text-gray-400'
      : 'bg-paper-disabled text-gray-500';
  }
  return VARIANT_CLASSES[props.variant];
});
</script>
