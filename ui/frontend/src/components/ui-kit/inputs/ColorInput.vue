<template>
  <div class="space-y-2">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div class="flex items-center gap-3">
      <input
        class="size-10 rounded-lg border-none p-0 cursor-pointer overflow-hidden"
        type="color"
        :disabled="disabled"
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      <span class="text-xs font-mono text-slate-500">HEX: {{ modelValue.toUpperCase() }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; modelValue: string; disabled?: boolean; hint?: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>
