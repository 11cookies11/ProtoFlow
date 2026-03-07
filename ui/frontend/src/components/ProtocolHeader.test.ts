import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import ProtocolHeader from './ProtocolHeader.vue'

function mountProtocolHeader() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []

  const Root = defineComponent({
    components: { ProtocolHeader },
    render() {
      return h(ProtocolHeader, {
        onRefresh: () => events.push('refresh'),
        onCreate: () => events.push('create'),
      })
    },
  })

  const app = createApp(Root)
  app.provide('t', (key: string) => key)
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

describe('ProtocolHeader interactions', () => {
  it('emits refresh and create events', async () => {
    const vm = mountProtocolHeader()
    const buttons = vm.host.querySelectorAll('button')
    ;(buttons[0] as HTMLButtonElement)?.click()
    ;(buttons[1] as HTMLButtonElement)?.click()
    await tick()

    expect(vm.events).toEqual(['refresh', 'create'])
    vm.unmount()
  })
})
