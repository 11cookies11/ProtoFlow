import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import ProxyCaptureDetails from './ProxyCaptureDetails.vue'

function mountDetails(activeFrame: any = { note: 'AA BB', protocolLabel: 'modbus' }) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: Array<{ type: string; value?: string }> = []

  const Root = defineComponent({
    render() {
      return h(ProxyCaptureDetails, {
        activeFrame,
        isUnknownFrame: false,
        activeProtocolLabel: 'modbus',
        activeHexSize: 2,
        activeHexCells: ['AA', 'BB'],
        activeHexAscii: ['..', '..'],
        activeTreeRows: [],
        captureMetrics: { rtt: '1ms', loss: '0%' },
        hexCellClass: () => '',
        onClose: () => events.push({ type: 'close' }),
        onCopyHex: () => events.push({ type: 'copy' }),
        onOpenRule: (mode: string) => events.push({ type: 'rule', value: mode }),
      })
    },
  })

  const app = createApp(Root)
  app.provide('tr', (text: string) => text)
  app.mount(host)

  return {
    host,
    events,
    unmount: () => {
      app.unmount()
      host.remove()
    },
  }
}

async function tick() {
  await nextTick()
  await Promise.resolve()
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('ProxyCaptureDetails', () => {
  it('emits copy/close and rule actions', async () => {
    const vm = mountDetails()
    const buttons = vm.host.querySelectorAll('button')
    ;(buttons[0] as HTMLButtonElement).click()
    ;(buttons[1] as HTMLButtonElement).click()
    ;(buttons[2] as HTMLButtonElement).click()
    ;(buttons[3] as HTMLButtonElement).click()
    await tick()
    expect(vm.events).toEqual([
      { type: 'copy' },
      { type: 'close' },
      { type: 'rule', value: 'inspect' },
      { type: 'rule', value: 'configure' },
    ])
    vm.unmount()
  })
})
