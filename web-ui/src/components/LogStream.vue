<script setup>
import { ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
  mode: { type: String, default: 'comm' },
  formatTime: { type: Function, default: null },
  formatPayload: { type: Function, default: null },
})

const rootEl = ref(null)

defineExpose({ rootEl })
</script>

<template>
  <div ref="rootEl" class="log-stream" :class="{ compact }">
    <template v-if="mode === 'text'">
      <div class="log-line" v-for="line in items" :key="line.id">
        {{ line.text }}
      </div>
    </template>
    <template v-else>
      <div class="log-line" v-for="item in items" :key="item.id">
        <span class="log-time">{{ formatTime ? formatTime(item.ts) : '' }}</span>
        <span class="log-kind" :class="`kind-${item.kind?.toLowerCase()}`">{{ item.kind }}</span>
        <span class="log-text" :class="`text-${item.kind?.toLowerCase()}`">
          {{ formatPayload ? formatPayload(item) : item.text }}
        </span>
      </div>
    </template>
  </div>
</template>
