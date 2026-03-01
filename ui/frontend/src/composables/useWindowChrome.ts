import { ref, type Ref } from 'vue'

type UseWindowChromeOptions = {
  bridge: Ref<any>
  sidebarRef: Ref<any>
  lockPageScroll: () => void
  unlockPageScroll: () => void
}

export function useWindowChrome(options: UseWindowChromeOptions) {
  const draggingWindow = ref(false)
  const dragArmed = ref(false)
  const dragStarted = ref(false)
  const dragStart = ref({ x: 0, y: 0 })
  const snapPreview = ref('')
  const enableSnapPreview = ref(false)
  let snapPreviewRaf = 0
  let pendingSnapPreview: any = null

  function lockSidebarWidth() {
    const sidebar = options.sidebarRef.value
    if (!sidebar || !sidebar.getBoundingClientRect) return
    const width = Math.round(sidebar.getBoundingClientRect().width)
    document.documentElement.style.setProperty('--sidebar-width', `${width}px`)
  }

  function unlockSidebarWidth() {
    document.documentElement.style.removeProperty('--sidebar-width')
  }

  function armWindowMove(event: any) {
    if (!event) return
    dragArmed.value = true
    dragStarted.value = false
    dragStart.value = { x: event.screenX, y: event.screenY }
  }

  function maybeStartWindowMove(event: any) {
    if (!dragArmed.value || dragStarted.value || !event) return
    const dx = Math.abs(event.screenX - dragStart.value.x)
    const dy = Math.abs(event.screenY - dragStart.value.y)
    if (dx < 10 && dy < 10) return
    lockSidebarWidth()
    if (options.bridge.value) {
      if (options.bridge.value.window_start_move_at) {
        options.bridge.value.window_start_move_at(Math.round(event.screenX), Math.round(event.screenY))
      } else if (options.bridge.value.window_start_move) {
        options.bridge.value.window_start_move()
      }
    }
    dragStarted.value = true
    draggingWindow.value = true
    document.body.classList.add('dragging-window')
    options.lockPageScroll()
    snapPreview.value = ''
    attachDragListeners()
  }

  function minimizeWindow() {
    if (options.bridge.value && options.bridge.value.window_minimize) {
      options.bridge.value.window_minimize()
    }
  }

  function toggleMaximize() {
    if (options.bridge.value && options.bridge.value.window_toggle_maximize) {
      options.bridge.value.window_toggle_maximize()
    }
  }

  function closeWindow() {
    if (options.bridge.value && options.bridge.value.window_close) {
      options.bridge.value.window_close()
    }
  }

  function applyWindowSnap(event: any) {
    if (options.bridge.value && event && dragStarted.value && options.bridge.value.window_apply_snap) {
      options.bridge.value.window_apply_snap(Math.round(event.screenX), Math.round(event.screenY))
    }
    clearDragState()
  }

  function showSystemMenu(event: any) {
    if (options.bridge.value && event && options.bridge.value.window_show_system_menu) {
      options.bridge.value.window_show_system_menu(Math.round(event.screenX), Math.round(event.screenY))
    }
  }

  function startResize(edge: string, event: any) {
    if (!options.bridge.value || !edge || !event || !options.bridge.value.window_start_resize) return
    document.body.classList.add('resizing')
    options.lockPageScroll()
    options.bridge.value.window_start_resize(edge)
  }

  function scheduleSnapPreview(event: any) {
    if (!event) return
    pendingSnapPreview = {
      x: event.clientX,
      y: event.clientY,
      screenX: event.screenX,
      screenY: event.screenY,
      buttons: event.buttons,
    }
    if (snapPreviewRaf) return
    snapPreviewRaf = window.requestAnimationFrame(() => {
      snapPreviewRaf = 0
      if (!pendingSnapPreview) return
      const payload = pendingSnapPreview
      pendingSnapPreview = null
      updateSnapPreview(payload)
    })
  }

  function updateSnapPreview(payload: any) {
    if (!draggingWindow.value || !payload) return
    if (payload.buttons !== 1) {
      applyWindowSnap(payload)
      return
    }
    if (!enableSnapPreview.value) {
      snapPreview.value = ''
      return
    }
    const margin = 24
    const x = payload.x
    const y = payload.y
    const width = window.innerWidth
    if (y <= margin) {
      snapPreview.value = 'max'
    } else if (x <= margin) {
      snapPreview.value = 'left'
    } else if (x >= width - margin) {
      snapPreview.value = 'right'
    } else {
      snapPreview.value = ''
    }
  }

  function handleDragEnd(event: any) {
    if (!draggingWindow.value) return
    applyWindowSnap(event)
  }

  function attachDragListeners() {
    window.addEventListener('mousemove', scheduleSnapPreview)
    window.addEventListener('mouseup', handleDragEnd)
    window.addEventListener('blur', handleDragCancel)
    document.addEventListener('visibilitychange', handleDragCancel)
  }

  function detachDragListeners() {
    window.removeEventListener('mousemove', scheduleSnapPreview)
    window.removeEventListener('mouseup', handleDragEnd)
    window.removeEventListener('blur', handleDragCancel)
    document.removeEventListener('visibilitychange', handleDragCancel)
  }

  function handleDragCancel() {
    clearDragState()
  }

  function clearDragState() {
    draggingWindow.value = false
    dragArmed.value = false
    dragStarted.value = false
    snapPreview.value = ''
    pendingSnapPreview = null
    unlockSidebarWidth()
    if (snapPreviewRaf) {
      window.cancelAnimationFrame(snapPreviewRaf)
      snapPreviewRaf = 0
    }
    document.body.classList.remove('dragging-window')
    document.body.classList.remove('resizing')
    options.unlockPageScroll()
    detachDragListeners()
  }

  function disposeWindowChrome() {
    clearDragState()
  }

  return {
    draggingWindow,
    snapPreview,
    armWindowMove,
    maybeStartWindowMove,
    minimizeWindow,
    toggleMaximize,
    closeWindow,
    applyWindowSnap,
    showSystemMenu,
    startResize,
    disposeWindowChrome,
  }
}
