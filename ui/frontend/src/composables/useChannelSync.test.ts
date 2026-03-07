import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useChannelSync } from './useChannelSync'

function createSync(bridgeValue: any = null) {
  const bridge = ref(bridgeValue)
  const channels = ref<any[]>([])
  const connectionInfo = ref({ state: 'disconnected', detail: '' })
  const isConnecting = ref(false)
  const statuses: string[] = []
  const sync = useChannelSync({
    bridge,
    channels,
    connectionInfo,
    isConnecting,
    emitStatus: (text: string) => statuses.push(text),
  })
  return { bridge, channels, connectionInfo, isConnecting, statuses, sync }
}

describe('useChannelSync', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('updates connection info for connected and error channel', () => {
    const { channels, connectionInfo, isConnecting, statuses, sync } = createSync()
    isConnecting.value = true

    sync.setChannels([{ status: 'connected', address: '127.0.0.1:9000' }])
    expect(channels.value).toHaveLength(1)
    expect(connectionInfo.value).toEqual({ state: 'connected', detail: '127.0.0.1:9000' })
    expect(isConnecting.value).toBe(false)
    expect(statuses[0]).toContain('Connected:')

    isConnecting.value = true
    sync.setChannels([{ status: 'error', error: 'timeout' }])
    expect(connectionInfo.value).toEqual({ state: 'error', detail: 'timeout' })
    expect(isConnecting.value).toBe(false)
    expect(statuses[1]).toBe('Error: timeout')
  })

  it('coalesces scheduleSetChannels updates to the latest item', () => {
    let rafCallback: FrameRequestCallback | null = null
    const rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb: FrameRequestCallback) => {
      rafCallback = cb
      return 1
    })

    const { connectionInfo, sync } = createSync()
    sync.scheduleSetChannels([{ status: 'error', error: 'old' }])
    sync.scheduleSetChannels([{ status: 'connected', port: 'COM3' }])
    expect(rafSpy).toHaveBeenCalledTimes(1)
    expect(connectionInfo.value.state).toBe('disconnected')

    rafCallback?.(0)
    expect(connectionInfo.value).toEqual({ state: 'connected', detail: 'COM3' })
  })

  it('debounces channel refresh by timeout', () => {
    vi.useFakeTimers()
    let listCalls = 0
    const { sync, channels } = createSync({
      list_channels: () => {
        listCalls += 1
        return [{ status: 'connected', type: 'serial' }]
      },
    })

    sync.scheduleChannelRefresh()
    sync.scheduleChannelRefresh()
    vi.advanceTimersByTime(149)
    expect(listCalls).toBe(0)

    vi.advanceTimersByTime(1)
    expect(listCalls).toBe(1)
    expect(channels.value[0]?.status).toBe('connected')
  })

  it('refreshes channels and supports promise bridge result', async () => {
    const { sync, channels } = createSync({
      list_channels: () => Promise.resolve([{ status: 'connected', address: 'A' }]),
    })
    sync.refreshChannels()
    await Promise.resolve()
    expect(channels.value[0]?.address).toBe('A')
  })
})
