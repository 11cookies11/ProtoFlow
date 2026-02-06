<template>
  <div class="flex items-center justify-between w-full">
    <div class="flex items-center gap-4">
      <div class="bg-primary p-2 rounded-xl text-white">
        <span class="material-symbols-outlined !text-2xl">component_exchange</span>
      </div>
      <div>
        <h1 class="text-xl font-bold tracking-tight text-slate-900">{{ title }}</h1>
        <p class="text-xs text-slate-500 font-medium uppercase tracking-wider">{{ subtitle }}</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg border border-slate-200">
        <span class="size-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="text-xs font-bold text-slate-600">{{ modeLabel }}</span>
      </div>
      <button
        class="flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
        @click="$emit('publish')"
      >
        <span class="material-symbols-outlined !text-sm">publish</span>
        <span>{{ tr('发布规格页') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'

defineProps<{ title: string; subtitle: string; modeLabel: string }>()
defineEmits<{ (e: 'publish'): void }>()

const tr = inject('tr', (text) => text)
</script>
