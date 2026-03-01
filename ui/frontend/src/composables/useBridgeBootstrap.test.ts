import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useBridgeBootstrap } from './useBridgeBootstrap'

function createBootstrap() {
  const bridge = ref<any>(null)
  const appVersion = ref('')
  let commBindCount = 0
  let scriptBindCount = 0
  let portsCount = 0
  let channelsCount = 0
  let protocolsCount = 0
  let settingsCount = 0

  const bootstrap = useBridgeBootstrap({
    bridge,
    appVersion,
    bindCommBridgeSignals: () => {
      commBindCount += 1
    },
    bindScriptBridgeSignals: () => {
      scriptBindCount += 1
    },
    refreshPorts: () => {
      portsCount += 1
    },
    refreshChannels: () => {
      channelsCount += 1
    },
    refreshProtocols: () => {
      protocolsCount += 1
    },
    loadSettings: () => {
      settingsCount += 1
    },
  })

  return {
    bridge,
    appVersion,
    bootstrap,
    getCounters: () => ({
      commBindCount,
      scriptBindCount,
      portsCount,
      channelsCount,
      protocolsCount,
      settingsCount,
    }),
  }
}

describe('useBridgeBootstrap', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('attaches bridge once and runs bind/refresh pipeline', () => {
    const { bridge, appVersion, bootstrap, getCounters } = createBootstrap()
    const candidate = {
      get_app_version: () => ' 1.2.3 ',
    }

    bootstrap.attachBridge(candidate)
    expect(bridge.value).toEqual(candidate)
    expect(appVersion.value).toBe('1.2.3')
    expect(getCounters()).toEqual({
      commBindCount: 1,
      scriptBindCount: 1,
      portsCount: 1,
      channelsCount: 1,
      protocolsCount: 1,
      settingsCount: 1,
    })

    bootstrap.attachBridge(candidate)
    expect(getCounters().commBindCount).toBe(1)
  })

  it('polls resolver and auto-stops after first attach', () => {
    vi.useFakeTimers()
    const { bridge, bootstrap, getCounters } = createBootstrap()
    let calls = 0
    const candidate = {}

    bootstrap.startBridgeBootstrap(() => {
      calls += 1
      return calls >= 2 ? candidate : null
    }, 100)

    vi.advanceTimersByTime(100)
    expect(bridge.value).toBe(null)
    vi.advanceTimersByTime(100)
    expect(bridge.value).toEqual(candidate)
    expect(getCounters().commBindCount).toBe(1)

    vi.advanceTimersByTime(300)
    expect(calls).toBe(2)
  })

  it('disposes polling timer safely', () => {
    vi.useFakeTimers()
    const { bootstrap } = createBootstrap()
    let calls = 0
    bootstrap.startBridgeBootstrap(() => {
      calls += 1
      return null
    }, 100)
    vi.advanceTimersByTime(100)
    expect(calls).toBe(1)
    bootstrap.disposeBridgeBootstrap()
    vi.advanceTimersByTime(300)
    expect(calls).toBe(1)
  })
})
