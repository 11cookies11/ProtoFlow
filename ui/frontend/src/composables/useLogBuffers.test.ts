import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useLogBuffers } from './useLogBuffers'

function createManager() {
  const commLogs = ref<any[]>([])
  const scriptLogs = ref<any[]>([])
  const commPaused = ref(false)
  const scriptRunning = ref(true)
  const scriptState = ref('running')
  const mgr = useLogBuffers({
    commLogs,
    scriptLogs,
    commPaused,
    scriptRunning,
    scriptState,
    maxCommLogs: 3,
    maxScriptLogs: 2,
  })
  return { commLogs, scriptLogs, commPaused, scriptRunning, scriptState, mgr }
}

describe('useLogBuffers', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('buffers comm logs and flushes in animation frame', () => {
    let rafCallback: FrameRequestCallback | null = null
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb: FrameRequestCallback) => {
      rafCallback = cb
      return 1
    })
    const { commLogs, mgr } = createManager()

    mgr.addCommLog('RX', 'PING')
    mgr.addCommLog('TX', { hex: 'AA BB', ts: 12 })
    expect(commLogs.value).toHaveLength(0)

    rafCallback?.(0)
    expect(commLogs.value).toHaveLength(2)
    expect(commLogs.value[0].text).toBe('PING')
    expect(commLogs.value[1].hex).toBe('AA BB')
  })

  it('respects pause and clears comm logs', () => {
    let rafCallback: FrameRequestCallback | null = null
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb: FrameRequestCallback) => {
      rafCallback = cb
      return 2
    })
    const { commLogs, commPaused, mgr } = createManager()
    commPaused.value = true

    mgr.addCommLog('RX', 'DROP')
    rafCallback?.(0)
    expect(commLogs.value).toHaveLength(0)

    mgr.toggleCommPaused()
    mgr.addCommLog('RX', 'KEEP')
    rafCallback?.(0)
    expect(commLogs.value).toHaveLength(1)

    mgr.clearCommLogs()
    expect(commLogs.value).toHaveLength(0)
  })

  it('deduplicates status text and marks status activity', () => {
    let rafCallback: FrameRequestCallback | null = null
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb: FrameRequestCallback) => {
      rafCallback = cb
      return 3
    })
    const { commLogs, mgr } = createManager()

    mgr.emitStatus('Connected: COM3', 1)
    mgr.emitStatus('Connected: COM3', 2)
    mgr.emitStatus('Error: timeout', 3)
    rafCallback?.(0)

    expect(mgr.hasStatusActivity.value).toBe(true)
    expect(commLogs.value.filter((item) => item.kind === 'STATUS')).toHaveLength(2)
  })

  it('flushes script logs and handles terminal states', () => {
    let rafCallback: FrameRequestCallback | null = null
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb: FrameRequestCallback) => {
      rafCallback = cb
      return 4
    })
    const { scriptLogs, scriptRunning, scriptState, mgr } = createManager()

    mgr.addScriptLog('line1')
    mgr.addScriptLog('Script finished')
    rafCallback?.(0)

    expect(scriptLogs.value).toHaveLength(2)
    expect(scriptRunning.value).toBe(false)
    expect(scriptState.value).toBe('idle')
  })

  it('disposes pending raf flush', () => {
    vi.useFakeTimers()
    const cancelSpy = vi.spyOn(window, 'cancelAnimationFrame')
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => 99)
    const { mgr } = createManager()

    mgr.addCommLog('RX', 'pending')
    mgr.disposeLogBuffers()
    expect(cancelSpy).toHaveBeenCalledWith(99)
  })
})
