import { describe, expect, it } from 'vitest'
import { computed, ref } from 'vue'
import { useChannelConnectionActions } from './useChannelConnectionActions'

describe('useChannelConnectionActions', () => {
  it('selects port and switches to serial mode', () => {
    const selected = ref('')
    const mode = ref('tcp')
    const actions = useChannelConnectionActions({
      bridge: ref(null),
      isConnecting: ref(false),
      isConnected: computed(() => false),
      selectedPort: selected,
      baud: ref(115200),
      tcpHost: ref('127.0.0.1'),
      tcpPort: ref(9000),
      channelMode: mode,
      resolveSerialPort: (value: string) => value,
      selectChannelPort: (item: string) => {
        selected.value = item
      },
    })

    actions.selectPort('COM7')
    expect(selected.value).toBe('COM7')
    expect(mode.value).toBe('serial')
  })

  it('connects serial with normalized port and sets connecting state', () => {
    const selected = ref('com3')
    const isConnecting = ref(false)
    let calledPort = ''
    let calledBaud = 0

    const actions = useChannelConnectionActions({
      bridge: ref({
        connect_serial: (port: string, baud: number) => {
          calledPort = port
          calledBaud = baud
        },
      }),
      isConnecting,
      isConnected: computed(() => false),
      selectedPort: selected,
      baud: ref(57600),
      tcpHost: ref('127.0.0.1'),
      tcpPort: ref(9000),
      channelMode: ref('serial'),
      resolveSerialPort: (value: string) => String(value).toUpperCase(),
      selectChannelPort: () => {},
    })

    actions.connectSerial()
    expect(selected.value).toBe('COM3')
    expect(calledPort).toBe('COM3')
    expect(calledBaud).toBe(57600)
    expect(isConnecting.value).toBe(true)
  })

  it('skips connect when already connecting or connected', () => {
    let serialCalls = 0
    let tcpCalls = 0
    const isConnecting = ref(true)
    const connected = ref(false)
    const actions = useChannelConnectionActions({
      bridge: ref({
        connect_serial: () => {
          serialCalls += 1
        },
        connect_tcp: () => {
          tcpCalls += 1
        },
      }),
      isConnecting,
      isConnected: computed(() => connected.value),
      selectedPort: ref('COM1'),
      baud: ref(115200),
      tcpHost: ref('127.0.0.1'),
      tcpPort: ref(9000),
      channelMode: ref('serial'),
      resolveSerialPort: (value: string) => value,
      selectChannelPort: () => {},
    })

    actions.connectSerial()
    actions.connectTcp()
    expect(serialCalls).toBe(0)
    expect(tcpCalls).toBe(0)

    isConnecting.value = false
    connected.value = true
    actions.connectSerial()
    actions.connectTcp()
    expect(serialCalls).toBe(0)
    expect(tcpCalls).toBe(0)
  })

  it('connectPrimary switches by mode and disconnect delegates bridge', () => {
    let serialCalls = 0
    let tcpCalls = 0
    let disconnectCalls = 0
    const mode = ref('serial')
    const actions = useChannelConnectionActions({
      bridge: ref({
        connect_serial: () => {
          serialCalls += 1
        },
        connect_tcp: () => {
          tcpCalls += 1
        },
        disconnect: () => {
          disconnectCalls += 1
        },
      }),
      isConnecting: ref(false),
      isConnected: computed(() => false),
      selectedPort: ref('COM4'),
      baud: ref(115200),
      tcpHost: ref('127.0.0.1'),
      tcpPort: ref(9010),
      channelMode: mode,
      resolveSerialPort: (value: string) => value,
      selectChannelPort: () => {},
    })

    actions.connectPrimary()
    expect(serialCalls).toBe(1)
    expect(tcpCalls).toBe(0)

    mode.value = 'tcp'
    actions.connectPrimary()
    expect(serialCalls).toBe(1)
    expect(tcpCalls).toBe(0)

    actions.disconnect()
    expect(disconnectCalls).toBe(1)
  })
})
