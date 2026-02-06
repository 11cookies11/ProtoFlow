<template>
  <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
    <label class="text-sm font-medium text-slate-700">{{ label }}</label>
    <button
      class="relative inline-flex h-6 w-11 items-center rounded-full transition"
      :class="modelValue ? 'bg-primary' : 'bg-slate-300'"
      :disabled="disabled"
      @click="$emit('update:modelValue', !modelValue)"
    >
      <span
        class="inline-block h-4 w-4 transform rounded-full bg-white transition"
        :class="modelValue ? 'translate-x-6' : 'translate-x-1'"
      ></span>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; modelValue: boolean; disabled?: boolean; hint?: string }>()
defineEmits<{ (e: 'update:modelValue', value: boolean): void }>()
</script>
