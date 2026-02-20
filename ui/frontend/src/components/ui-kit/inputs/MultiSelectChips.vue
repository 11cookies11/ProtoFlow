<template>
  <div class="space-y-2">
    <label class="text-xs font-bold text-slate-500">{{ label }}</label>
    <div class="w-full p-2 border border-slate-200 rounded-lg flex flex-wrap gap-2 min-h-[40px] items-center">
      <span
        v-for="chip in modelValue"
        :key="chip"
        class="flex items-center gap-1 px-2 py-0.5 bg-slate-100 rounded text-xs font-medium text-slate-600"
      >
        {{ chip }}
        <span class="material-symbols-outlined !text-[12px] cursor-pointer" @click="removeChip(chip)">close</span>
      </span>
      <input
        v-model="draft"
        class="min-w-[120px] flex-1 text-xs bg-transparent border-none outline-none text-slate-600 placeholder-slate-300"
        :placeholder="tr('输入后回车添加...')"
        :disabled="disabled"
        @keydown.enter.prevent="addChip"
        @keydown.tab.prevent="addChip"
        @blur="addChip"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref } from 'vue'

const props = defineProps<{ label: string; modelValue: string[]; disabled?: boolean; hint?: string }>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
  (e: 'add', value: string): void
  (e: 'remove', value: string): void
}>()
const tr = inject('tr', (text) => text)
const draft = ref('')

function removeChip(chip: string) {
  if (props.disabled) return
  emit('update:modelValue', props.modelValue.filter((item) => item !== chip))
  emit('remove', chip)
}

function addChip() {
  if (props.disabled) return
  const value = draft.value.trim()
  if (!value) return
  if (props.modelValue.includes(value)) {
    draft.value = ''
    return
  }
  emit('update:modelValue', [...props.modelValue, value])
  emit('add', value)
  draft.value = ''
}
</script>
