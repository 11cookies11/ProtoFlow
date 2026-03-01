import type { Ref } from 'vue'

type UseBridgeBootstrapOptions = {
  bridge: Ref<any>
  appVersion: Ref<string>
  bindCommBridgeSignals: (obj: any) => void
  bindScriptBridgeSignals: (obj: any) => void
  refreshPorts: () => void
  refreshChannels: () => void
  refreshProtocols: () => void
  loadSettings: () => void
}

function withResult(value: any, handler: (payload: any) => void) {
  if (value && typeof value.then === 'function') {
    value.then(handler)
    return
  }
  handler(value)
}

export function useBridgeBootstrap(options: UseBridgeBootstrapOptions) {
  let attachedBridge: any = null
  let bridgePollTimer: number | null = null

  function attachBridge(obj: any) {
    if (!obj || attachedBridge === obj) return
    attachedBridge = obj
    options.bridge.value = obj
    if (obj.get_app_version) {
      withResult(obj.get_app_version(), (value) => {
        if (value) {
          options.appVersion.value = String(value).trim()
        }
      })
    }
    options.bindCommBridgeSignals(obj)
    options.bindScriptBridgeSignals(obj)
    options.refreshPorts()
    options.refreshChannels()
    options.refreshProtocols()
    options.loadSettings()
  }

  function startBridgeBootstrap(resolveBridge: () => any = () => (window as any).bridge, intervalMs = 200) {
    if (bridgePollTimer) return
    bridgePollTimer = window.setInterval(() => {
      const candidate = resolveBridge()
      if (!candidate) return
      attachBridge(candidate)
      if (bridgePollTimer) {
        window.clearInterval(bridgePollTimer)
        bridgePollTimer = null
      }
    }, intervalMs)
  }

  function disposeBridgeBootstrap() {
    if (!bridgePollTimer) return
    window.clearInterval(bridgePollTimer)
    bridgePollTimer = null
  }

  return {
    attachBridge,
    startBridgeBootstrap,
    disposeBridgeBootstrap,
  }
}
