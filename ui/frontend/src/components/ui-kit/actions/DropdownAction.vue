<template>
  <button
    class="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold"
    @click="$emit('open')"
  >
    <span><slot>{{ tr('导出数据格式') }}</slot></span>
    <span class="material-symbols-outlined">expand_more</span>
  </button>
</template>

<script setup lang="ts">
import { inject } from 'vue'

defineEmits<{ (e: 'open'): void }>()

const tr = inject('tr', (text) => text)
</script>
