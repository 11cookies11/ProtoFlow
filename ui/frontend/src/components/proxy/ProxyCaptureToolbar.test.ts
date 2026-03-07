import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import ProxyCaptureToolbar from './ProxyCaptureToolbar.vue'

function mountToolbar() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: Array<{ type: string; value?: string }> = []
  const keyword = ref('')

  const Root = defineComponent({
    render() {
      return h(ProxyCaptureToolbar, {
        captureProxy: { hostPort: 'COM3' },
        captureMeta: { channel: 'COM3', engine: 'x' },
        searchKeyword: keyword.value,
        'onUpdate:search-keyword': (value: string) => {
          keyword.value = value
          events.push({ type: 'search', value })
        },
        onResumeCapture: () => events.push({ type: 'resume' }),
        onOpenSettings: () => events.push({ type: 'settings' }),
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

describe('ProxyCaptureToolbar', () => {
  it('emits search, resume and settings actions', async () => {
    const vm = mountToolbar()
    const input = vm.host.querySelector('input') as HTMLInputElement
    input.value = 'modbus'
    input.dispatchEvent(new Event('input'))
    const buttons = vm.host.querySelectorAll('button')
    ;(buttons[0] as HTMLButtonElement).click()
    ;(buttons[1] as HTMLButtonElement).click()
    await tick()

    expect(vm.events).toEqual([{ type: 'search', value: 'modbus' }, { type: 'resume' }, { type: 'settings' }])
    vm.unmount()
  })
})
