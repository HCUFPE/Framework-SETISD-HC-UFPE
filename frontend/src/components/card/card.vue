<template>
  <div class="bg-white shadow-lab rounded-lg">
    <div v-if="$slots.header" class="p-4">
      <slot name="header"></slot>
    </div>
    <div class="p-6">
      <slot></slot>
    </div>
    <div v-if="$slots.footer" class="p-4">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
