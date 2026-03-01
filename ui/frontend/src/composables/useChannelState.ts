import { computed, type Ref } from 'vue'
import { fallbackPorts } from '@/config/runtimeDefaults'
import { normalizeSerialPortList, normalizeSerialPortName } from '@/utils/serialPort'

export function useChannelState(ports: Ref<string[]>, selectedPort: Ref<string>) {
  const noPorts = computed(() => ports.value.length === 0)
  const portOptionsList = computed(() => {
    const source = ports.value.length ? ports.value : fallbackPorts
    return source.map((item) => ({ label: item, value: item, icon: 'usb' }))
  })

  function applyPorts(rawItems: unknown) {
    ports.value = normalizeSerialPortList(rawItems)
    selectedPort.value = normalizeSerialPortName(selectedPort.value)
    if (!selectedPort.value && ports.value.length) {
      selectedPort.value = ports.value[0]
    }
  }

  function selectPort(item: unknown) {
    const normalized = normalizeSerialPortName(item)
    if (!normalized) return
    selectedPort.value = normalized
  }

  return {
    noPorts,
    portOptionsList,
    applyPorts,
    selectPort,
  }
}
