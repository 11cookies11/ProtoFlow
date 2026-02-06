<template>
  <label class="space-y-2 block">
    <span class="text-xs font-bold text-slate-500">{{ label }}</span>
    <select
      class="w-full h-10 px-3 rounded-lg border-slate-200 text-sm bg-slate-50"
      :disabled="disabled"
      :value="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
    </select>
  </label>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  modelValue: string
  options: { label: string; value: string }[]
  disabled?: boolean
  hint?: string
}>()

defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>
