<template>
  <div class="flex items-center bg-slate-100 p-1 rounded-xl">
    <button class="flex-1 flex items-center justify-center gap-1.5 py-2 bg-white shadow-sm rounded-lg text-xs font-bold text-slate-700" @click="$emit('run')">
      <span class="material-symbols-outlined !text-sm text-emerald-500">play_arrow</span>
      {{ tr('批量运行') }}
    </button>
    <button class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-bold text-slate-500 hover:text-slate-700" @click="$emit('pause')">
      <span class="material-symbols-outlined !text-sm">pause</span>
      {{ tr('暂停') }}
    </button>
    <button class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-bold text-slate-500 hover:text-slate-700" @click="$emit('reset')">
      <span class="material-symbols-outlined !text-sm">restart_alt</span>
      {{ tr('重置') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'

defineEmits<{ (e: 'run'): void; (e: 'pause'): void; (e: 'reset'): void }>()

const tr = inject('tr', (text) => text)
</script>
