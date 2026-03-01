<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useWindowedList } from '@/composables/useWindowedList'

const props = defineProps({
  items: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
  mode: { type: String, default: 'comm' },
  formatTime: { type: Function, default: null },
  formatPayload: { type: Function, default: null },
  virtualize: { type: Boolean, default: true },
  virtualThreshold: { type: Number, default: 160 },
  rowHeight: { type: Number, default: 0 },
})

const rootEl = ref(null)
const itemCount = computed(() => (Array.isArray(props.items) ? props.items.length : 0))
const effectiveRowHeight = computed(() => {
  if (props.rowHeight > 0) return props.rowHeight
  if (props.mode === 'text') return props.compact ? 18 : 22
  return props.compact ? 22 : 28
})
const shouldVirtualize = computed(() => props.virtualize && itemCount.value > props.virtualThreshold)
const windowed = useWindowedList({
  itemCount,
  rowHeight: effectiveRowHeight,
  overscan: 12,
  minVisibleRows: 24,
})
const visibleItems = computed(() => {
  if (!shouldVirtualize.value) return props.items
  const { start, end } = windowed.range.value
  return props.items.slice(start, end)
})

function syncWindow() {
  if (!rootEl.value) return
  windowed.updateViewport(rootEl.value.clientHeight || 0, rootEl.value.scrollTop || 0)
}

watch(
  () => itemCount.value,
  () => {
    nextTick(() => syncWindow())
  }
)

onMounted(() => {
  nextTick(() => syncWindow())
  window.addEventListener('resize', syncWindow)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncWindow)
})

defineExpose({ rootEl })
</script>

<template>
  <div ref="rootEl" class="log-stream" :class="{ compact }" @scroll.passive="syncWindow">
    <div
      v-if="shouldVirtualize && windowed.range.topOffset > 0"
      class="log-spacer"
      :style="{ height: `${windowed.range.topOffset}px` }"
    ></div>
    <template v-if="mode === 'text'">
      <div class="log-line" v-for="(line, idx) in visibleItems" :key="line?.id ?? `${windowed.range.start + idx}`">
        {{ line.text }}
      </div>
    </template>
    <template v-else>
      <div class="log-line" v-for="(item, idx) in visibleItems" :key="item?.id ?? `${windowed.range.start + idx}`">
        <span class="log-time">{{ formatTime ? formatTime(item.ts) : '' }}</span>
        <span class="log-kind" :class="`kind-${item.kind?.toLowerCase()}`">{{ item.kind }}</span>
        <span class="log-text" :class="`text-${item.kind?.toLowerCase()}`">
          {{ formatPayload ? formatPayload(item) : item.text }}
        </span>
      </div>
    </template>
    <div
      v-if="shouldVirtualize && windowed.range.bottomOffset > 0"
      class="log-spacer"
      :style="{ height: `${windowed.range.bottomOffset}px` }"
    ></div>
  </div>
</template>
