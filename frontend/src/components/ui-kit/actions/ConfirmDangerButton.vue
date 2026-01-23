<template>
  <div class="relative group">
    <button
      class="w-full py-2.5 bg-rose-50 text-rose-600 border border-rose-200 rounded-lg text-sm font-bold flex items-center justify-center gap-2 hover:bg-rose-100 transition-all"
      @click="$emit('confirm')"
    >
      <span class="material-symbols-outlined !text-lg">delete_forever</span>
      {{ label }}
    </button>
    <div class="absolute -top-12 left-1/2 -translate-x-1/2 hidden group-hover:flex items-center gap-2 px-3 py-1.5 bg-slate-900 text-white text-[10px] rounded-lg shadow-xl whitespace-nowrap">
      <span class="material-symbols-outlined !text-[12px] text-amber-400">warning</span>
      {{ hint }}
      <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900 rotate-45"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; hint: string }>()
defineEmits<{ (e: 'confirm'): void }>()
</script>
