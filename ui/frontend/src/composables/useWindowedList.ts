import { computed, ref, type ComputedRef } from 'vue'

export type WindowedListOptions = {
  itemCount: ComputedRef<number>
  rowHeight: number | ComputedRef<number>
  overscan?: number
  minVisibleRows?: number
}

export function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

export function calculateWindowRange(
  itemCount: number,
  rowHeight: number,
  viewportHeight: number,
  scrollTop: number,
  overscan = 10,
  minVisibleRows = 20
) {
  if (itemCount <= 0 || rowHeight <= 0) {
    return { start: 0, end: 0, topOffset: 0, bottomOffset: 0 }
  }
  const visibleRows = Math.max(minVisibleRows, Math.ceil(viewportHeight / rowHeight) || minVisibleRows)
  const rawStart = Math.floor(scrollTop / rowHeight) - overscan
  const start = clamp(rawStart, 0, Math.max(0, itemCount - 1))
  const end = clamp(start + visibleRows + overscan * 2, start, itemCount)
  const topOffset = start * rowHeight
  const bottomOffset = Math.max(0, (itemCount - end) * rowHeight)
  return { start, end, topOffset, bottomOffset }
}

export function useWindowedList(options: WindowedListOptions) {
  const viewportHeight = ref(0)
  const scrollTop = ref(0)
  const overscan = options.overscan ?? 10
  const minVisibleRows = options.minVisibleRows ?? 20

  const range = computed(() =>
    calculateWindowRange(
      options.itemCount.value,
      typeof options.rowHeight === 'number' ? options.rowHeight : options.rowHeight.value,
      viewportHeight.value,
      scrollTop.value,
      overscan,
      minVisibleRows
    )
  )

  function updateViewport(nextHeight: number, nextScrollTop: number) {
    viewportHeight.value = Math.max(0, Number(nextHeight) || 0)
    scrollTop.value = Math.max(0, Number(nextScrollTop) || 0)
  }

  function reset() {
    scrollTop.value = 0
  }

  return {
    range,
    updateViewport,
    reset,
  }
}
