import type { Ref } from 'vue'
import { withResult } from '../utils/withResult'

type ConnectionInfo = {
  state: string
  detail: string
}

type UseChannelSyncOptions = {
  bridge: Ref<any>
  channels: Ref<any[]>
  connectionInfo: Ref<ConnectionInfo>
  isConnecting: Ref<boolean>
  emitStatus: (text: string, ts: number) => void
}

export function useChannelSync(options: UseChannelSyncOptions) {
  let channelRefreshTimer: number | null = null
  let channelUpdateRaf = 0
  let pendingChannelItems: any = null

  function setChannels(items: any) {
    options.channels.value = Array.isArray(items) ? items : []
    const primary = options.channels.value[0]
    if (!primary) return
    if (primary.status === 'connected') {
      const target = primary.address || primary.port || primary.type || ''
      options.emitStatus(`Connected: ${target}`, Date.now() / 1000)
      options.connectionInfo.value = {
        state: 'connected',
        detail: primary.address || primary.port || primary.type || '',
      }
      options.isConnecting.value = false
      return
    }
    if (primary.status === 'error') {
      options.emitStatus(`Error: ${primary.error || ''}`, Date.now() / 1000)
      options.connectionInfo.value = { state: 'error', detail: primary.error || '' }
      options.isConnecting.value = false
    }
  }

  function scheduleSetChannels(items: any) {
    pendingChannelItems = items
    if (channelUpdateRaf) return
    channelUpdateRaf = window.requestAnimationFrame(() => {
      channelUpdateRaf = 0
      const next = pendingChannelItems
      pendingChannelItems = null
      setChannels(next)
    })
  }

  function refreshChannels() {
    if (!options.bridge.value || !options.bridge.value.list_channels) return
    withResult(options.bridge.value.list_channels(), (items) => {
      setChannels(items)
    })
  }

  function scheduleChannelRefresh() {
    if (channelRefreshTimer) return
    channelRefreshTimer = window.setTimeout(() => {
      channelRefreshTimer = null
      refreshChannels()
    }, 150)
  }

  function disposeChannelSync() {
    if (channelRefreshTimer) {
      window.clearTimeout(channelRefreshTimer)
      channelRefreshTimer = null
    }
    if (channelUpdateRaf) {
      window.cancelAnimationFrame(channelUpdateRaf)
      channelUpdateRaf = 0
    }
    pendingChannelItems = null
  }

  return {
    setChannels,
    scheduleSetChannels,
    refreshChannels,
    scheduleChannelRefresh,
    disposeChannelSync,
  }
}
