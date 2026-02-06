<template>
  <div class="border border-dashed border-slate-300 bg-slate-50 rounded-lg p-4 text-xs text-slate-500">
    <div class="font-bold text-slate-700">Unknown Widget</div>
    <div>ID: {{ widgetId }}</div>
    <div>Type: {{ widgetType }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ widgetId: string; widgetType: string }>()
</script>
