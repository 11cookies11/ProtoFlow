<template>
  <div class="space-y-2">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div class="flex gap-4">
      <label v-for="option in options" :key="option.value" class="flex items-center gap-2 cursor-pointer">
        <input
          class="rounded text-primary focus:ring-primary/20 border-slate-300"
          type="checkbox"
          :value="option.value"
          :checked="modelValue.includes(option.value)"
          :disabled="disabled"
          @change="toggle(option.value)"
        />
        <span class="text-sm">{{ option.label }}</span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  label: string
  modelValue: string[]
  options: { label: string; value: string }[]
  disabled?: boolean
  hint?: string
}>()

const emit = defineEmits<{ (e: 'update:modelValue', value: string[]): void }>()

function toggle(value: string) {
  if (props.disabled) return
  const next = props.modelValue.includes(value)
    ? props.modelValue.filter((item) => item !== value)
    : [...props.modelValue, value]
  emit('update:modelValue', next)
}
</script>
