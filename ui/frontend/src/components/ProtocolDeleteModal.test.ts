import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import ProtocolDeleteModal from './ProtocolDeleteModal.vue'

function mountProtocolDeleteModal() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []

  const Root = defineComponent({
    components: { ProtocolDeleteModal },
    render() {
      return h(ProtocolDeleteModal, {
        open: true,
        deleting: { name: 'ProtoA' },
        onClose: () => events.push('close'),
        onConfirm: () => events.push('confirm'),
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

describe('ProtocolDeleteModal interactions', () => {
  it('emits confirm', async () => {
    const vm = mountProtocolDeleteModal()
    const confirmButton = Array.from(vm.host.querySelectorAll('.modal-footer button')).find((item) =>
      item.textContent?.includes('确认删除')
    ) as HTMLButtonElement
    confirmButton?.click()
    await tick()
    expect(vm.events).toContain('confirm')
    vm.unmount()
  })
})
