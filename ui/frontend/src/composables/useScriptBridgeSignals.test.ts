import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useScriptBridgeSignals } from './useScriptBridgeSignals'

function createSignal() {
  const listeners: Array<(payload: any) => void> = []
  return {
    connect(fn: (payload: any) => void) {
      listeners.push(fn)
    },
    emit(payload: any) {
      listeners.forEach((fn) => fn(payload))
    },
  }
}

describe('useScriptBridgeSignals', () => {
  it('binds script log and channel update handlers', () => {
    const logs: any[] = []
    const channels: any[] = []
    const scriptLog = createSignal()
    const channelUpdate = createSignal()

    const mgr = useScriptBridgeSignals({
      scriptRunning: ref(false),
      scriptState: ref('idle'),
      scriptProgress: ref(0),
      addScriptLog: (line) => logs.push(line),
      scheduleSetChannels: (items) => channels.push(items),
    })

    mgr.bindScriptBridgeSignals({
      script_log: scriptLog,
      channel_update: channelUpdate,
    })

    scriptLog.emit('line-a')
    channelUpdate.emit([1, 2, 3])
    expect(logs).toEqual(['line-a'])
    expect(channels).toEqual([[1, 2, 3]])
  })

  it('handles script state transitions and progress', () => {
    const scriptRunning = ref(false)
    const scriptState = ref('idle')
    const scriptProgress = ref(0)
    const scriptStateSignal = createSignal()
    const scriptProgressSignal = createSignal()

    const mgr = useScriptBridgeSignals({
      scriptRunning,
      scriptState,
      scriptProgress,
      addScriptLog: () => {},
      scheduleSetChannels: () => {},
    })

    mgr.bindScriptBridgeSignals({
      script_state: scriptStateSignal,
      script_progress: scriptProgressSignal,
    })

    scriptStateSignal.emit('__running__')
    expect(scriptRunning.value).toBe(true)
    expect(scriptState.value).toBe('running')

    scriptProgressSignal.emit(55)
    expect(scriptProgress.value).toBe(55)

    scriptStateSignal.emit('__finished__')
    expect(scriptRunning.value).toBe(false)
    expect(scriptState.value).toBe('idle')
    expect(scriptProgress.value).toBe(100)
  })
})
