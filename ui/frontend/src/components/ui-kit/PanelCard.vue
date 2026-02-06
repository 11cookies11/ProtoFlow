<template>
  <section class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <div v-if="title" class="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <h3 class="font-bold text-slate-700 text-sm">{{ title }}</h3>
        <span v-if="badgeText" :class="badgeClass" class="text-[10px] px-2 py-0.5 rounded font-bold">{{ badgeText }}</span>
      </div>
      <slot name="headerExtra"></slot>
    </div>
    <div class="p-6">
      <slot></slot>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title?: string
  badgeText?: string
  badgeTone?: 'blue' | 'emerald' | 'slate' | 'rose'
}>()

const badgeClass = computed(() => {
  const tone = props.badgeTone || 'blue'
  const map: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-700',
    emerald: 'bg-emerald-100 text-emerald-700',
    slate: 'bg-slate-100 text-slate-600',
    rose: 'bg-rose-100 text-rose-700',
  }
  return map[tone]
})
</script>
