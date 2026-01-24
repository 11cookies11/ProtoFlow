<template>
  <div
    class="flex gap-4"
    :class="orientation === 'vertical' ? 'flex-col' : 'flex-row'"
  >
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
defineProps<{ orientation: 'horizontal' | 'vertical' }>()
</script>
