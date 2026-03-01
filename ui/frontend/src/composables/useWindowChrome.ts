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
  let armedListenersAttached = false

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
    if (event.detail && event.detail > 1) return
    dragArmed.value = true
    dragStarted.value = false
    dragStart.value = { x: event.screenX, y: event.screenY }
    attachArmedListeners()
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
    detachArmedListeners()
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

  function handleDragEnd(event: any) {
    if (!draggingWindow.value) return
    applyWindowSnap(event)
  }

  function handleArmedMouseUp() {
    if (!draggingWindow.value) {
      dragArmed.value = false
      dragStarted.value = false
    }
    detachArmedListeners()
  }

  function attachArmedListeners() {
    if (armedListenersAttached) return
    armedListenersAttached = true
    window.addEventListener('mousemove', maybeStartWindowMove)
    window.addEventListener('mouseup', handleArmedMouseUp)
    window.addEventListener('blur', handleArmedMouseUp)
  }

  function detachArmedListeners() {
    if (!armedListenersAttached) return
    armedListenersAttached = false
    window.removeEventListener('mousemove', maybeStartWindowMove)
    window.removeEventListener('mouseup', handleArmedMouseUp)
    window.removeEventListener('blur', handleArmedMouseUp)
  }

  function attachDragListeners() {
    window.addEventListener('mouseup', handleDragEnd)
    window.addEventListener('blur', handleDragCancel)
    document.addEventListener('visibilitychange', handleDragCancel)
  }

  function detachDragListeners() {
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
    unlockSidebarWidth()
    document.body.classList.remove('dragging-window')
    document.body.classList.remove('resizing')
    options.unlockPageScroll()
    detachArmedListeners()
    detachDragListeners()
  }

  function disposeWindowChrome() {
    clearDragState()
  }

  function cancelWindowMoveArm() {
    if (draggingWindow.value) return
    dragArmed.value = false
    dragStarted.value = false
    detachArmedListeners()
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
    cancelWindowMoveArm,
    disposeWindowChrome,
  }
}
