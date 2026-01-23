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
      <span class="text-xs text-slate-300 ml-1 italic">输入搜索...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ label: string; modelValue: string[]; disabled?: boolean; hint?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string[]): void }>()

function removeChip(chip: string) {
  if (props.disabled) return
  emit('update:modelValue', props.modelValue.filter((item) => item !== chip))
  // TODO: emit add/remove events once selection logic is wired
}
</script>
