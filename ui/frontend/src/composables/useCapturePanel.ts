import { computed, ref } from 'vue'

export function useCapturePanel() {
  const captureOpen = ref(false)
  const captureFilter = ref('all')
  const selectedFrame = ref<any>(null)

  const hasSelection = computed(() => Boolean(selectedFrame.value))

  function openCapture(defaultFrame: any = null) {
    captureOpen.value = true
    selectedFrame.value = defaultFrame
    captureFilter.value = 'all'
  }

  function closeCapture() {
    captureOpen.value = false
  }

  return {
    captureOpen,
    captureFilter,
    selectedFrame,
    hasSelection,
    openCapture,
    closeCapture,
  }
}
