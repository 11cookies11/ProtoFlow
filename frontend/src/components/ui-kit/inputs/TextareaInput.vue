<template>
  <label class="space-y-2 block">
    <span class="text-xs font-bold text-slate-500">{{ label }}</span>
    <textarea
      class="w-full p-3 rounded-lg border-slate-200 text-sm focus:border-primary focus:ring-4 focus:ring-primary/10"
      rows="3"
      :placeholder="hint"
      :disabled="disabled"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
  </label>
</template>

<script setup lang="ts">
defineProps<{ label: string; modelValue: string; disabled?: boolean; hint?: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>
