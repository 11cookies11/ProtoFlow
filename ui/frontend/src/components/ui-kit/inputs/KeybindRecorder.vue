<template>
  <div class="space-y-2">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div
      class="flex items-center justify-between h-10 px-4 bg-slate-900 text-white rounded-lg group cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all"
      @click="$emit('startRecord')"
    >
      <div class="flex gap-1">
        <kbd v-for="(key, index) in keys" :key="index" class="px-1.5 py-0.5 bg-slate-700 rounded text-[10px] font-bold">
          {{ key }}
        </kbd>
      </div>
      <span class="material-symbols-outlined !text-sm text-slate-500 group-hover:text-white">keyboard</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ label: string; modelValue: string[]; disabled?: boolean; hint?: string }>()

defineEmits<{ (e: 'startRecord'): void }>()

const keys = props.modelValue.length ? props.modelValue : ['Ctrl', 'Shift', 'P']
</script>
