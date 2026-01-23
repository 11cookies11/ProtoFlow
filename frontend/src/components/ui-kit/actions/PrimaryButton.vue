<template>
  <button class="w-full py-2.5 bg-primary text-white font-bold text-sm rounded-lg hover:bg-blue-700 transition-all shadow-sm" @click="$emit('click')">
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
defineEmits<{ (e: 'click'): void }>()
</script>
