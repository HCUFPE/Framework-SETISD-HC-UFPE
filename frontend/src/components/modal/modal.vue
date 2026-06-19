<template>
  <teleport to="body">
    <!-- Overlay com Blur -->
    <transition name="fade">
      <div 
        v-if="show" 
        class="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-40 transition-opacity" 
        @click="close"
      ></div>
    </transition>

    <!-- Container do Modal -->
    <transition name="modal-scale">
      <div 
        v-if="show" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      >
        <div 
          class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden transform transition-all"
          @click.stop
        >
          <!-- Header -->
          <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
            <h2 class="text-xl font-bold text-gray-800">
              <slot name="header">Título do Modal</slot>
            </h2>
            <button 
              @click="close" 
              class="p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <XMarkIcon class="h-6 w-6" />
            </button>
          </div>

          <!-- Body -->
          <div class="px-6 py-6 text-gray-600 leading-relaxed">
            <slot></slot>
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end space-x-3">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(['close']);
const close = () => emit('close');

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
