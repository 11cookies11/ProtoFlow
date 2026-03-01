import type { Ref } from 'vue'

type ChannelDialogRefs = {
  channelDialogOpen: Ref<boolean>
  channelDialogMode: Ref<string>
  channelType: Ref<string>
  channelName: Ref<string>
  channelPort: Ref<string>
  channelBaud: Ref<number | string>
  channelDataBits: Ref<string>
  channelParity: Ref<string>
  channelStopBits: Ref<string>
  channelFlowControl: Ref<string>
  channelReadTimeout: Ref<number>
  channelWriteTimeout: Ref<number>
  channelHost: Ref<string>
  channelTcpPort: Ref<number>
  channelAutoConnect: Ref<boolean>
  selectedPort: Ref<string>
  ports: Ref<any[]>
  defaultBaud: Ref<number>
  defaultParity: Ref<string>
  defaultStopBits: Ref<string>
  tcpHost: Ref<string>
  tcpPort: Ref<number>
  autoConnectOnStart: Ref<boolean>
}

type ChannelDialogDefaults = {
  fallbackPorts: string[]
  serialDefaults: { baud: number }
  networkDefaults: { host: string }
}

type UseChannelDialogOptions = {
  refs: ChannelDialogRefs
  defaults: ChannelDialogDefaults
  bridge: Ref<any>
  normalizeSerialPortName: (value: any) => string
}

export function useChannelDialog(options: UseChannelDialogOptions) {
  const { refs } = options

  function handleNewChannel() {
    refs.channelDialogMode.value = 'create'
    refs.channelType.value = 'serial'
    refs.channelName.value = ''
    refs.channelPort.value = options.normalizeSerialPortName(
      refs.selectedPort.value || refs.ports.value[0] || options.defaults.fallbackPorts[0]
    )
    refs.channelBaud.value = Number(refs.defaultBaud.value || options.defaults.serialDefaults.baud)
    refs.channelDataBits.value = '8'
    refs.channelParity.value = refs.defaultParity.value || 'none'
    refs.channelStopBits.value = refs.defaultStopBits.value || '1'
    refs.channelFlowControl.value = 'none'
    refs.channelReadTimeout.value = 1000
    refs.channelWriteTimeout.value = 1000
    refs.channelHost.value = refs.tcpHost.value || options.defaults.networkDefaults.host
    refs.channelTcpPort.value = Number(refs.tcpPort.value || 502)
    refs.channelAutoConnect.value = !!refs.autoConnectOnStart.value
    refs.channelDialogOpen.value = true
  }

  function openChannelSettings() {
    handleNewChannel()
    refs.channelDialogMode.value = 'serial'
    refs.channelType.value = 'serial'
  }

  function closeChannelDialog() {
    refs.channelDialogOpen.value = false
  }

  function submitChannelDialog() {
    if (!options.bridge.value) return
    if (refs.channelType.value === 'serial') {
      if (refs.channelAutoConnect.value) {
        const targetPort = options.normalizeSerialPortName(refs.channelPort.value)
        if (targetPort) {
          refs.channelPort.value = targetPort
          options.bridge.value.connect_serial(targetPort, Number(refs.channelBaud.value || 115200))
        }
      }
    } else if (refs.channelType.value === 'tcp') {
      if (refs.channelAutoConnect.value) {
        options.bridge.value.connect_tcp(refs.channelHost.value, Number(refs.channelTcpPort.value || 502))
      }
    }
    refs.channelDialogOpen.value = false
  }

  return {
    handleNewChannel,
    openChannelSettings,
    closeChannelDialog,
    submitChannelDialog,
  }
}
