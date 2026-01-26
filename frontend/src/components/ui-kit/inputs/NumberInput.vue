<template>
  <label class="space-y-2 block">
    <span class="text-xs font-bold text-slate-500">{{ label }}</span>
    <input
      class="w-full h-10 px-3 rounded-lg border-slate-200 text-sm focus:border-primary focus:ring-4 focus:ring-primary/10"
      type="number"
      :placeholder="hint"
      :disabled="disabled"
      :value="modelValue"
      @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
    />
  </label>
</template>

<script setup lang="ts">
defineProps<{ label: string; modelValue: number; disabled?: boolean; hint?: string }>()
defineEmits<{ (e: 'update:modelValue', value: number): void }>()
</script>
