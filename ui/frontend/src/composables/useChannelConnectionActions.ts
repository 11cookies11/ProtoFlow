import type { Ref } from 'vue'

type UseChannelConnectionActionsOptions = {
  bridge: Ref<any>
  isConnecting: Ref<boolean>
  isConnected: Readonly<Ref<boolean>>
  selectedPort: Ref<string>
  baud: Ref<number>
  tcpHost: Ref<string>
  tcpPort: Ref<number>
  channelMode: Ref<string>
  resolveSerialPort: (value: string) => string
  selectChannelPort: (item: string) => void
}

export function useChannelConnectionActions(options: UseChannelConnectionActionsOptions) {
  function selectPort(item: string) {
    if (!item) return
    options.selectChannelPort(item)
    options.channelMode.value = 'serial'
  }

  function connectSerial() {
    if (!options.bridge.value) return
    if (options.isConnecting.value || options.isConnected.value) return
    const targetPort = options.resolveSerialPort(options.selectedPort.value)
    if (!targetPort) return
    options.selectedPort.value = targetPort
    options.isConnecting.value = true
    options.bridge.value.connect_serial(targetPort, Number(options.baud.value))
  }

  function connectTcp() {
    if (!options.bridge.value) return
    if (options.isConnecting.value || options.isConnected.value) return
    options.isConnecting.value = true
    options.bridge.value.connect_tcp(options.tcpHost.value, Number(options.tcpPort.value))
  }

  function connectPrimary() {
    if (options.channelMode.value === 'tcp') {
      connectTcp()
      return
    }
    connectSerial()
  }

  function disconnect() {
    if (!options.bridge.value) return
    options.bridge.value.disconnect()
  }

  return {
    selectPort,
    connectSerial,
    connectTcp,
    connectPrimary,
    disconnect,
  }
}
