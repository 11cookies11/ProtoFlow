<template>
  <button class="w-full py-2.5 text-slate-500 font-bold text-sm rounded-lg hover:bg-slate-100 transition-all" @click="$emit('click')">
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
defineEmits<{ (e: 'click'): void }>()
</script>
