<template>
  <button
    class="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold"
    @click="$emit('open')"
  >
    <span><slot>导出数据格式</slot></span>
    <span class="material-symbols-outlined">expand_more</span>
  </button>
</template>

<script setup lang="ts">
defineEmits<{ (e: 'open'): void }>()
</script>
