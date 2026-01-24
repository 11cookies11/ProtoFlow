<template>
  <div class="space-y-2">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div class="flex gap-2">
      <div class="flex-1 flex items-center h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 overflow-hidden truncate">
        {{ modelValue || hint || tr('选择路径') }}
      </div>
      <button
        class="px-3 h-10 bg-slate-100 border border-slate-200 rounded-lg text-xs font-bold hover:bg-slate-200"
        type="button"
        @click="$emit('browse')"
      >
        {{ tr('浏览...') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'

defineProps<{ label: string; modelValue: string; disabled?: boolean; hint?: string }>()
defineEmits<{ (e: 'browse'): void }>()

const tr = inject('tr', (text) => text)
</script>
