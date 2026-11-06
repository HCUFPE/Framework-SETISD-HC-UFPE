<template>
  <teleport to="body">
    <!-- Overlay com Blur -->
    <transition name="fade">
      <div 
        v-if="show" 
        class="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-40 transition-opacity" 
      ></div>
    </transition>

    <!-- Container do Modal -->
    <transition name="modal-scale">
      <div 
        v-if="show" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
        @mousedown.self="backdropPressed = true"
        @click.self="onBackdropClick"
      >
        <div 
          :class="sizeClass"
          class="bg-white rounded-2xl shadow-2xl w-full max-h-full flex flex-col overflow-hidden transform transition-all"
          role="dialog"
          aria-modal="true"
        >
          <!-- Header -->
          <div class="shrink-0 px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
            <h2 class="text-xl font-bold text-gray-800">
              <slot name="header">Título do Modal</slot>
            </h2>
            <button 
              type="button"
              aria-label="Fechar"
              @click="close" 
              class="focus-ring p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 active:bg-gray-200 active:scale-95 transition"
            >
              <XMarkIcon class="h-6 w-6" />
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 min-h-0 overflow-y-auto px-6 py-6 text-gray-600 leading-relaxed">
            <slot></slot>
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="shrink-0 px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end space-x-3">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl';

const props = withDefaults(
  defineProps<{
    show?: boolean;
    /** Largura máxima do modal; `lg` mantém a largura histórica. */
    size?: ModalSize;
    /** Quando `false`, clicar no fundo escurecido não fecha o modal. */
    closeOnBackdrop?: boolean;
  }>(),
  { show: false, size: 'lg', closeOnBackdrop: true },
);

const emit = defineEmits<{ (e: 'close'): void }>();
const close = () => emit('close');

const SIZE_CLASSES: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-3xl',
};

const sizeClass = computed(() => SIZE_CLASSES[props.size]);

/** Só conta como clique fora se o botão do mouse também foi pressionado fora (evita fechar ao arrastar uma seleção de texto). */
const backdropPressed = ref(false);

/** Fecha ao clicar fora do painel, se permitido pela tela. */
const onBackdropClick = () => {
  const pressedOutside = backdropPressed.value;
  backdropPressed.value = false;
  if (pressedOutside && props.closeOnBackdrop) close();
};

// Bloqueia o scroll do corpo quando o modal abre
watch(() => props.show, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.show) close();
};

onMounted(() => document.addEventListener('keydown', handleEscape));
onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape);
  document.body.style.overflow = ''; // Garante limpeza no unmount
});
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.modal-scale-enter-active { transition: all 0.3s ease-out; }
.modal-scale-leave-active { transition: all 0.2s ease-in; }
.modal-scale-enter-from { opacity: 0; transform: scale(0.95) translateY(-10px); }
.modal-scale-leave-to { opacity: 0; transform: scale(0.95) translateY(10px); }
</style>
