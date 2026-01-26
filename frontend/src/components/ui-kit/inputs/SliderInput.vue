<template>
  <div class="space-y-3">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div class="flex items-center gap-4">
      <input
        class="flex-1 h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-primary"
        type="range"
        :disabled="disabled"
        :value="modelValue"
        @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
      />
      <span class="text-xs font-mono font-bold text-primary bg-blue-50 px-2 py-1 rounded">{{ modelValue }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; modelValue: number; disabled?: boolean; hint?: string }>()
defineEmits<{ (e: 'update:modelValue', value: number): void }>()
</script>
