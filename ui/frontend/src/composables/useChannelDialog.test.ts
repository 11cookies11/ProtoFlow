import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useChannelDialog } from './useChannelDialog'

function createRefs() {
  return {
    channelDialogOpen: ref(false),
    channelDialogMode: ref('create'),
    channelType: ref('serial'),
    channelName: ref(''),
    channelPort: ref(''),
    channelBaud: ref(115200),
    channelDataBits: ref('8'),
    channelParity: ref('none'),
    channelStopBits: ref('1'),
    channelFlowControl: ref('none'),
    channelReadTimeout: ref(0),
    channelWriteTimeout: ref(0),
    channelHost: ref(''),
    channelTcpPort: ref(0),
    channelAutoConnect: ref(false),
    selectedPort: ref('COM9'),
    ports: ref(['COM3', 'COM4']),
    defaultBaud: ref(57600),
    defaultParity: ref('even'),
    defaultStopBits: ref('2'),
    tcpHost: ref('192.168.1.2'),
    tcpPort: ref(7001),
    autoConnectOnStart: ref(true),
  }
}

describe('useChannelDialog', () => {
  it('prepares new channel defaults', () => {
    const refs = createRefs()
    const mgr = useChannelDialog({
      refs,
      defaults: { fallbackPorts: ['COM1'], serialDefaults: { baud: 9600 }, networkDefaults: { host: '127.0.0.1' } },
      bridge: ref(null),
      normalizeSerialPortName: (value) => String(value || '').toUpperCase(),
    })

    mgr.handleNewChannel()
    expect(refs.channelDialogOpen.value).toBe(true)
    expect(refs.channelPort.value).toBe('COM9')
    expect(refs.channelBaud.value).toBe(57600)
    expect(refs.channelParity.value).toBe('even')
  })

  it('opens serial settings mode', () => {
    const refs = createRefs()
    const mgr = useChannelDialog({
      refs,
      defaults: { fallbackPorts: ['COM1'], serialDefaults: { baud: 9600 }, networkDefaults: { host: '127.0.0.1' } },
      bridge: ref(null),
      normalizeSerialPortName: (value) => String(value || ''),
    })

    mgr.openChannelSettings()
    expect(refs.channelDialogMode.value).toBe('serial')
    expect(refs.channelType.value).toBe('serial')
  })

  it('submits serial and tcp connections through bridge', () => {
    const refs = createRefs()
    let serialCalls = 0
    let tcpCalls = 0
    const mgr = useChannelDialog({
      refs,
      defaults: { fallbackPorts: ['COM1'], serialDefaults: { baud: 9600 }, networkDefaults: { host: '127.0.0.1' } },
      bridge: ref({
        connect_serial: () => {
          serialCalls += 1
        },
        connect_tcp: () => {
          tcpCalls += 1
        },
      }),
      normalizeSerialPortName: (value) => String(value || '').toUpperCase(),
    })

    refs.channelDialogOpen.value = true
    refs.channelType.value = 'serial'
    refs.channelPort.value = 'com5'
    refs.channelAutoConnect.value = true
    mgr.submitChannelDialog()
    expect(serialCalls).toBe(1)
    expect(refs.channelPort.value).toBe('COM5')
    expect(refs.channelDialogOpen.value).toBe(false)

    refs.channelDialogOpen.value = true
    refs.channelType.value = 'tcp'
    refs.channelAutoConnect.value = true
    mgr.submitChannelDialog()
    expect(tcpCalls).toBe(1)
  })
})
