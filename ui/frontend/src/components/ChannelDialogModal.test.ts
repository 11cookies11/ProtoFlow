import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import ChannelDialogModal from './ChannelDialogModal.vue'

function mountChannelDialogModal() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []

  const Root = defineComponent({
    components: { ChannelDialogModal },
    render() {
      return h(ChannelDialogModal, {
        open: true,
        mode: 'create',
        channelType: 'serial',
        channelName: 'CH-A',
        channelPort: 'COM3',
        channelBaud: 115200,
        channelDataBits: '8',
        channelParity: 'none',
        channelStopBits: '1',
        channelFlowControl: 'none',
        channelReadTimeout: 1000,
        channelWriteTimeout: 1000,
        channelHost: '127.0.0.1',
        channelTcpPort: 502,
        channelAutoConnect: false,
        hasPorts: true,
        portOptionsList: ['COM1', 'COM2', 'COM3'],
        supportedBaudRates: ['9600', '115200'],
        onClose: () => events.push('close'),
        onSubmit: () => events.push('submit'),
        'onUpdate:channelName': (value: string) => events.push(`name:${value}`),
        'onUpdate:channelAutoConnect': (value: boolean) => events.push(`auto:${value}`),
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

describe('ChannelDialogModal interactions', () => {
  it('emits close/submit and field updates', async () => {
    const vm = mountChannelDialogModal()

    const textInput = vm.host.querySelector('input[type="text"]') as HTMLInputElement
    textInput.value = 'CH-B'
    textInput.dispatchEvent(new Event('input', { bubbles: true }))

    const checkbox = vm.host.querySelector('input[type="checkbox"]') as HTMLInputElement
    checkbox.checked = true
    checkbox.dispatchEvent(new Event('change', { bubbles: true }))

    const footerButtons = vm.host.querySelectorAll('.modal-footer button')
    ;(footerButtons[0] as HTMLButtonElement)?.click()
    ;(footerButtons[1] as HTMLButtonElement)?.click()
    await tick()

    expect(vm.events).toContain('name:CH-B')
    expect(vm.events).toContain('auto:true')
    expect(vm.events).toContain('close')
    expect(vm.events).toContain('submit')
    vm.unmount()
  })
})
