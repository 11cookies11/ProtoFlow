import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useWindowChrome } from './useWindowChrome'

describe('useWindowChrome', () => {
  it('starts window move when drag threshold reached', () => {
    let moveAt = 0
    let lockCount = 0
    let unlockCount = 0
    const sidebarRef = ref({
      getBoundingClientRect: () => ({ width: 240 }),
    })
    const chrome = useWindowChrome({
      bridge: ref({
        window_start_move_at: () => {
          moveAt += 1
        },
      }),
      sidebarRef,
      lockPageScroll: () => {
        lockCount += 1
      },
      unlockPageScroll: () => {
        unlockCount += 1
      },
    })

    chrome.armWindowMove({ screenX: 10, screenY: 10 })
    chrome.maybeStartWindowMove({ screenX: 30, screenY: 30 })

    expect(moveAt).toBe(1)
    expect(lockCount).toBe(1)
    expect(chrome.draggingWindow.value).toBe(true)

    chrome.applyWindowSnap({ screenX: 31, screenY: 32 })
    expect(chrome.draggingWindow.value).toBe(false)
    expect(unlockCount).toBeGreaterThanOrEqual(1)
  })

  it('invokes bridge actions for window controls', () => {
    let minimized = 0
    let maximized = 0
    let closed = 0
    let menu = 0
    let resized = 0
    let snapped = 0

    const chrome = useWindowChrome({
      bridge: ref({
        window_minimize: () => {
          minimized += 1
        },
        window_toggle_maximize: () => {
          maximized += 1
        },
        window_close: () => {
          closed += 1
        },
        window_show_system_menu: () => {
          menu += 1
        },
        window_start_resize: () => {
          resized += 1
        },
        window_apply_snap: () => {
          snapped += 1
        },
      }),
      sidebarRef: ref(null),
      lockPageScroll: () => {},
      unlockPageScroll: () => {},
    })

    chrome.armWindowMove({ screenX: 1, screenY: 1 })
    chrome.maybeStartWindowMove({ screenX: 20, screenY: 20 })
    chrome.applyWindowSnap({ screenX: 50, screenY: 50 })
    chrome.minimizeWindow()
    chrome.toggleMaximize()
    chrome.closeWindow()
    chrome.showSystemMenu({ screenX: 4, screenY: 5 })
    chrome.startResize('left', { screenX: 1, screenY: 1 })

    expect(minimized).toBe(1)
    expect(maximized).toBe(1)
    expect(closed).toBe(1)
    expect(menu).toBe(1)
    expect(resized).toBe(1)
    expect(snapped).toBe(1)
  })

  it('shows snap preview near top edge while dragging', async () => {
    let rafCallback: FrameRequestCallback | null = null
    const originalRaf = window.requestAnimationFrame
    window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
      rafCallback = cb
      return 1
    }) as typeof window.requestAnimationFrame

    const chrome = useWindowChrome({
      bridge: ref({
        window_start_move_at: () => {},
        window_apply_snap: () => {},
      }),
      sidebarRef: ref(null),
      lockPageScroll: () => {},
      unlockPageScroll: () => {},
    })

    chrome.armWindowMove({ screenX: 10, screenY: 10 })
    chrome.maybeStartWindowMove({ screenX: 30, screenY: 30 })
    window.dispatchEvent(
      new MouseEvent('mousemove', { clientX: 20, clientY: 5, screenX: 20, screenY: 5, buttons: 1, bubbles: true })
    )
    if (rafCallback) {
      rafCallback(0)
    }

    expect(chrome.snapPreview.value).toBe('max')

    chrome.disposeWindowChrome()
    window.requestAnimationFrame = originalRaf
  })

  it('starts window move from global mousemove after titlebar mousedown', () => {
    let moveAt = 0
    const chrome = useWindowChrome({
      bridge: ref({
        window_start_move_at: () => {
          moveAt += 1
        },
      }),
      sidebarRef: ref(null),
      lockPageScroll: () => {},
      unlockPageScroll: () => {},
    })

    chrome.armWindowMove({ screenX: 10, screenY: 10 })
    window.dispatchEvent(new MouseEvent('mousemove', { screenX: 26, screenY: 26, buttons: 1, bubbles: true }))

    expect(moveAt).toBe(1)
    expect(chrome.draggingWindow.value).toBe(true)

    chrome.disposeWindowChrome()
  })
})
