<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-bold text-slate-700">{{ title }}</h3>
      <button class="text-xs text-slate-400 hover:text-slate-600" @click="copy">{{ tr('Copy') }}</button>
    </div>
    <pre class="text-[10px] font-mono leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-600 min-h-[160px]">
{{ formatted }}
    </pre>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

const props = defineProps<{ title: string; value: unknown }>()
const tr = inject('tr', (text: string) => text)

const formatted = computed(() => {
  if (props.value == null) return tr('未选择任何组件')
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
    // TODO: fallback
  }
}
</script>
