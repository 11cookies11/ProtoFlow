<template>
  <div class="bg-slate-900 rounded-xl p-6 text-slate-300">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">terminal</span>
        <h4 class="text-sm font-bold text-white">{{ title }}</h4>
      </div>
      <button class="text-xs text-slate-400 hover:text-white" @click="copy">Copy</button>
    </div>
    <pre class="text-[10px] font-mono leading-relaxed bg-slate-800/50 p-3 rounded-lg border border-slate-700">{{ formatted }}</pre>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ title: string; value: string | Record<string, unknown> }>()

const formatted = computed(() => {
  if (typeof props.value === 'string') return props.value
  try {
    return JSON.stringify(props.value, null, 2)
  } catch (error) {
    return String(props.value)
  }
})

async function copy() {
  try {
    await navigator.clipboard.writeText(formatted.value)
  } catch {
    // TODO: add fallback copy
  }
}
</script>
