<template>
  <div class="space-y-2">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div class="flex gap-4">
      <label v-for="option in options" :key="option.value" class="flex items-center gap-2 cursor-pointer">
        <input
          class="text-primary focus:ring-primary/20 border-slate-300"
          type="radio"
          :value="option.value"
          :checked="modelValue === option.value"
          :disabled="disabled"
          @change="$emit('update:modelValue', option.value)"
        />
        <span class="text-sm">{{ option.label }}</span>
      </label>
    </div>
  </div>
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
